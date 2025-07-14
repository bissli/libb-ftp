import contextlib
import os
import struct
import tempfile

import config
import paramiko
import pytest
from src.ftp.client import sync_site

import ftp


def make_text_file(filename, lines):
    with open(filename, 'w') as f:
        f.writelines('Line %d\n' % i for i in range(lines))


def make_binary_file(filename, ints):
    with open(filename, 'wb') as f:
        for i in range(ints):
            n = struct.pack('i', i)
            f.write(n)


def create_local_file(filename='foofile.txt'):
    localfile1 = os.path.join(config.mountdir, filename)
    make_text_file(localfile1, 10)
    return localfile1


def test_ftp_pwd(clean_ftp_mount, ftp_docker):
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        assert ftpcn.pwd() == '/'


def test_ftp_change_directory(ftp_docker):
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        initial_dir = ftpcn.pwd()
        ftpcn.cd('/')
        assert ftpcn.pwd() == '/'
        ftpcn.cd(initial_dir)
        assert ftpcn.pwd() == initial_dir


def test_ftp_dir(clean_ftp_mount, ftp_docker):
    localDir = os.path.join(config.tmpdir.dir, 'LocalDir')
    localFile1 = os.path.join(localDir, 'LocalFile1.txt')
    localFile2 = os.path.join(localDir, 'LocalFile2.txt')
    os.makedirs(localDir, exist_ok=True)
    make_text_file(localFile1, 10)
    make_text_file(localFile2, 10)

    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        ftpcn.putascii(localFile1, 'RemoteFile1.txt')
        ftpcn.putascii(localFile2, 'RemoteFile2.txt')

        entries = ftpcn.dir()
        assert len(entries) > 0
        file_names = [entry.name for entry in entries]

        assert 'RemoteFile1.txt' in file_names
        assert 'RemoteFile2.txt' in file_names


def test_ftp_put_ascii(clean_ftp_mount, ftp_docker):
    localfile = os.path.join(config.tmpdir.dir, 'Local.txt')
    make_text_file(localfile, 10)
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        with contextlib.suppress(Exception):
            ftpcn.delete('Remote.txt')
        files = ftpcn.files()
        assert 'Remote.txt' not in files
        ftpcn.putascii(localfile, 'Remote.txt')
        files = ftpcn.files()
        assert 'Remote.txt' in files
        remotefile = os.path.join(config.tmpdir.dir, 'Remote.txt')
        ftpcn.getascii('Remote.txt', remotefile)
        assert open(localfile).read() == open(remotefile).read()


def test_ftp_put_binary(clean_ftp_mount, ftp_docker):
    localfile = os.path.join(config.tmpdir.dir, 'Local.dat')
    make_binary_file(localfile, 1000)
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        with contextlib.suppress(Exception):
            ftpcn.delete('Remote.dat')
        files = ftpcn.files()
        assert 'Remote.dat' not in files
        ftpcn.putbinary(localfile, 'Remote.dat')
        files = ftpcn.files()
        assert 'Remote.dat' in files
        remotefile = os.path.join(config.tmpdir.dir, 'Remote.dat')
        ftpcn.getbinary('Remote.dat', remotefile)
        assert open(localfile, 'rb').read() == open(remotefile, 'rb').read()


def test_ftp_get_ascii(clean_ftp_mount, ftp_docker):
    localfile = os.path.join(config.tmpdir.dir, 'LocalAscii.txt')
    make_text_file(localfile, 10)
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        with contextlib.suppress(Exception):
            ftpcn.delete('RemoteAscii.txt')
        ftpcn.putascii(localfile, 'RemoteAscii.txt')
        files = ftpcn.files()
        assert 'RemoteAscii.txt' in files
        remotefile = os.path.join(config.tmpdir.dir, 'RemoteAscii.txt')
        ftpcn.getascii('RemoteAscii.txt', remotefile)
        assert open(localfile).read() == open(remotefile).read()


def test_ftp_get_binary(clean_ftp_mount, ftp_docker):
    localfile = os.path.join(config.tmpdir.dir, 'Local.dat')
    make_binary_file(localfile, 1000)
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        print(ftpcn.pwd)
        with contextlib.suppress(Exception):
            ftpcn.delete('Remote.dat')
        ftpcn.putbinary(localfile, 'Remote.dat')
        files = ftpcn.files()
        assert 'Remote.dat' in files
        remotefile = os.path.join(config.tmpdir.dir, 'Remote.dat')
        ftpcn.getbinary('Remote.dat', remotefile)
        assert open(localfile, 'rb').read() == open(remotefile, 'rb').read()


def test_ftp_delete(clean_ftp_mount, ftp_docker):
    localfile = os.path.join(config.tmpdir.dir, 'ToDelete.txt')
    make_text_file(localfile, 10)
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        ftpcn.putascii(localfile, 'RemoteToDelete.txt')
        files = ftpcn.files()
        assert 'RemoteToDelete.txt' in files
        ftpcn.delete('RemoteToDelete.txt')
        files = ftpcn.files()
        assert 'RemoteToDelete.txt' not in files


def test_connect_manager(ftp_docker):
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        assert ftpcn is not None
        assert ftpcn.pwd() == '/'


def test_sync_site(clean_ftp_mount, ftp_docker):
    localfile1 = create_local_file('foofile.txt')

    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        ftpcn.putascii(localfile1, 'foofile.txt')

    os.remove(localfile1)

    sync_site('vendor.FOO.ftp', config)

    assert os.path.exists(localfile1)
    with open(localfile1) as f:
        lines = f.readlines()
        assert len(lines) == 10


@pytest.fixture
def ssh_key_pair():
    """Generate SSH key pair for testing.

    Creates a temporary RSA key pair that can be used for SSH authentication
    testing with the SFTP server.
    """

    # Generate RSA key pair
    key = paramiko.RSAKey.generate(2048)

    # Create temporary files for the keys
    with tempfile.NamedTemporaryFile(mode='w', suffix='_rsa', delete=False) as private_file:
        key.write_private_key(private_file)
        private_key_path = private_file.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='_rsa.pub', delete=False) as public_file:
        public_file.write(f'{key.get_name()} {key.get_base64()}')
        public_key_path = public_file.name

    # Get private key content as string
    private_key_content = ''
    with open(private_key_path) as f:
        private_key_content = f.read()

    yield {
        'private_key_path': private_key_path,
        'public_key_path': public_key_path,
        'private_key_content': private_key_content,
        'key_type': 'rsa'
        }

    # Cleanup
    os.unlink(private_key_path)
    os.unlink(public_key_path)


def test_sftp_pwd_with_ssh_key_file(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair):
    """Test SFTP pwd operation using SSH key file authentication.

    Verifies that SSH key file authentication works with the SFTP server
    and basic directory operations function correctly.
    """
    config.configure_sftp_ssh_key(
        ssh_key_filename=ssh_key_pair['private_key_path'],
        ssh_key_type=ssh_key_pair['key_type']
        )

    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        assert sftpcn.pwd() == '/upload'


def test_sftp_pwd_with_ssh_key_content(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair):
    """Test SFTP pwd operation using SSH key content authentication.

    Verifies that SSH key content (string) authentication works with the SFTP server
    and basic directory operations function correctly.
    """
    config.configure_sftp_ssh_key(
        ssh_key_content=ssh_key_pair['private_key_content'],
        ssh_key_type=ssh_key_pair['key_type']
        )

    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        assert sftpcn.pwd() == '/upload'


def test_sftp_put_ascii_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair):
    """Test SFTP ASCII file upload using SSH key authentication.

    Verifies that file upload operations work correctly when using SSH key
    authentication instead of password authentication.
    """
    config.configure_sftp_ssh_key(
        ssh_key_filename=ssh_key_pair['private_key_path'],
        ssh_key_type=ssh_key_pair['key_type']
        )

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


def test_sftp_put_binary_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair):
    """Test SFTP binary file upload using SSH key authentication.

    Verifies that binary file operations work correctly when using SSH key
    authentication for secure file transfers.
    """
    config.configure_sftp_ssh_key(
        ssh_key_content=ssh_key_pair['private_key_content'],
        ssh_key_type=ssh_key_pair['key_type']
        )

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


def test_sftp_dir_listing_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair):
    """Test SFTP directory listing using SSH key authentication.

    Verifies that directory operations and file listing work correctly
    with SSH key authentication.
    """
    config.configure_sftp_ssh_key(
        ssh_key_filename=ssh_key_pair['private_key_path'],
        ssh_key_type=ssh_key_pair['key_type']
        )

    localDir = os.path.join(config.tmpdir.dir, 'SftpLocalDir')
    localFile1 = os.path.join(localDir, 'SftpLocalFile1.txt')
    localFile2 = os.path.join(localDir, 'SftpLocalFile2.txt')
    os.makedirs(localDir, exist_ok=True)
    make_text_file(localFile1, 5)
    make_text_file(localFile2, 5)

    with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
        sftpcn.putascii(localFile1, 'SftpRemoteFile1.txt')
        sftpcn.putascii(localFile2, 'SftpRemoteFile2.txt')

        entries = sftpcn.dir()
        assert len(entries) >= 2
        file_names = [entry.name for entry in entries]

        assert 'SftpRemoteFile1.txt' in file_names
        assert 'SftpRemoteFile2.txt' in file_names


def test_sftp_delete_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair):
    """Test SFTP file deletion using SSH key authentication.

    Verifies that file deletion operations work correctly when using
    SSH key authentication.
    """
    config.configure_sftp_ssh_key(
        ssh_key_content=ssh_key_pair['private_key_content'],
        ssh_key_type=ssh_key_pair['key_type']
        )

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
