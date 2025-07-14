import io
from collections import deque
from unittest import mock

import pytest
from tests.fixtures.mock_connections import MockFTPConnection


@pytest.fixture
def ftp_mock():
    """Create a MockFTPConnection instance for testing.

    Provides a clean mock FTP connection for each test function.
    """
    return MockFTPConnection()


def test_delete(ftp_mock):
    """Verify delete operation works for existing files."""
    ftp_mock.delete('foo')


def test_initialization(ftp_mock):
    """Verify MockFTPConnection initializes with correct default values."""
    assert ftp_mock._files is None
    assert ftp_mock._size == 0
    assert ftp_mock._dirlist == []
    assert ftp_mock._exists is True
    assert ftp_mock._stack == deque()
    assert ftp_mock._contents == ''


def test_set_files(ftp_mock):
    """Verify _set_files method updates the files list correctly."""
    files = ['file1.txt', 'file2.txt']
    ftp_mock._set_files(files)
    assert ftp_mock._files == files


def test_set_dirlist(ftp_mock):
    """Verify _set_dirlist method updates the directory list correctly."""
    dirlist = ['dir1', 'dir2']
    ftp_mock._set_dirlist(dirlist)
    assert ftp_mock._dirlist == dirlist


def test_set_exists(ftp_mock):
    """Verify _set_exists method updates the exists flag correctly."""
    ftp_mock._set_exists(False)
    assert ftp_mock._exists is False


def test_set_contents(ftp_mock):
    """Verify _set_contents method updates the file contents correctly."""
    contents = 'file contents'
    ftp_mock._set_contents(contents)
    assert ftp_mock._contents == contents


def test_pwd(ftp_mock):
    """Verify pwd returns correct current directory path."""
    ftp_mock._stack = deque(['home', 'user'])
    assert ftp_mock.pwd() == 'home/user'


def test_cd(ftp_mock):
    """Verify cd operation updates directory stack correctly."""
    ftp_mock.cd('home/user')
    assert list(ftp_mock._stack) == ['home', 'user']
    ftp_mock.cd('..')
    assert list(ftp_mock._stack) == ['home']


def test_cd_non_existent_path(ftp_mock):
    """Verify cd raises exception for non-existent paths."""
    ftp_mock._set_exists(False)
    with pytest.raises(Exception) as excinfo:
        ftp_mock.cd('non/existent/path')
    assert str(excinfo.value) == "Doesn't exist"


def test_dir(ftp_mock):
    """Verify dir method calls callback for each directory entry."""
    dirlist = ['dir1', 'dir2']
    ftp_mock._set_dirlist(dirlist)
    callback = mock.Mock()
    ftp_mock.dir(callback)
    callback.assert_has_calls([mock.call('dir1'), mock.call('dir2')])


def test_files(ftp_mock):
    """Verify files method returns the current files list."""
    files = ['file1.txt', 'file2.txt']
    ftp_mock._set_files(files)
    assert ftp_mock.files() == files


def test_getascii(ftp_mock):
    """Verify getascii calls callback with file contents."""
    contents = 'file contents'
    ftp_mock._set_contents(contents)
    callback = mock.Mock()
    ftp_mock.getascii('remote.txt', 'local.txt', callback)
    callback.assert_called_once_with(contents)


def test_getbinary(ftp_mock):
    """Verify getbinary calls callback with file contents."""
    contents = 'file contents'
    ftp_mock._set_contents(contents)
    callback = mock.Mock()
    ftp_mock.getbinary('remote.bin', 'local.bin', callback)
    callback.assert_called_once_with(contents)


def test_putascii(ftp_mock):
    """Verify putascii accepts file stream input."""
    content = b'Lorem ipsum dolor sit amet'
    stream = io.BytesIO(content)
    ftp_mock.putascii(stream)


def test_putbinary(ftp_mock):
    """Verify putbinary accepts file stream input."""
    file = mock.Mock(spec=io.IOBase)
    assert ftp_mock.putbinary(file) is None


def test_delete_non_existent_file(ftp_mock):
    """Verify delete raises exception for non-existent files."""
    ftp_mock._set_exists(False)
    with pytest.raises(Exception) as excinfo:
        ftp_mock.delete('remote.txt')
    assert str(excinfo.value) == "Doesn't exist"


def test_close(ftp_mock):
    """Verify close operation returns True."""
    assert ftp_mock.close() is True


if __name__ == '__main__':
    pytest.main([__file__])
