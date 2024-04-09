import logging
import os
import platform

from libb import Setting, get_tempdir

logger = logging.getLogger(__name__)

tmpdir = get_tempdir()

# GnuPG encryption
gpg = Setting()
gpg.dir = os.path.abspath(os.getenv('CONFIG_GPG_DIR') or tmpdir.dir)
gpg.exe = os.path.join(gpg.dir, 'gpg.exe' if 'Win' in platform.system() else 'gpg')

if __name__ == '__main__':
    print('tmpdir: '+tmpdir.dir)
    print('gpg: '+gpg.dir)
