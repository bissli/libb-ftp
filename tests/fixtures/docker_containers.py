import logging
import os
import pathlib
import shutil
import subprocess
import tempfile
import time

import docker
import pytest
from tests import config

logger = logging.getLogger(__name__)


def remove_files(path: str) -> None:
    """Remove all files from a directory.

    Parameters
        path: Directory path to clean
    """
    for file in os.scandir(path):
        pathlib.Path(file.path).unlink()


@pytest.fixture
def clean_ftp_mount():
    """Clean the FTP mount directory before and after tests.

    Ensures each test starts with a clean FTP mount directory
    and cleans up after completion.
    """
    remove_files(config.mountdir)
    yield
    remove_files(config.mountdir)


@pytest.fixture(scope='session')
def ftp_docker(request):
    """Docker fixture for FTP server using garethflowers/ftp-server.

    Creates an FTP server container for testing regular FTP connections.
    """
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
def ftp_docker_nonstandard_port(request):
    """Docker fixture for FTP server on non-standard port 2121.

    Verifies that the port parameter is correctly passed through the FTP connection.
    Uses different passive mode ports (40010-40019) to avoid collision with ftp_docker.
    """
    client = docker.from_env()
    container = client.containers.run(
        image='garethflowers/ftp-server',
        auto_remove=True,
        environment={
            'FTP_USER': config.vendor.FOO.ftp.username,
            'FTP_PASS': config.vendor.FOO.ftp.password,
            'PASV_MIN_PORT': '40010',
            'PASV_MAX_PORT': '40019',
            },
        name='ftp_server_nonstandard',
        ports={
            '21/tcp': (config.vendor.FOO.ftp.hostname, '2121'),
            **{f'{port}/tcp': (config.vendor.FOO.ftp.hostname, f'{port}') for port in range(40010, 40020)},
            },
        volumes={config.mountdir: {'bind': '/data', 'mode': 'rw'}},
        detach=True,
        remove=True,
    )
    time.sleep(5)

    def cleanup():
        try:
            container.stop()
        except docker.errors.NotFound:
            pass

    request.addfinalizer(cleanup)


@pytest.fixture(scope='session')
def sftp_docker(request):
    """Docker fixture for SFTP server using atmoz/sftp Debian image.

    Creates a secure SFTP server container for testing secure FTP connections.
    Uses the same credentials as the FTP fixture but on port 22.
    """
    client = docker.from_env()

    try:
        subprocess.run(['chown', '1001:1001', config.mountdir], check=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug('chown failed, falling back to chmod permissions')
        pathlib.Path(config.mountdir).chmod(0o777)

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


@pytest.fixture
def sftp_docker_with_key(request, ssh_key_pair):
    """Docker fixture for SFTP server with SSH key authentication enabled.

    Creates a secure SFTP server container that accepts the provided SSH key
    for authentication testing. Uses port 2223 to avoid conflicts.
    """
    client = docker.from_env()

    sftp_data_dir = tempfile.mkdtemp(prefix='sftp_test_')
    logger.debug(f'Created temp SFTP data dir {sftp_data_dir}')

    ssh_keys_dir = tempfile.mkdtemp(prefix='sftp_ssh_keys_')
    logger.debug(f'Created temp SSH keys dir {ssh_keys_dir}')

    username = config.vendor.FOO.ftp.username
    authorized_key_path = os.path.join(ssh_keys_dir, f'{username}.pub')
    shutil.copy2(ssh_key_pair['public_key_path'], authorized_key_path)

    try:
        subprocess.run(['chown', '1001:1001', sftp_data_dir], check=True, stderr=subprocess.DEVNULL)
        subprocess.run(['chown', '1001:1001', ssh_keys_dir], check=True, stderr=subprocess.DEVNULL)
        subprocess.run(['chown', '1001:1001', authorized_key_path], check=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug('chown failed, falling back to chmod permissions')
        pathlib.Path(sftp_data_dir).chmod(0o777)
        pathlib.Path(ssh_keys_dir).chmod(0o755)
        pathlib.Path(authorized_key_path).chmod(0o644)

    volumes = {
        sftp_data_dir: {'bind': f'/home/{username}/upload', 'mode': 'rw'},
        ssh_keys_dir: {'bind': f'/home/{username}/.ssh/keys', 'mode': 'ro'}
    }

    container = client.containers.run(
        image='atmoz/sftp',
        auto_remove=True,
        command=f'{username}::1001::upload',
        name='sftp_server_with_key',
        ports={'22/tcp': (config.vendor.FOO.ftp.hostname, '2223')},
        volumes=volumes,
        detach=True,
        remove=True,
    )
    time.sleep(5)

    def cleanup():
        container.stop()
        shutil.rmtree(sftp_data_dir, ignore_errors=True)
        shutil.rmtree(ssh_keys_dir, ignore_errors=True)

    request.addfinalizer(cleanup)
    return container
