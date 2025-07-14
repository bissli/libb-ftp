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


def configure_sftp_ssh_key(ssh_key_filename: str = None, ssh_key_content: str = None, 
                          ssh_key_type: str = 'rsa') -> None:
    """Configure SFTP connection to use SSH key authentication.
    
    Updates the vendor.FOO.sftp configuration to use SSH key authentication
    instead of password authentication.
    
    Parameters
        ssh_key_filename: Path to SSH private key file
        ssh_key_content: SSH private key content as string  
        ssh_key_type: Type of SSH key ('rsa', 'dsa', 'ecdsa', 'ed25519')
    """
    Setting.unlock()
    if ssh_key_filename:
        vendor.FOO.sftp.ssh_key_filename = ssh_key_filename
    if ssh_key_content:
        vendor.FOO.sftp.ssh_key_content = ssh_key_content
    vendor.FOO.sftp.ssh_key_type = ssh_key_type
    vendor.FOO.sftp.password = None  # Use key auth, not password
    Setting.lock()
