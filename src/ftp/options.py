import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import DefaultDict, List

from date import LCL
from ftp.config import tmpdir
from libb import ConfigOptions


def is_encrypted():
    def wrapper(filename: str):
        return 'pgp' in filename.split('.')
    return wrapper


def rename_pgp():
    def wrapper(pgpname: str):
        bits = pgpname.split('.')
        bits.remove('pgp')
        return '.'.join(bits)
    return wrapper


@dataclass
class FtpOptions(ConfigOptions):

    # sitename for repr
    sitename: str = None

    # connetion required
    hostname: str = None
    username: str = None
    password: str = None
    secure: bool = False
    port: int = 22

    # connection optional
    pgp_extension: str = None
    ignore_re: str = None
    is_encrypted: callable = field(default_factory=is_encrypted, repr=False)
    rename_pgp: callable = field(default_factory=rename_pgp, repr=False)
    localdir: str = tmpdir.dir
    remotedir: str = '/'

    # for sync
    nocopy: bool = False
    nodecryptlocal: bool = False
    ignorelocal:bool = False
    ignoresize: bool = False
    ignoreolderthan: int | None = None
    address: List = field(default_factory=list)
    stats: DefaultDict = field(init=False)
    tzinfo = LCL

    def __post_init__(self):
        self.stats = defaultdict(int)
        self.localdir = Path(self.localdir)
        self.remotedir = str(self.remotedir).replace(os.sep, '/')


__all__ = ['FtpOptions']


if __name__ == '__main__':
    options = FtpOptions(hostname='127.0.0.1', username='foo', password='bar')
    print(options.rename_pgp('test.pgp'))
    options.stats['test'] += 1
    print(options.__dict__)
