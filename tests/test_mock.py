import pytest


def test_delete(ftp_mock):
    ftp_mock.delete('foo')


if __name__ == '__main__':
    pytest.main([__file__])
