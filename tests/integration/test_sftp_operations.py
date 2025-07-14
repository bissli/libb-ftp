import contextlib
import os

import pytest
from tests import config
from tests.fixtures.test_data import make_binary_file, make_text_file

import ftp


def test_sftp_pwd_with_ssh_key_file(clean_ftp_mount, sftp_docker_with_key, configure_sftp_ssh_key_file):
    """Verify SFTP pwd operation using SSH key file authentication.

    Tests that SSH key file authentication works with the SFTP server
    and basic directory operations function correctly.
    """
    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        assert sftpcn.pwd() == '/upload'


def test_sftp_pwd_with_ssh_key_content(clean_ftp_mount, sftp_docker_with_key, configure_sftp_ssh_key_content):
    """Verify SFTP pwd operation using SSH key content authentication.

    Tests that SSH key content (string) authentication works with the SFTP server
    and basic directory operations function correctly.
    """
    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        assert sftpcn.pwd() == '/upload'


def test_sftp_put_ascii_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, configure_sftp_ssh_key_file):
    """Verify SFTP ASCII file upload using SSH key authentication.

    Tests that file upload operations work correctly when using SSH key
    authentication instead of password authentication.
    """

    localfile = os.path.join(config.tmpdir.dir, 'SftpLocal.txt')
    make_text_file(localfile, 10)

    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        with contextlib.suppress(Exception):
            sftpcn.delete('SftpRemote.txt')
        files = sftpcn.files()
        assert 'SftpRemote.txt' not in files
        sftpcn.putascii(localfile, 'SftpRemote.txt')
        files = sftpcn.files()
        assert 'SftpRemote.txt' in files
        remotefile = os.path.join(config.tmpdir.dir, 'SftpRemote.txt')
        sftpcn.getascii('SftpRemote.txt', remotefile)
        assert open(localfile).read() == open(remotefile).read()


def test_sftp_put_binary_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, configure_sftp_ssh_key_content):
    """Verify SFTP binary file upload using SSH key authentication.

    Tests that binary file operations work correctly when using SSH key
    authentication for secure file transfers.
    """

    localfile = os.path.join(config.tmpdir.dir, 'SftpLocal.dat')
    make_binary_file(localfile, 1000)

    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        with contextlib.suppress(Exception):
            sftpcn.delete('SftpRemote.dat')
        files = sftpcn.files()
        assert 'SftpRemote.dat' not in files
        sftpcn.putbinary(localfile, 'SftpRemote.dat')
        files = sftpcn.files()
        assert 'SftpRemote.dat' in files
        remotefile = os.path.join(config.tmpdir.dir, 'SftpRemote.dat')
        sftpcn.getbinary('SftpRemote.dat', remotefile)
        assert open(localfile, 'rb').read() == open(remotefile, 'rb').read()


def test_sftp_dir_listing_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, configure_sftp_ssh_key_file):
    """Verify SFTP directory listing using SSH key authentication.

    Tests that directory operations and file listing work correctly
    with SSH key authentication.
    """

    local_dir = os.path.join(config.tmpdir.dir, 'sftp_local_dir')
    local_file1 = os.path.join(local_dir, 'SftpLocalFile1.txt')
    local_file2 = os.path.join(local_dir, 'SftpLocalFile2.txt')
    os.makedirs(local_dir, exist_ok=True)
    make_text_file(local_file1, 5)
    make_text_file(local_file2, 5)

    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        sftpcn.putascii(local_file1, 'SftpRemoteFile1.txt')
        sftpcn.putascii(local_file2, 'SftpRemoteFile2.txt')

        entries = sftpcn.dir()
        assert len(entries) >= 2
        file_names = [entry.name for entry in entries]

        assert 'SftpRemoteFile1.txt' in file_names
        assert 'SftpRemoteFile2.txt' in file_names


def test_sftp_delete_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, configure_sftp_ssh_key_content):
    """Verify SFTP file deletion using SSH key authentication.

    Tests that file deletion operations work correctly when using
    SSH key authentication.
    """

    localfile = os.path.join(config.tmpdir.dir, 'SftpToDelete.txt')
    make_text_file(localfile, 5)

    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        sftpcn.putascii(localfile, 'SftpRemoteToDelete.txt')
        files = sftpcn.files()
        assert 'SftpRemoteToDelete.txt' in files
        sftpcn.delete('SftpRemoteToDelete.txt')
        files = sftpcn.files()
        assert 'SftpRemoteToDelete.txt' not in files


if __name__ == '__main__':
    pytest.main([__file__])
