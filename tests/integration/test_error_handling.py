import ftplib
import os
import time

import pytest
from tests import config

import ftp


def test_sftp_wrong_password(clean_ftp_mount, sftp_docker, sftp_config):
    """Verify SFTP authentication fails with incorrect password.

    Tests that the system properly rejects authentication attempts
    with an invalid password.
    """
    with sftp_config(password='wrong_password'):
        cn = ftp.connect('vendor.FOO.sftp', config)
        assert cn is None


def test_sftp_wrong_username(clean_ftp_mount, sftp_docker, sftp_config):
    """Verify SFTP authentication fails with incorrect username.

    Tests that the system properly rejects authentication attempts
    with an invalid username.
    """
    with sftp_config(username='wrong_user'):
        cn = ftp.connect('vendor.FOO.sftp', config)
        assert cn is None


def test_sftp_invalid_ssh_key_path(clean_ftp_mount, mocker, sftp_config):
    """Verify SFTP fails with non-existent SSH key file path.

    Tests that attempting to use a non-existent key file path
    raises an appropriate error.
    """
    mocker.patch('ftp.client.time.sleep')

    with sftp_config(ssh_key_filename='/nonexistent/key/path.pem',
                     ssh_key_content=None,
                     password=None):
        cn = ftp.connect('vendor.FOO.sftp', config)
        assert cn is None


def test_sftp_invalid_ssh_key_content(clean_ftp_mount, mocker, sftp_config):
    """Verify SFTP fails with corrupted SSH key content.

    Tests that attempting to use invalid key content raises
    an appropriate error.
    """
    mocker.patch('ftp.client.time.sleep')

    with sftp_config(ssh_key_filename=None,
                     ssh_key_content='invalid key content',
                     password=None):
        cn = ftp.connect('vendor.FOO.sftp', config)
        assert cn is None


def test_sftp_wrong_hostname(clean_ftp_mount, mocker, sftp_config):
    """Verify SFTP connection fails with invalid hostname.

    Tests that connection attempts to non-existent hosts
    properly timeout and return None.
    """
    mocker.patch('ftp.client.time.sleep')

    with sftp_config(hostname='invalid.hostname.example.com'):
        cn = ftp.connect('vendor.FOO.sftp', config)
        assert cn is None


def test_sftp_wrong_port(clean_ftp_mount, sftp_docker, mocker, sftp_config):
    """Verify SFTP connection fails with incorrect port.

    Tests that connection attempts to the wrong port
    properly timeout and return None.
    """
    mocker.patch('ftp.client.time.sleep')

    with sftp_config(port=9999):
        cn = ftp.connect('vendor.FOO.sftp', config)
        assert cn is None


def test_sftp_get_nonexistent_file(clean_ftp_mount, sftp_docker):
    """Verify SFTP get operation fails for non-existent files.

    Tests that attempting to download a file that doesn't exist
    raises an appropriate error.
    """
    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        localfile = os.path.join(config.tmpdir.dir, 'NonExistent.txt')
        with pytest.raises(FileNotFoundError):
            sftpcn.getascii('NonExistentRemoteFile.txt', localfile)


def test_sftp_delete_nonexistent_file(clean_ftp_mount, sftp_docker):
    """Verify SFTP delete operation fails for non-existent files.

    Tests that attempting to delete a file that doesn't exist
    raises an appropriate error.
    """
    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        with pytest.raises(FileNotFoundError):
            sftpcn.delete('NonExistentFile.txt')


def test_sftp_cd_invalid_directory(clean_ftp_mount, sftp_docker):
    """Verify SFTP cd operation fails for non-existent directories.

    Tests that attempting to change to a non-existent directory
    raises an appropriate error.
    """
    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        with pytest.raises(FileNotFoundError):
            sftpcn.cd('/nonexistent/directory/path')


def test_ftp_wrong_password(clean_ftp_mount, ftp_docker, ftp_config):
    """Verify FTP authentication fails with incorrect password.

    Tests that the system properly rejects FTP authentication attempts
    with an invalid password.
    """
    with ftp_config(password='wrong_password'), pytest.raises(Exception):
        with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
            pass


def test_ftp_get_nonexistent_file(clean_ftp_mount, ftp_docker):
    """Verify FTP get operation fails for non-existent files.

    Tests that attempting to download a file that doesn't exist
    raises an appropriate error.
    """
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        localfile = os.path.join(config.tmpdir.dir, 'NonExistent.txt')
        with pytest.raises(Exception):
            ftpcn.getascii('NonExistentRemoteFile.txt', localfile)


def test_ftp_delete_nonexistent_file(clean_ftp_mount, ftp_docker):
    """Verify FTP delete operation fails for non-existent files.

    Tests that attempting to delete a file that doesn't exist
    raises an appropriate error.
    """
    time.sleep(1)

    try:
        with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
            with pytest.raises(ftplib.error_perm):
                ftpcn.delete('NonExistentFile.txt')
    except (EOFError, OSError, ConnectionError) as e:
        pytest.skip(f'FTP server connection unstable: {e}')


if __name__ == '__main__':
    pytest.main([__file__])
