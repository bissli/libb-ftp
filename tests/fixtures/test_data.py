import os
import struct

from tests import config


def make_text_file(filename: str, lines: int) -> None:
    """Create a text file with numbered lines.

    Parameters
        filename: Path where the file should be created
        lines: Number of lines to write to the file
    """
    with open(filename, 'w') as f:
        f.writelines(f'Line {i}\n' for i in range(lines))


def make_binary_file(filename: str, ints: int) -> None:
    """Create a binary file with packed integers.

    Parameters
        filename: Path where the file should be created
        ints: Number of integers to pack into the file
    """
    with open(filename, 'wb') as f:
        for i in range(ints):
            n = struct.pack('i', i)
            f.write(n)


def create_local_file(filename: str = 'foofile.txt') -> str:
    """Create a test file in the mount directory.

    Parameters
        filename: Name of the file to create

    Returns
        Full path to the created file
    """
    localfile1 = os.path.join(config.mountdir, filename)
    make_text_file(localfile1, 10)
    return localfile1
