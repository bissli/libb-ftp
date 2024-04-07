import logging
import os
import platform
import tempfile
from pathlib import Path

from libb import Setting, expandabspath

logger = logging.getLogger(__name__)

Setting.unlock()

# Tmpdir
tmpdir = Setting()
if os.getenv('CONFIG_TMPDIR_DIR'):
    tmpdir.dir = expandabspath(os.getenv('CONFIG_TMPDIR_DIR'))
else:
    tmpdir.dir = tempfile.gettempdir()
Path(tmpdir.dir).mkdir(parents=True, exist_ok=True)

# GnuPG encryption
gpg = Setting()
gpg.dir = os.path.abspath(os.getenv('CONFIG_GPG_DIR') or tmpdir.dir)
gpg.exe = os.path.join(gpg.dir, 'gpg.exe' if 'Win' in platform.system() else 'gpg')

Setting.lock()

if __name__ == '__main__':
    __import__('doctest').testmod(optionflags=4 | 8 | 32)
    print('tmpdir: '+tmpdir.dir)
