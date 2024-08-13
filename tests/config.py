from ftp.config import gpg, tmpdir  # noqa
import os
import shutil

from libb import Setting

mountdir = os.path.join(tmpdir.dir, 'ftpmount')
shutil.rmtree(mountdir, ignore_errors=True)
os.makedirs(mountdir)

Setting.unlock()
vendor = Setting()
vendor.FOO.ftp.hostname = '127.0.0.1'
vendor.FOO.ftp.username = 'foo'
vendor.FOO.ftp.password = 'bar'
vendor.FOO.ftp.port = 21
vendor.FOO.ftp.localdir = mountdir
vendor.FOO.ftp.remotedir = '/'

Setting.lock()
