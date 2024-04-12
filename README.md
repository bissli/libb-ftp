libb-ftp
========

This project provides a set of tools for interacting with FTP servers, including secure connections and file encryption/decryption.

## Features

- Secure FTP connections via `SecureFtpConnection` class.
- Encryption and decryption of files using GnuPG through `decrypt_pgp_file` and `decrypt_all_pgp_files` functions.
- Flexible configuration options provided by `FtpOptions` dataclass.
- Directory synchronization with remote FTP server using `sync_site` function.
- Customizable file handling based on file attributes and patterns.

## Configuration

The configuration is managed through environmental variables and the `FtpOptions` class. The following environmental variables can be set:

- `CONFIG_GPG_DIR`: Directory for GnuPG configuration and keys.
- `CONFIG_TMPDIR_DIR`: Temporary directory for file operations.

## Usage

To use the FTP tools, you need to create an instance of `FtpOptions` with the required connection parameters and then pass it to the `connect`
function to establish a connection with the FTP server.

Example:
```python
from ftp.options import FtpOptions
from ftp.client import connect

options = FtpOptions(hostname='sftp.example.com', username='user', password='pass')
connection = connect(options)
```

For file decryption, you can use the `decrypt_pgp_file` function directly or `decrypt_all_pgp_files` to process multiple files.

## Dependencies

- `paramiko` for SSH and SFTP support.
- `ftplib` for FTP protocol handling.
- `libb` for additional utilities and settings management.
- `date` for date and time handling.

## Installation

To install the required dependencies, use the following command:

```shell
pip install git+https://github.com/bissli/libb-ftp.git
```

Ensure you have the necessary environmental variables set before running the application.

## License

This project is licensed under Open Software License ("OSL") v. 3.0 - see the LICENSE file for details.
