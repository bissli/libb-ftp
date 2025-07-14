import os
import tempfile

import paramiko
import pytest


@pytest.fixture
def ssh_key_pair():
    """Generate SSH key pair for testing.

    Creates a temporary RSA key pair that can be used for SSH authentication
    testing with the SFTP server.

    Returns
        Dictionary containing key paths and content for testing
    """
    key = paramiko.RSAKey.generate(2048)

    with tempfile.NamedTemporaryFile(mode='w', suffix='_rsa', delete=False) as private_file:
        key.write_private_key(private_file)
        private_key_path = private_file.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='_rsa.pub', delete=False) as public_file:
        public_file.write(f'{key.get_name()} {key.get_base64()}')
        public_key_path = public_file.name

    private_key_content = ''
    with open(private_key_path) as f:
        private_key_content = f.read()

    yield {
        'private_key_path': private_key_path,
        'public_key_path': public_key_path,
        'private_key_content': private_key_content,
        'key_type': 'rsa'
        }

    os.unlink(private_key_path)
    os.unlink(public_key_path)
