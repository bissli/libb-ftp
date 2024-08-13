import contextlib
import os
import struct

import config
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


if __name__ == '__main__':
    pytest.main([__file__])
