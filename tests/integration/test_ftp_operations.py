import contextlib
import os

import pytest
from tests import config
from src.ftp.client import sync_site
from tests.fixtures.test_data import create_local_file, make_binary_file
from tests.fixtures.test_data import make_text_file

import ftp


def test_ftp_pwd(clean_ftp_mount, ftp_docker):
    """Verify FTP pwd operation returns correct working directory."""
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        assert ftpcn.pwd() == '/'


def test_ftp_change_directory(ftp_docker):
    """Verify FTP directory navigation works correctly."""
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        initial_dir = ftpcn.pwd()
        ftpcn.cd('/')
        assert ftpcn.pwd() == '/'
        ftpcn.cd(initial_dir)
        assert ftpcn.pwd() == initial_dir


def test_ftp_dir(clean_ftp_mount, ftp_docker):
    """Verify FTP directory listing shows uploaded files."""
    local_dir = os.path.join(config.tmpdir.dir, 'local_dir')
    local_file1 = os.path.join(local_dir, 'LocalFile1.txt')
    local_file2 = os.path.join(local_dir, 'LocalFile2.txt')
    os.makedirs(local_dir, exist_ok=True)
    make_text_file(local_file1, 10)
    make_text_file(local_file2, 10)

    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        ftpcn.putascii(local_file1, 'RemoteFile1.txt')
        ftpcn.putascii(local_file2, 'RemoteFile2.txt')

        entries = ftpcn.dir()
        assert len(entries) > 0
        file_names = [entry.name for entry in entries]

        assert 'RemoteFile1.txt' in file_names
        assert 'RemoteFile2.txt' in file_names


def test_ftp_put_ascii(clean_ftp_mount, ftp_docker):
    """Verify FTP ASCII file upload and download maintains content integrity."""
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
    """Verify FTP binary file upload and download maintains content integrity."""
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
    """Verify FTP ASCII file retrieval works correctly."""
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
    """Verify FTP binary file retrieval works correctly."""
    localfile = os.path.join(config.tmpdir.dir, 'Local.dat')
    make_binary_file(localfile, 1000)
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        with contextlib.suppress(Exception):
            ftpcn.delete('Remote.dat')
        ftpcn.putbinary(localfile, 'Remote.dat')
        files = ftpcn.files()
        assert 'Remote.dat' in files
        remotefile = os.path.join(config.tmpdir.dir, 'Remote.dat')
        ftpcn.getbinary('Remote.dat', remotefile)
        assert open(localfile, 'rb').read() == open(remotefile, 'rb').read()


def test_ftp_delete(clean_ftp_mount, ftp_docker):
    """Verify FTP file deletion removes files from server."""
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
    """Verify FTP connection manager establishes valid connections."""
    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        assert ftpcn is not None
        assert ftpcn.pwd() == '/'


def test_sync_site(clean_ftp_mount, ftp_docker):
    """Verify FTP site synchronization downloads remote files correctly."""
    localfile1 = create_local_file('foofile.txt')

    with ftp.connectmanager('vendor.FOO.ftp', config) as ftpcn:
        ftpcn.putascii(localfile1, 'foofile.txt')

    os.remove(localfile1)

    sync_site('vendor.FOO.ftp', config)

    assert os.path.exists(localfile1)
    with open(localfile1) as f:
        lines = f.readlines()
        assert len(lines) == 10


if __name__ == '__main__':
    pytest.main([__file__])
