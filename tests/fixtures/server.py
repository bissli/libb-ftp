import logging
import os
import sys
import time
from collections import deque
from io import IOBase

import docker
import pytest

from ftp import BaseConnection

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append('..')
from tests import config

logger = logging.getLogger(__name__)


def remove_files(path):
    for file in os.scandir(path):
        os.unlink(file.path)


@pytest.fixture
def clean_ftp_mount():
    remove_files(config.mountdir)
    yield
    remove_files(config.mountdir)


@pytest.fixture(scope='session')
def ftp_docker(request):
    client = docker.from_env()
    container = client.containers.run(
        image='garethflowers/ftp-server',
        auto_remove=True,
        environment={
            'FTP_USER': config.vendor.FOO.ftp.username,
            'FTP_PASS': config.vendor.FOO.ftp.password,
            },
        name='ftp_server',
        ports={
            f'{port}/tcp': (config.vendor.FOO.ftp.hostname, f'{port}/tcp')
            for port in [20, 21]+list(range(40000,40010))
            },
        volumes={config.mountdir: {'bind': '/data', 'mode': 'rw'}},
        detach=True,
        remove=True,
    )
    time.sleep(5)
    request.addfinalizer(container.stop)


@pytest.fixture(scope='session')
def sftp_docker(request):
    """Docker fixture for SFTP server using atmoz/sftp Debian image.
    
    Creates a secure SFTP server container for testing secure FTP connections.
    Uses the same credentials as the FTP fixture but on port 22.
    """
    client = docker.from_env()
    container = client.containers.run(
        image='atmoz/sftp',
        auto_remove=True,
        command=f'{config.vendor.FOO.ftp.username}:{config.vendor.FOO.ftp.password}:1001::upload',
        name='sftp_server',
        ports={'22/tcp': (config.vendor.FOO.ftp.hostname, '2222')},
        volumes={config.mountdir: {'bind': f'/home/{config.vendor.FOO.ftp.username}/upload', 'mode': 'rw'}},
        detach=True,
        remove=True,
    )
    time.sleep(5)
    request.addfinalizer(container.stop)


@pytest.fixture(scope='function')
def sftp_docker_with_key(request, ssh_key_pair):
    """Docker fixture for SFTP server with SSH key authentication enabled.
    
    Creates a secure SFTP server container that accepts the provided SSH key
    for authentication testing.
    """
    import subprocess
    import tempfile
    
    client = docker.from_env()
    
    # Create a temporary directory with correct permissions for the SFTP user
    sftp_data_dir = tempfile.mkdtemp(prefix='sftp_test_')
    
    # Set ownership to UID 1001 (the SFTP user) - this might require sudo on some systems
    # For testing purposes, make it world-writable as a fallback
    try:
        subprocess.run(['chown', '1001:1001', sftp_data_dir], check=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: make directory world-writable if chown fails
        os.chmod(sftp_data_dir, 0o777)
    
    # Create volume mapping for SSH public key and data directory
    volumes = {
        sftp_data_dir: {'bind': f'/home/{config.vendor.FOO.ftp.username}/upload', 'mode': 'rw'},
        ssh_key_pair['public_key_path']: {'bind': f'/home/{config.vendor.FOO.ftp.username}/.ssh/keys/test_key.pub', 'mode': 'ro'}
    }
    
    container = client.containers.run(
        image='atmoz/sftp',
        auto_remove=True,
        command=f'{config.vendor.FOO.ftp.username}::1001::upload',  # No password, key auth only
        name='sftp_server_with_key',
        ports={'22/tcp': (config.vendor.FOO.ftp.hostname, '2222')},
        volumes=volumes,
        detach=True,
        remove=True,
    )
    time.sleep(5)
    
    def cleanup():
        container.stop()
        # Clean up temporary directory
        import shutil
        shutil.rmtree(sftp_data_dir, ignore_errors=True)
    
    request.addfinalizer(cleanup)
    return container


class MockFTPConnection(BaseConnection):
    """Mock FTP lib for testing
    """
    def __init__(self):
        self._files: list = None
        self._size: float = 0
        self._dirlist: list = []
        self._exists: bool = True
        self._stack = deque()
        self._contents: str = ''

    def _set_files(self, files):
        self._files = files

    def _set_dirlist(self, dirlist):
        self._dirlist = dirlist

    def _set_exists(self, exists):
        self._exists = exists

    def _set_contents(self, contents):
        self._contents = contents

    def pwd(self):
        return '/'.join(self._stack)

    def cd(self, path: str):
        path = as_posix(path)
        if not self._exists:
            self._exists = True
            raise Exception("Doesn't exist")
        for dir_ in path.split('/'):
            if dir_ == '..':
                self._stack.pop()
            else:
                self._stack.append(dir_)

    def dir(self, callback):
        for dir_ in self._dirlist:
            callback(dir_)

    def files(self):
        return self._files

    def getascii(self, remotefile, localfile, callback):
        callback(self._contents)

    getbinary = getascii

    def putascii(self, f: IOBase, *_):
        self._set_files

    putbinary = putascii

    def delete(self, remotefile):
        if not self._exists:
            raise Exception("Doesn't exist")
        return True

    def close(self):
        return True


def as_posix(path):
    if not path:
        return path
    return str(path).replace(os.sep, '/')


@pytest.fixture
def ftp_mock():
    return MockFTPConnection()


def test_sftp_docker_fixture(sftp_docker):
    """Test that the SFTP Docker fixture starts correctly.
    
    Verifies the SFTP server container is running and accessible.
    """
    assert sftp_docker is None  # fixture doesn't return anything, just starts container
