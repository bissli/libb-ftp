import contextlib
from functools import wraps

import pytest
from tests import config

from libb import Setting


@contextlib.contextmanager
def temporary_config(config_path, **settings):
    """Temporarily modify config settings and restore them after.

    Parameters
        config_path: Dot-separated path to config object (e.g., 'vendor.FOO.sftp')
        **settings: Key-value pairs of settings to temporarily modify
    """
    parts = config_path.split('.')
    obj = config
    for part in parts:
        obj = getattr(obj, part)

    Setting.unlock()
    
    originals = {key: obj.get(key) for key in settings}

    try:
        for key, value in settings.items():
            setattr(obj, key, value)
        Setting.lock()
        yield
    finally:
        Setting.unlock()
        for key, value in originals.items():
            setattr(obj, key, value)
        Setting.lock()


def with_temporary_config(config_path, **settings):
    """Decorator to temporarily modify config settings for a test function.

    Parameters
        config_path: Dot-separated path to config object
        **settings: Key-value pairs of settings to temporarily modify
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with temporary_config(config_path, **settings):
                return func(*args, **kwargs)
        return wrapper
    return decorator


@pytest.fixture
def sftp_config():
    """Fixture providing temporary SFTP config modification.

    Returns callable that accepts kwargs for config modification.
    """
    def modifier(**settings):
        return temporary_config('vendor.FOO.sftp', **settings)
    return modifier


@pytest.fixture
def ftp_config():
    """Fixture providing temporary FTP config modification.

    Returns callable that accepts kwargs for config modification.
    """
    def modifier(**settings):
        return temporary_config('vendor.FOO.ftp', **settings)
    return modifier


@pytest.fixture
def configure_sftp_ssh_key_file(ssh_key_pair, sftp_config):
    """Configure SFTP to use SSH key file authentication.

    Sets up SFTP configuration to authenticate using an SSH private key file
    instead of password authentication.

    Parameters
        ssh_key_pair: SSH key pair fixture providing key paths and content
        sftp_config: Fixture for temporary SFTP config modification
    """
    with sftp_config(
        ssh_key_filename=ssh_key_pair['private_key_path'],
        ssh_key_type=ssh_key_pair['key_type'],
        password=None,
        port=2223
    ):
        yield


@pytest.fixture
def configure_sftp_ssh_key_content(ssh_key_pair, sftp_config):
    """Configure SFTP to use SSH key content authentication.

    Sets up SFTP configuration to authenticate using SSH private key content
    instead of password authentication.

    Parameters
        ssh_key_pair: SSH key pair fixture providing key paths and content
        sftp_config: Fixture for temporary SFTP config modification
    """
    with sftp_config(
        ssh_key_content=ssh_key_pair['private_key_content'],
        ssh_key_type=ssh_key_pair['key_type'],
        password=None,
        port=2223
    ):
        yield
