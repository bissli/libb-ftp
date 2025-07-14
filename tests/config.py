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

# SFTP configuration (secure FTP)
vendor.FOO.sftp.hostname = '127.0.0.1'
vendor.FOO.sftp.username = 'foo'
vendor.FOO.sftp.password = 'bar'
vendor.FOO.sftp.port = 2222
vendor.FOO.sftp.secure = True
vendor.FOO.sftp.localdir = mountdir
vendor.FOO.sftp.remotedir = '/upload'

Setting.lock()
