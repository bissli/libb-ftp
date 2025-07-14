import os
from collections import deque
from io import IOBase

from ftp import BaseConnection


class MockFTPConnection(BaseConnection):
    """Mock FTP connection class for testing.

    Provides a fake FTP connection that simulates server responses
    without requiring an actual FTP server.
    """
    def __init__(self):
        self._files: list = None
        self._size: float = 0
        self._dirlist: list = []
        self._exists: bool = True
        self._stack = deque()
        self._contents: str = ''

    def _set_files(self, files: list) -> None:
        """Set the list of files that will be returned by files() method.

        Parameters
            files: List of filenames to simulate on the server
        """
        self._files = files

    def _set_dirlist(self, dirlist: list) -> None:
        """Set the directory listing that will be returned by dir() method.

        Parameters
            dirlist: List of directory entries to simulate
        """
        self._dirlist = dirlist

    def _set_exists(self, exists: bool) -> None:
        """Set whether files/directories should appear to exist.

        Parameters
            exists: Whether operations should succeed or fail with "doesn't exist"
        """
        self._exists = exists

    def _set_contents(self, contents: str) -> None:
        """Set the contents that will be returned by get operations.

        Parameters
            contents: File content to return when downloading files
        """
        self._contents = contents

    def pwd(self) -> str:
        """Return the current working directory path.

        Returns
            Current directory path as string
        """
        return '/'.join(self._stack)

    def cd(self, path: str) -> None:
        """Change to the specified directory.

        Parameters
            path: Directory path to navigate to
        """
        path = as_posix(path)
        if not self._exists:
            self._exists = True
            raise Exception("Doesn't exist")
        for dir_ in path.split('/'):
            if dir_ == '..':
                self._stack.pop()
            else:
                self._stack.append(dir_)

    def dir(self, callback) -> None:
        """List directory contents by calling callback for each entry.

        Parameters
            callback: Function to call with each directory entry
        """
        for dir_ in self._dirlist:
            callback(dir_)

    def files(self) -> list:
        """Return the list of files in current directory.

        Returns
            List of filenames
        """
        return self._files

    def getascii(self, remotefile: str, localfile: str, callback) -> None:
        """Download file in ASCII mode.

        Parameters
            remotefile: Remote filename to download
            localfile: Local filename to save to
            callback: Callback function to receive file contents
        """
        callback(self._contents)

    getbinary = getascii

    def putascii(self, f: IOBase, *_):
        """Upload file in ASCII mode.

        Parameters
            f: File object to upload
        """
        self._set_files

    putbinary = putascii

    def delete(self, remotefile: str) -> bool:
        """Delete a file from the server.

        Parameters
            remotefile: Remote filename to delete

        Returns
            True if deletion succeeded
        """
        if not self._exists:
            raise Exception("Doesn't exist")
        return True

    def close(self) -> bool:
        """Close the connection.

        Returns
            True indicating successful closure
        """
        return True


def as_posix(path: str) -> str:
    """Convert path to POSIX format.

    Parameters
        path: Path string to convert

    Returns
        Path with forward slashes
    """
    if not path:
        return path
    return str(path).replace(os.sep, '/')
