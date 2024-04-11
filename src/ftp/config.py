import logging
import os
import platform

from libb import Setting, get_tempdir

logger = logging.getLogger(__name__)

Setting.unlock()

tmpdir = get_tempdir()

# GnuPG encryption
gpg = Setting()
gpg.dir = os.path.abspath(os.getenv('CONFIG_GPG_DIR') or tmpdir.dir)
gpg.exe = os.path.join(gpg.dir, 'gpg.exe' if 'Win' in platform.system() else 'gpg')

Setting.lock()

if __name__ == '__main__':
    print(f"tmpdir: {tmpdir.dir}")
    print(f"gpg: {gpg.dir}")
