import contextlib
import logging
import os
import shutil
import subprocess
from pathlib import Path

from date import DateTime, now
from ftp.config import gpg
from ftp.options import FtpOptions
from libb import load_options

logger = logging.getLogger(__name__)

__all__ = ['decrypt_pgp_file']


def decrypt_pgp_file(options, pgpname: str, newname=None):
    """Decrypt file with GnuPG: FIXME move this to a library
    """
    if not newname:
        newname = options.rename_pgp(pgpname)
    if newname == pgpname:
        raise ValueError('pgpname and newname cannot be the same')
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
        (options.localdir / newname).as_posix(),
        '--decrypt',
        (options.localdir / pgpname).as_posix(),
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


@load_options(cls=FtpOptions)
def decrypt_all_pgp_files(options=None, config=None, **kw):
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
    for localdir, _, files in os.walk(options.localdir):
        if '.pgp' in os.path.split(localdir):
            continue
        localdir = Path(localdir)
        logger.info(f'Walking through {len(files)} files')
        for name in files:
            localfile = localdir / name
            localpgpfile = (localdir / '.pgp') / name
            if options.ignoreolderthan:
                created_on = DateTime(localfile.stat().st_ctime)
                ignore_datetime = now().subtract(days=int(options.ignoreolderthan))
                if created_on < ignore_datetime:
                    logger.debug('File is too old: %s/%s, skipping (%s)',
                                 localdir, name, str(created_on))
                    continue
            if options.is_encrypted(name):
                newname = options.rename_pgp(name)
                decrypt_pgp_file(options, localdir, name, newname)
                with contextlib.suppress(Exception):
                    os.makedirs(os.path.split(localpgpfile)[0])
                shutil.move(localfile, localpgpfile)
                filename = localdir / newname
                files.append(filename)
    return files
