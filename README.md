# libb-ftp

A comprehensive FTP/SFTP client library with encryption support for secure file transfers and synchronization.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [FtpOptions Configuration](#ftpoptions-configuration)
- [Quick Start](#quick-start)
- [Connection Types](#connection-types)
  - [Basic FTP](#basic-ftp)
  - [Secure SFTP](#secure-sftp)
  - [SSH Key Authentication](#ssh-key-authentication)
- [File Synchronization](#file-synchronization)
  - [Basic Sync](#basic-sync)
  - [Advanced Filtering](#advanced-filtering)
  - [Sync Options](#sync-options)
- [PGP Encryption/Decryption](#pgp-encryptiondecryption)
  - [Single File Decryption](#single-file-decryption)
  - [Batch Decryption](#batch-decryption)
- [API Reference](#api-reference)
  - [Connection Classes](#connection-classes)
  - [Core Functions](#core-functions)
  - [Configuration Classes](#configuration-classes)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Dependencies](#dependencies)
- [License](#license)

## Features

- **Multiple Connection Types**: Standard FTP, secure SFTP, and FTP over TLS
- **SSH Key Authentication**: Support for RSA, DSA, ECDSA, and Ed25519 keys
- **Directory Synchronization**: Recursive sync with intelligent filtering
- **PGP Integration**: Automatic encryption/decryption using GnuPG
- **File Filtering**: Regex patterns, age-based filtering, size comparison
- **Timezone Support**: Proper handling of file timestamps across timezones
- **Statistics Tracking**: Monitor copied, decrypted, skipped, and ignored files
- **Context Management**: Safe connection handling with automatic cleanup

## Installation

```bash
pip install git+https://github.com/bissli/libb-ftp.git
```

### Dependencies

- `paramiko` - SSH and SFTP support
- `ftplib` - Standard library FTP protocol handling
- `libb` - Core utilities and configuration management
- `date` - Enhanced date and time handling
- GnuPG - External dependency for PGP operations

## Configuration

### Environment Variables

Set these environment variables for global configuration:

```bash
export CONFIG_GPG_DIR="/path/to/gnupg/config"    # GnuPG configuration directory
export CONFIG_TMPDIR_DIR="/path/to/temp"         # Temporary directory for operations
```

### FtpOptions Configuration

The `FtpOptions` dataclass provides comprehensive configuration:

```python
from ftp.options import FtpOptions

options = FtpOptions(
    # Connection settings
    hostname='sftp.example.com',
    username='user',
    password='password',          # Optional if using SSH keys
    secure=True,                  # Use SFTP instead of FTP
    port=22,                      # Default: 22 for SFTP, 21 for FTP

    # SSH key authentication
    ssh_key_filename='/path/to/private_key',
    ssh_key_type='rsa',           # 'rsa', 'dsa', 'ecdsa', 'ed25519'
    ssh_key_passphrase='key_pass', # Optional

    # Directory settings
    localdir='/local/sync/path',
    remotedir='/remote/path',

    # Sync behavior
    nocopy=False,                 # Dry run mode
    nodecryptlocal=False,         # Skip local decryption
    ignorelocal=False,            # Ignore local file existence
    ignoresize=False,             # Ignore file size comparison
    ignoreolderthan=30,           # Skip files older than N days
    ignore_re=r'\.tmp$',          # Regex to ignore files

    # PGP settings
    pgp_extension='custom_ext',   # Custom PGP extension
)
```

## Quick Start

### Basic Connection

```python
from ftp.client import connect
from ftp.options import FtpOptions

# Standard FTP
options = FtpOptions(
    hostname='ftp.example.com',
    username='user',
    password='password'
)
connection = connect(options)

# List files
files = connection.files()
print(f"Found {len(files)} files")

# Download a file
connection.getbinary('remote_file.txt', '/local/path/file.txt')

connection.close()
```

### Using Context Manager

```python
from ftp.client import connectmanager

with connectmanager(options) as connection:
    # Connection automatically closed when exiting context
    entries = connection.dir(sort=True)
    for entry in entries:
        print(f"{entry.name}: {entry.size} bytes, {entry.datetime}")
```

## Connection Types

### Basic FTP

```python
options = FtpOptions(
    hostname='ftp.example.com',
    username='user',
    password='password',
    secure=False  # Use standard FTP
)
```

### Secure SFTP

```python
options = FtpOptions(
    hostname='sftp.example.com',
    username='user',
    password='password',
    secure=True,  # Use SFTP
    port=22
)
```

### SSH Key Authentication

#### Using Key File

```python
options = FtpOptions(
    hostname='sftp.example.com',
    username='user',
    secure=True,
    ssh_key_filename='/home/user/.ssh/id_rsa',
    ssh_key_type='rsa',
    ssh_key_passphrase='optional_passphrase'
)
```

#### Using Key Content

```python
key_content = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAA...
-----END OPENSSH PRIVATE KEY-----"""

options = FtpOptions(
    hostname='sftp.example.com',
    username='user',
    secure=True,
    ssh_key_content=key_content,
    ssh_key_type='rsa'
)
```

## File Synchronization

### Basic Sync

```python
from ftp.client import sync_site

options = FtpOptions(
    hostname='sftp.example.com',
    username='user',
    secure=True,
    ssh_key_filename='/path/to/key',
    localdir='/local/sync/directory',
    remotedir='/remote/directory'
)

# Synchronize the site
downloaded_files = sync_site(options)
print(f"Downloaded {len(downloaded_files)} files")

# Check statistics
print(f"Copied: {options.stats['copied']}")
print(f"Decrypted: {options.stats['decrypted']}")
print(f"Skipped: {options.stats['skipped']}")
print(f"Ignored: {options.stats['ignored']}")
```

### Advanced Filtering

```python
options = FtpOptions(
    hostname='sftp.example.com',
    username='user',
    secure=True,

    # File filtering
    ignore_re=r'\.(tmp|log|bak)$',     # Ignore temp, log, backup files
    ignoreolderthan=7,                  # Only sync files from last 7 days
    ignoresize=True,                    # Skip size comparison

    # Sync behavior
    nocopy=True,                        # Dry run - don't actually download
    nodecryptlocal=True,                # Don't decrypt downloaded files
)
```

### Sync Options

| Option | Description | Default |
|--------|-------------|---------|
| `nocopy` | Dry run mode - don't download files | `False` |
| `nodecryptlocal` | Skip automatic PGP decryption | `False` |
| `ignorelocal` | Ignore existing local files | `False` |
| `ignoresize` | Skip file size comparison | `False` |
| `ignoreolderthan` | Skip files older than N days | `None` |
| `ignore_re` | Regex pattern for files to ignore | `None` |

## PGP Encryption/Decryption

### Single File Decryption

```python
from ftp.pgp import decrypt_pgp_file

# Decrypt a specific file
decrypt_pgp_file(
    options=options,
    pgpname='encrypted_file.txt.pgp',
    newname='decrypted_file.txt',
    _local=Path('/local/directory')
)
```

### Batch Decryption

```python
from ftp.pgp import decrypt_all_pgp_files

options = FtpOptions(
    localdir='/path/to/encrypted/files',
    ignoreolderthan=30  # Only decrypt files from last 30 days
)

# Decrypt all PGP files in directory tree
decrypted_files = decrypt_all_pgp_files(options)
print(f"Decrypted {len(decrypted_files)} files")
```

## API Reference

### Connection Classes

#### BaseConnection (Abstract)

Base class defining the connection interface:

- `pwd()` - Get current directory
- `cd(path)` - Change directory
- `dir(sort=False)` - List directory contents
- `files()` - Get file names list
- `getascii(remote, local)` - Download text file
- `getbinary(remote, local)` - Download binary file
- `putascii(local, remote)` - Upload text file
- `putbinary(local, remote)` - Upload binary file
- `delete(remote)` - Delete remote file
- `close()` - Close connection

#### FtpConnection

Standard FTP implementation using `ftplib.FTP`.

#### SecureFtpConnection

SFTP implementation using `paramiko` with SSH key support.

### Core Functions

#### connect(options, config=None, **kwargs)

Factory function to create appropriate connection type.

**Parameters:**
- `options`: FtpOptions configuration object
- `config`: Optional config module path
- `**kwargs`: Additional options

**Returns:** Connection object or None

#### connectmanager(options, config=None, **kwargs)

Context manager version of connect with automatic cleanup.

#### sync_site(options, config=None, **kwargs)

Synchronize remote directory with local directory.

**Returns:** List of downloaded file paths

### Configuration Classes

#### FtpOptions

Comprehensive configuration dataclass with all connection and sync options.

#### Entry

NamedTuple representing directory entry:
- `line`: Raw directory listing line
- `name`: File/directory name
- `is_dir`: Boolean indicating if entry is directory
- `size`: File size in bytes
- `datetime`: File modification timestamp

## Error Handling

The library includes robust error handling:

```python
from ftp.client import connect
import paramiko

try:
    connection = connect(options)
    if connection is None:
        print("Failed to establish connection")
        return

except paramiko.AuthenticationException:
    print("Authentication failed - check credentials")
except paramiko.SSHException as e:
    print(f"SSH connection error: {e}")
except OSError as e:
    print(f"Network error: {e}")
```

## Examples

### Complete Sync with Statistics

```python
from ftp.client import sync_site
from ftp.options import FtpOptions
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

options = FtpOptions(
    sitename='vendor_data',
    hostname='sftp.vendor.com',
    username='data_user',
    secure=True,
    ssh_key_filename='/secure/keys/vendor_key',
    localdir='/data/vendor/incoming',
    remotedir='/outgoing',
    ignoreolderthan=14,  # Only sync files from last 2 weeks
    ignore_re=r'\.(tmp|processing)$'
)

try:
    files = sync_site(options)

    print(f"Sync completed for {options.sitename}")
    print(f"Files downloaded: {len(files)}")
    print(f"Statistics:")
    print(f"  Copied: {options.stats['copied']}")
    print(f"  Decrypted: {options.stats['decrypted']}")
    print(f"  Skipped: {options.stats['skipped']}")
    print(f"  Ignored: {options.stats['ignored']}")

    for file_path in files:
        print(f"  Downloaded: {file_path}")

except Exception as e:
    print(f"Sync failed: {e}")
```

### Manual File Operations

```python
from ftp.client import connectmanager
from pathlib import Path

with connectmanager(options) as conn:
    # List remote directory
    entries = conn.dir(sort=True)

    # Filter for CSV files
    csv_files = [e for e in entries if e.name.endswith('.csv')]

    # Download each CSV file
    for entry in csv_files:
        local_path = Path('/data/csv') / entry.name
        local_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Downloading {entry.name} ({entry.size} bytes)")
        conn.getbinary(entry.name, local_path)

        # Set file timestamp to match remote
        import os
        timestamp = entry.datetime.epoch()
        os.utime(local_path, (timestamp, timestamp))
```

### Custom PGP Handling

```python
from ftp.options import FtpOptions
from ftp.pgp import decrypt_pgp_file
from pathlib import Path

# Custom PGP file detection
def custom_is_encrypted(filename):
    return filename.endswith('.encrypted') or '.pgp.' in filename

# Custom PGP file renaming
def custom_rename_pgp(pgpname):
    if pgpname.endswith('.encrypted'):
        return pgpname[:-10]  # Remove .encrypted
    elif '.pgp.' in pgpname:
        return pgpname.replace('.pgp.', '.')
    return pgpname

options = FtpOptions(
    hostname='sftp.example.com',
    username='user',
    secure=True,
    ssh_key_filename='/path/to/key',
    is_encrypted=custom_is_encrypted,
    rename_pgp=custom_rename_pgp
)

# Use in sync operation
files = sync_site(options)
```

## Dependencies

- **Python 3.8+**
- **paramiko** - SSH2 protocol library for secure connections
- **libb** - Core utilities and configuration management
- **date** - Enhanced date/time handling
- **GnuPG** - External binary for PGP operations

Install external dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install gnupg

# macOS
brew install gnupg

# Windows
# Download from https://www.gnupg.org/download/
```

## License

This project is licensed under Open Software License ("OSL") v. 3.0 - see the LICENSE file for details.
