import pytest

from libb import Setting


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
    from tests import config

    Setting.unlock()

    config.vendor.FOO.sftp.ssh_key_filename = ssh_key_filename
    config.vendor.FOO.sftp.ssh_key_content = ssh_key_content
    config.vendor.FOO.sftp.ssh_key_type = ssh_key_type
    config.vendor.FOO.sftp.password = None  # Use key auth, not password

    Setting.lock()


@pytest.fixture
def configure_sftp_ssh_key_file(ssh_key_pair) -> None:
    """Configure SFTP to use SSH key file authentication.

    Sets up SFTP configuration to authenticate using an SSH private key file
    instead of password authentication.

    Parameters
        ssh_key_pair: SSH key pair fixture providing key paths and content
    """
    configure_sftp_ssh_key(
        ssh_key_filename=ssh_key_pair['private_key_path'],
        ssh_key_type=ssh_key_pair['key_type']
    )


@pytest.fixture
def configure_sftp_ssh_key_content(ssh_key_pair) -> None:
    """Configure SFTP to use SSH key content authentication.

    Sets up SFTP configuration to authenticate using SSH private key content
    instead of password authentication.

    Parameters
        ssh_key_pair: SSH key pair fixture providing key paths and content
    """
    configure_sftp_ssh_key(
        ssh_key_content=ssh_key_pair['private_key_content'],
        ssh_key_type=ssh_key_pair['key_type']
    )
