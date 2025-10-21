import os

import pytest
from tests import config
from tests.fixtures.test_data import make_text_file

import ftp


def test_sftp_allow_agent_false_look_for_keys_false_with_ssh_key(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair, sftp_config):
    """Verify SFTP works with allow_agent=False and look_for_keys=False when explicit SSH key provided.

    Tests that explicit SSH key authentication works even when agent
    and key discovery are disabled.
    """
    with sftp_config(ssh_key_filename=ssh_key_pair['private_key_path'],
                     ssh_key_type=ssh_key_pair['key_type'],
                     password=None,
                     port=2223,
                     allow_agent=False,
                     look_for_keys=False):
        with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
            assert sftpcn.pwd() == '/upload'


def test_sftp_allow_agent_false_look_for_keys_false_no_credentials(clean_ftp_mount, sftp_docker, sftp_config):
    """Verify SFTP fails with allow_agent=False and look_for_keys=False without credentials.

    Tests that connection fails when both agent and key discovery are disabled
    and no explicit credentials are provided.
    """
    with sftp_config(password=None,
                     ssh_key_filename=None,
                     ssh_key_content=None,
                     allow_agent=False,
                     look_for_keys=False), pytest.raises(ValueError):
        ftp.connect('vendor.FOO.sftp', config)


def test_sftp_allow_agent_false_with_password(clean_ftp_mount, sftp_docker, sftp_config):
    """Verify SFTP works with allow_agent=False when password is provided.

    Tests that password authentication works when agent is disabled.
    """
    with sftp_config(allow_agent=False):
        with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
            assert sftpcn.pwd() == '/upload'


def test_sftp_look_for_keys_false_with_password(clean_ftp_mount, sftp_docker, sftp_config):
    """Verify SFTP works with look_for_keys=False when password is provided.

    Tests that password authentication works when key discovery is disabled.
    """
    with sftp_config(look_for_keys=False):
        with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
            assert sftpcn.pwd() == '/upload'


def test_sftp_both_false_with_password(clean_ftp_mount, sftp_docker, sftp_config):
    """Verify SFTP works with both allow_agent=False and look_for_keys=False when password provided.

    Tests that password authentication works when both agent and key
    discovery are disabled.
    """
    with sftp_config(allow_agent=False, look_for_keys=False):
        with ftp.connectmanager('vendor.FOO.sftp', config) as sftpcn:
            assert sftpcn.pwd() == '/upload'


def test_sftp_file_operations_with_agent_keys_disabled(clean_ftp_mount, sftp_docker_with_key, ssh_key_pair, sftp_config):
    """Verify SFTP file operations work with agent and key discovery disabled.

    Tests complete file upload/download cycle when using explicit SSH key
    with agent and key discovery disabled.
    """
    with sftp_config(ssh_key_content=ssh_key_pair['private_key_content'],
                     ssh_key_type=ssh_key_pair['key_type'],
                     password=None,
                     port=2223,
                     allow_agent=False,
                     look_for_keys=False):
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
