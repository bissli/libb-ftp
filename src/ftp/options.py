import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from date import LCL
from ftp.config import tmpdir
from libb import ConfigOptions


def is_encrypted():
    def wrapper(filename: str):
        return 'pgp' in Path(filename).name.split('.')
    return wrapper


def rename_pgp():
    def wrapper(pgpname: str):
        bits = Path(pgpname).name.split('.')
        bits.remove('pgp')
        return '.'.join(bits)
    return wrapper


@dataclass
class FtpOptions(ConfigOptions):

    # Sitename for repr
    sitename: str = None

    # Connetion required
    hostname: str = None
    username: str = None
    password: str = None
    secure: bool = False
    port: int = None

    # SSH key authentication (for secure connections)
    ssh_key_filename: str | Path = None
    ssh_key_content: str = None
    ssh_key_passphrase: str = None
    ssh_key_type: str = 'rsa'

    # Connection optional
    pgp_extension: str = None
    ignore_re: str = None
    is_encrypted: callable = field(default_factory=is_encrypted, repr=False)
    rename_pgp: callable = field(default_factory=rename_pgp, repr=False)
    localdir: Path = tmpdir.dir
    remotedir: str = '/'

    # For sync
    nocopy: bool = False
    nodecryptlocal: bool = False
    ignorelocal:bool = False
    ignoresize: bool = False
    ignoreolderthan: int | None = None
    address: list = field(default_factory=list)
    stats: defaultdict = field(init=False)
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
