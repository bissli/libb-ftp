import os

import pytest
from tests import config
from tests.fixtures.test_data import make_text_file

import ftp


def test_sftp_with_explicit_ssh_key(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair, sftp_config):
    """Verify SFTP works with explicit SSH key provided.

    Tests that explicit SSH key authentication works. When credentials
    are provided, agent and key discovery are automatically disabled.
    """
    with sftp_config(ssh_key_filename=ssh_key_pair['private_key_path'],
                     ssh_key_type=ssh_key_pair['key_type'],
                     password=None,
                     port=2223):
        with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
            assert sftpcn.pwd() == '/upload'


def test_sftp_with_password(clean_ftp_mount, sftp_docker, sftp_config):
    """Verify SFTP works with password authentication.

    Tests that password authentication works. When credentials are provided,
    agent and key discovery are automatically disabled.
    """
    with sftp_config():
        with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
            assert sftpcn.pwd() == '/upload'


def test_sftp_file_operations_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair, sftp_config):
    """Verify SFTP file operations work with SSH key authentication.

    Tests complete file upload/download cycle when using explicit SSH key.
    When credentials are provided, agent and key discovery are automatically disabled.
    """
    with sftp_config(ssh_key_content=ssh_key_pair['private_key_content'],
                     ssh_key_type=ssh_key_pair['key_type'],
                     password=None,
                     port=2223):
        localfile = os.path.join(config.tmpdir.dir, 'TestAgentKeys.txt')
        make_text_file(localfile, 10)

        with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
            sftpcn.putascii(localfile, 'RemoteAgentKeys.txt')
            files = sftpcn.files()
            assert 'RemoteAgentKeys.txt' in files

            remotefile = os.path.join(config.tmpdir.dir, 'RemoteAgentKeys.txt')
            sftpcn.getascii('RemoteAgentKeys.txt', remotefile)
            assert open(localfile).read() == open(remotefile).read()

            sftpcn.delete('RemoteAgentKeys.txt')


if __name__ == '__main__':
    pytest.main([__file__])
