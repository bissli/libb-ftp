import contextlib
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from date import Date, DateTime
from ftp.config import gpg
from ftp.options import FtpOptions
from libb import load_options

logger = logging.getLogger(__name__)

__all__ = ['decrypt_pgp_file', 'decrypt_all_pgp_files']


def decrypt_pgp_file(options, pgpname: str, newname=None, _local: Path = None):
    """Decrypt file with GnuPG: FIXME move this to a library
    """
    _local = _local or options.localdir
    if not newname:
        newname = options.rename_pgp(pgpname)
    if newname == pgpname:
        raise ValueError(f'pgpname and newname cannot be the same: {pgpname}')
    logger.debug(f'Decrypting file {pgpname} to {newname}')
    gpg_cmd = [
        gpg.exe,
        '--homedir',
        gpg.dir,
        '--decrypt',
        '--batch',
        '--yes',
        '--passphrase-fd',
        '0',
        '--output',
        (_local / newname).as_posix(),
        '--decrypt',
        (_local / pgpname).as_posix(),
    ]
    if options.pgp_extension:
        gpg_cmd.insert(-3, '--load-extension')
        gpg_cmd.insert(-3, options.pgp_extension)
    logger.debug(' '.join(gpg_cmd))
    p = subprocess.Popen(gpg_cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True)
    out, err = p.communicate('password')
    if 'gpg: decryption failed: secret key not available' in err:
        logger.error('Failed to decrypt %s\n%s:', pgpname, err)
    if 'decrypt_message failed: file open error' in err:
        logger.error('Failed to decrypt %s\n%s:', pgpname, err)


__THEYEAR = Date.today().year


def skip_folder(path):
    path = str(path)
    if re.search(r'prev|legacy|old|archive|depr|pgp', path, re.I):
        return True
    date_match = re.search(r'(\d{4})', path)
    if date_match:
        return int(date_match.group()) != __THEYEAR
    return False


@load_options(cls=FtpOptions)
def decrypt_all_pgp_files(options:FtpOptions = None, config=None, **kw):
    """Backup approach to decrypting all saved pgp files

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
    """
    files = []
    for _local, _, _files in os.walk(options.localdir):
        if skip_folder(_local):
            continue
        _local = Path(_local)
        logger.info(f'Walking through {len(_files)} files')
        for name in _files:
            localfile = _local / name
            localpgpfile = (_local / '.pgp') / name
            if options.ignoreolderthan:
                created_on = DateTime.parse(localfile.stat().st_ctime)
                before_date = DateTime.now().subtract(days=int(options.ignoreolderthan))
                if created_on < before_date:
                    logger.debug(f'Skipping {_local}/{name}, file created on ({str(created_on)})')
                    continue
            if options.is_encrypted(name):
                newname = options.rename_pgp(name)
                decrypt_pgp_file(options, name, newname, _local)
                with contextlib.suppress(Exception):
                    Path(os.path.split(localpgpfile)[0]).mkdir(parents=True)
                shutil.move(localfile, localpgpfile)
                filename = _local / newname
                files.append(filename)
    return files
