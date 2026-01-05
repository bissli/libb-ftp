from ftp.config import gpg, tmpdir  # noqa
import os
import shutil

from libb import Setting
import pathlib

mountdir = os.path.join(tmpdir.dir, 'ftpmount')
shutil.rmtree(mountdir, ignore_errors=True)
pathlib.Path(mountdir).mkdir(parents=True)

Setting.unlock()
vendor = Setting()
vendor.FOO.ftp.hostname = '127.0.0.1'
vendor.FOO.ftp.username = 'foo'
vendor.FOO.ftp.password = 'bar'
vendor.FOO.ftp.port = 21
vendor.FOO.ftp.localdir = mountdir
vendor.FOO.ftp.remotedir = '/'

# FTP configuration on non-standard port (for port selection testing)
vendor.FOO.ftp2121.hostname = '127.0.0.1'
vendor.FOO.ftp2121.username = 'foo'
vendor.FOO.ftp2121.password = 'bar'
vendor.FOO.ftp2121.port = 2121
vendor.FOO.ftp2121.localdir = mountdir
vendor.FOO.ftp2121.remotedir = '/'

# SFTP configuration (secure FTP)
vendor.FOO.sftp.hostname = '127.0.0.1'
vendor.FOO.sftp.username = 'foo'
vendor.FOO.sftp.password = 'bar'
vendor.FOO.sftp.port = 2222
vendor.FOO.sftp.secure = True
vendor.FOO.sftp.localdir = mountdir
vendor.FOO.sftp.remotedir = '/upload'

Setting.lock()
