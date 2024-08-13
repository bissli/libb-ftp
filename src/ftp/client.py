import contextlib
import ftplib
import logging
import os
import posixpath
import random
import re
import shutil
import stat
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from functools import wraps
from io import BytesIO, IOBase, StringIO
from pathlib import Path
from typing import NamedTuple

from date import LCL, DateTime
from ftp.options import FtpOptions
from ftp.pgp import decrypt_pgp_file
from libb import FileLike, load_options

logger = logging.getLogger(__name__)


import paramiko

__all__ = [
    'connect',
    'connectmanager',
    'sync_site',
    'BaseConnection',
]


class Entry(NamedTuple):
    line: str = None
    name: str = None
    is_dir: bool = False
    size: int = 0
    datetime: DateTime = None


FTP_DIR_RE = (
    # typical dir entry
    # drwxr-xr-x 2   4100            4100    4096    Sep 07 17:54 incoming
    # drwxr-xr-x 2   4100            4100    237568  Sep 08 10:42 outgoing
    # -rw-r--r-- 1   4100            4100    29948   Sep 07 22:35 foobarbaz.txt.pgp.20000907
    r'([drwx-]+)\s+\d+\s+\w+\s+\w+\s+(\d+)\s+(\w+\s+\d+\s+[\d:]+)\s+(.*)\s*$',
    # alternate that leaves out one field
    # drwxrwx--x   3 500         2048 Sep  7 19:00 incoming
    # drwxr-xr-x   2 400         1024 Sep  8 09:29 outgoing
    # -rw-r--r--   1 500        19045 Sep  7 06:10 20000907.FOO.BAR_BAZ.csv.asc
    r'([drwx-]+)\s+\d+\s+\w+\s+(\d+)\s+(\w+\s+\d+\s+[\d:]+)\s+(.*)\s*$',
)


@load_options(cls=FtpOptions)
def connect(options: FtpOptions = None, config=None, **kw):
    """Factory function to connect to a site. Add in each site that
    needs to be synced.

    opts:
        - Options configuration object
        - Kwargs of parameters
        - Sitename string and config module path (i.e. foo.bar.ftp)

    return:
        The FTP object, else raise exception

    note: having trouble with SSL auth?  test with ossl command:
    openssl s_client -starttls ftp -connect host.name:port
    """
    tries, cn = 0, None
    while tries < 10 and not cn:
        try:
            if options.secure:
                cn = SecureFtpConnection(options.hostname, username=options.username,
                                         password=options.password,
                                         port=options.port,
                                         tzinfo=options.tzinfo)
                if not cn:
                    raise paramiko.SSHException
            else:
                cn = FtpConnection(options.hostname, options.username,
                                   options.password, tzinfo=options.tzinfo)
        except paramiko.AuthenticationException as err:
            logger.error(err)
            return
        except (OSError, paramiko.SSHException) as err:
            logger.error(err)
            time.sleep(10)
            tries += 1
    if not cn or tries > 10:
        return
    if options.remotedir:
        cn.cd(options.remotedir)
    return cn


@contextlib.contextmanager
@load_options(cls=FtpOptions)
def connectmanager(options: FtpOptions = None, config=None, **kw):
    """Factory function to connect to a site. Add in each site that
    needs to be synced.

    opts:
        - Options configuration object
        - Kwargs of parameters
        - Sitename string and config module path (i.e. foo.bar.ftp)

    return:
        The FTP object, else raise exception

    note: having trouble with SSL auth?  test with ossl command:
    openssl s_client -starttls ftp -connect host.name:port
    """
    cn = connect(options, config, **kw)
    yield cn
    try:
        cn.close()
    except:
        pass


def parse_ftp_dir_entry(line, tzinfo):
    for pattern in FTP_DIR_RE:
        if m := re.search(pattern, line):
            try:
                entry = Entry(line,
                              m.group(4),
                              m.group(1)[0] == 'd',
                              int(m.group(2)),
                              DateTime.parse(m.group(3)).replace(tzinfo=tzinfo))
            except Exception as exc:
                logger.error(f'Error with line {line}, groups: {m.groups()}')
                logger.exception(exc)
                raise exc
            return entry


@load_options(cls=FtpOptions)
def sync_site(options=None, config=None, **kw):
    """Use local config module to specify sites to sync via FTP

    Assumes that local config.py contains a general stie structure
    for vendors:

    `local config.py`

    vendors = Setting()

    vendors.foo.ftp.hostname = 'sftp.foovendor.com'
    vendors.foo.ftp.username = 'foouser'
    vendors.foo.ftp.password = 'foopasswd'
    ...
    vendors.bar.ftp.hostname = 'sftp.barvendor.com'
    vendors.bar.ftp.username = 'baruser'
    vendors.bar.ftp.password = 'barpasswd'
    ...

    opts:
    `nocopy`: do not copy anything
    `nodecryptlocal`: do not decrypt local files
    `ignorelocal`: ignore presence of local file when deciding to copy
    `ignoresize`: ignore size of local file when deciding to copy
    `ignoreolderthan`: ignore files older than number of days
    `address`: Send notification of new files to address

    """
    logger.info(f'Syncing FTP site for {options.sitename or ""}')
    files = []
    with connectmanager(options, config) as cn:
        sync_directory(cn, options, files)
        logger.info(
            '%d copied, %d decrypted, %d skipped, %d ignored',
            options.stats['copied'],
            options.stats['decrypted'],
            options.stats['skipped'],
            options.stats['ignored'],
        )
    return files


def returntodir(func):
    @wraps(func)
    def wrapper(cn, options, files, _local: Path = None, _remote: str = None):
        _local = _local or options.localdir
        _remote = _remote or options.remotedir
        workdir = cn.pwd()
        logger.debug(f'CD to: {_remote}')
        cn.cd(_remote)
        try:
            func(cn, options, files, _local, _remote)
        finally:
            logger.debug(f'CD to: {workdir}')
            cn.cd(workdir)
    return wrapper


def streamtofile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for i, arg in enumerate(args):
            if isinstance(arg, IOBase):
                rf = os.path.join(tempfile.tempdir(), random.getrandbits(32))
                with open(rf, 'w' if isinstance(arg, StringIO) else 'wb') as f:
                    f.write(arg.read())
                args[i] = f
        for k, v in kwargs.items():
            if isinstance(v, IOBase):
                rf = os.path.join(tempfile.tempdir(), random.getrandbits(32))
                with open(rf, 'w' if isinstance(arg, StringIO) else 'wb') as f:
                    f.write(arg.read())
                kwargs[k] = f
        return func(*args, **kwargs)
    return wrapper


@returntodir
def sync_directory(cn, options, files, _local: Path = None, _remote: str = None):
    """Sync a remote FTP directory to a local directory recursively
    """
    logger.info(f'Syncing directory {_remote or options.remotedir}')
    entries = cn.dir(sort=True)
    for entry in entries:
        if options.ignore_re and re.match(options.ignore_re, entry.name):
            logger.debug(f'Ignoring file that matches ignore pattern: {entry.name}')
            options.stats['ignored'] += 1
            continue
        if entry.is_dir:
            sync_directory(cn, options, files, _local / entry.name,
                           posixpath.join(_remote, entry.name))
            continue
        try:
            filename = sync_file(cn, options, entry, _local, _remote)
            if filename:
                files.append(filename)
        except:
            logger.exception('Error syncing file: %s/%s', _remote, entry.name)


def sync_file(cn, options, entry, _local: Path, _remote: str):
    if options.ignoreolderthan and entry.datetime < DateTime.now().subtract(days=int(options.ignoreolderthan)):
        logger.debug('File is too old: %s/%s: (%s)', _remote, entry.name, str(entry.datetime))
        return
    localfile = _local / entry.name
    localpgpfile = (_local / '.pgp') / entry.name
    if not options.ignorelocal and (localfile.exists() or localpgpfile.exists()):
        st = localfile.stat() if localfile.exists() else localpgpfile.stat()
        if entry.datetime <= DateTime.parse(st.st_mtime).replace(tzinfo=options.tzinfo):
            if not options.ignoresize and (entry.size == st.st_size):
                logger.debug('File has not changed: %s/%s', _remote, entry.name)
                options.stats['skipped'] += 1
                return
    logger.debug('Downloading file: %s/%s to %s', _remote, entry.name, localfile)
    filename = None
    with contextlib.suppress(Exception):
        Path(os.path.split(localfile)[0]).mkdir(parents=True)
    if not options.nocopy:
        cn.getbinary(entry.name, localfile)
        mtime = int(DateTime(*entry.datetime.timetuple()[:7]).epoch())
        try:
            os.utime(localfile, (mtime, mtime))
        except OSError:
            logger.warning(f'Could not touch new file time on {localfile}')
        options.stats['copied'] += 1
        filename = localfile
    if not options.nocopy and not options.nodecryptlocal and options.is_encrypted(localfile.as_posix()):
        newname = options.rename_pgp(entry.name)
        decrypt_pgp_file(options, entry.name, newname, _local)
        # keep a copy for stat comparison above but move to .pgp dir so it doesn't clutter the main directory
        with contextlib.suppress(Exception):
            os.makedirs(os.path.split(localpgpfile)[0])
        shutil.move(localfile, localpgpfile)
        options.stats['decrypted'] += 1
        filename = _local / newname
    return filename


def as_posix(path):
    if not path:
        return path
    return str(path).replace(os.sep, '/')


class BaseConnection(ABC):

    @abstractmethod
    def pwd(self):
        pass

    @abstractmethod
    def cd(self, path):
        pass

    @abstractmethod
    def dir(self, *args):
        pass

    @abstractmethod
    def files(self):
        pass

    @abstractmethod
    def getascii(self, remotefile, localfile):
        pass

    @abstractmethod
    def getbinary(self, remotefile, localfile):
        pass

    @abstractmethod
    def putascii(self, localfile, remotefile):
        pass

    @abstractmethod
    def putbinary(self, localfile, remotefile):
        pass

    @abstractmethod
    def delete(self, remotefile):
        pass

    @abstractmethod
    def close(self):
        pass


class FtpConnection(BaseConnection):
    """Wrapper around ftplib
    """
    def __init__(self, hostname, username, password, tzinfo=LCL):
        self.ftp = ftplib.FTP(hostname, username, password)
        self._tzinfo = tzinfo

    def pwd(self):
        """Return the current directory"""
        return self.ftp.pwd()

    def cd(self, path):
        """Change the working directory"""
        return self.ftp.cwd(as_posix(path))

    def dir(self, sort=False) -> list[Entry]:
        """Return a directory listing as an array of lines"""
        lines = []
        self.ftp.dir(lines.append)
        entries = []
        for line in lines:
            entry = parse_ftp_dir_entry(line, self._tzinfo)
            if entry:
                entries.append(entry)
        if sort:
            return sorted(entries, key=lambda x: x.datetime, reverse=True)
        return entries

    def files(self):
        """Return a bare filename listing as an array of strings"""
        return self.ftp.nlst()

    def getascii(self, remotefile, localfile):
        """Get a file in ASCII (text) mode"""
        with Path(localfile).open('w') as f:
            self.ftp.retrlines(f'RETR {as_posix(remotefile)}', lambda line: f.write(f'{line}\n'))

    def getbinary(self, remotefile, localfile):
        """Get a file in binary mode"""
        with Path(localfile).open('wb') as f:
            self.ftp.retrbinary(f'RETR {as_posix(remotefile)}', f.write)

    @streamtofile
    def putascii(self, localfile, remotefile):
        """Put a file in ASCII (text) mode"""
        with Path(localfile).open('rb') as f:
            self.ftp.storlines(f'STOR {as_posix(remotefile)}', f)

    @streamtofile
    def putbinary(self, localfile, remotefile):
        """Put a file in binary mode"""
        with Path(localfile).open('rb') as f:
            self.ftp.storbinary(f'STOR {as_posix(remotefile)}', f, 1024)

    def delete(self, remotefile):
        self.ftp.delete(as_posix(remotefile))

    def close(self):
        with contextlib.suppress(Exception):
            self.ftp.close()


class SecureFtpConnection(BaseConnection):

    def __init__(self, hostname, username, password, port=22, tzinfo=LCL,
                 allow_agent=False, look_for_keys=False):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname,
                         username=username,
                         password=password,
                         port=port,
                         allow_agent=allow_agent,
                         look_for_keys=look_for_keys)
        self.ftp = self.ssh.open_sftp()
        self._tzinfo = tzinfo

    def pwd(self):
        """Return the current directory"""
        return self.ftp.getcwd()

    def cd(self, path):
        """Change the working directory"""
        return self.ftp.chdir(as_posix(path))

    def dir(self, sort=False) -> list[Entry]:
        """Return a directory listing as an array of lines"""
        files = self.ftp.listdir_attr()  # paramiko.SFTPAttributes
        entries = []
        for f in files:
            entry = Entry(f.longname,
                          f.filename,
                          stat.S_ISDIR(f.st_mode),
                          f.st_size,
                          DateTime.parse(f.st_mtime).replace(tzinfo=self._tzinfo))
            entries.append(entry)
        if sort:
            return sorted(entries, key=lambda x: x.datetime, reverse=True)
        return entries

    def files(self):
        """Return a bare filename listing as an array of strings"""
        return self.ftp.listdir()

    def getascii(self, remotefile, localfile):
        """Get a file in ASCII (text) mode"""
        self.ftp.get(as_posix(remotefile), localfile)

    def getbinary(self, remotefile, localfile):
        """Get a file in binary mode"""
        self.ftp.get(as_posix(remotefile), localfile)

    @streamtofile
    def putascii(self, localfile, remotefile):
        """Put a file in ASCII (text) mode"""
        self.ftp.put(localfile, as_posix(remotefile))

    @streamtofile
    def putbinary(self, localfile, remotefile):
        """Put a file in binary mode"""
        self.ftp.put(localfile, as_posix(remotefile))

    def delete(self, remotefile):
        self.ftp.remove(as_posix(remotefile))

    def close(self):
        with contextlib.suppress(Exception):
            self.ftp.close()
            self.ssh.close()


class TlsFtpConnection:
    """FTP connection for sites that use SSL

    from sqlalchemy-media (update to match above aproach)

    :param hostname: FTP server hostname or instance of :class:`ftplib.FTP`.
                     Note if pass the instance of :class:`ftplib.FTP` do not need to
                     set `username`, `password`, `passive`, `secure`, `kwargs` arguments.
    :param root_path: Root working directory path on FTP server.
    :param base_url: First part of URL that using to locate file access URL.
    :param username: FTP server username.
    :param password: FTP server password.
    :param passive: Enable passive FTP mode.
                    (How it works? https://www.ietf.org/rfc/rfc959.txt,
                                   http://slacksite.com/other/ftp.html)
    :param secure: Enable secure TLS connection.
    :param kwargs: Additional arguments to FTP client
                   (for :class:`ftplib.FTP` or :class:`ftplib.FTP_TLS` based
                   on `secure` argument status)
    """
    def __init__(self, hostname, root_path, base_url, username=None, password=None, passive=True, **kwargs):
        self.ftp_client = ftplib.FTP_TLS(host=hostname, user=username, passwd=password, **kwargs)
        self.ftp_client.prot_p()
        self.ftp_client.set_pasv(passive)
        self.root_path = root_path
        self.base_url = base_url.rstrip('/')

    def _get_remote_path(self, filename):
        return os.path.join(self.root_path, filename)

    def cd(self, remote):
        remote_dirs = remote.split('/')
        for directory in remote_dirs:
            try:
                self.ftp_client.cwd(directory)
            except Exception:
                # Try to make directory if not exists
                self.ftp_client.mkd(directory)
                self.ftp_client.cwd(directory)

    def put(self, filename: str, stream: FileLike) -> int:
        remote_filename = self._get_remote_path(filename)
        remote_dir = os.path.dirname(remote_filename)
        remote_file = os.path.basename(remote_filename)
        current = self.ftp_client.pwd()
        self.cd(remote_dir)

        try:
            self.ftp_client.storbinary(f'STOR {remote_file}', stream)
            size = self.ftp_client.size(remote_file)
        finally:
            stream.close()
            self.ftp_client.cwd(current)
        return size

    def delete(self, filename: str) -> None:
        remote_filename = self._get_remote_path(filename)
        self.ftp_client.delete(remote_filename)

    def open(self, filename: str, mode: str = 'rb'):
        remote_filename = self._get_remote_path(filename)
        file_bytes = BytesIO()
        self.ftp_client.retrbinary(f'RETR {remote_filename}', file_bytes.write)
        file_bytes.seek(0)
        return file_bytes

    def locate(self, attachment) -> str:
        return f'{self.base_url}/{attachment.path}'


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    if len(sys.argv) != 2:
        print('usage: ftp config (e.g. site.FOO, site.BAR)')
        sys.exit(1)
