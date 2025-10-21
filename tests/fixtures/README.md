# Test Configuration Helpers

This module provides utilities for temporarily modifying configuration during tests.

## Usage Patterns

### 1. Context Manager (Recommended)

Use the `temporary_config()` context manager or type-specific fixtures:

```python
from tests.fixtures.config_helpers import temporary_config

def test_something(sftp_config):
    # Using sftp_config fixture
    with sftp_config(allow_agent=False, password='test'):
        # Config is modified here
        assert something
    # Config is automatically restored

def test_something_else():
    # Using temporary_config directly
    with temporary_config('vendor.FOO.sftp', port=2223):
        # Config is modified here
        assert something
    # Config is automatically restored
```

### 2. Decorator Pattern

Use the `@with_temporary_config` decorator:

```python
from tests.fixtures.config_helpers import with_temporary_config

@with_temporary_config('vendor.FOO.sftp', allow_agent=False)
def test_something():
    # Config is modified for entire function
    assert something
```

### 3. Fixture Pattern

Use existing fixtures for common scenarios:

```python
def test_with_ssh_key_file(configure_sftp_ssh_key_file):
    # SFTP automatically configured with SSH key file
    assert something

def test_with_ssh_key_content(configure_sftp_ssh_key_content):
    # SFTP automatically configured with SSH key content
    assert something
```

## Available Fixtures

### Generic Config Modifiers

- `sftp_config`: Returns context manager for SFTP config (`vendor.FOO.sftp`)
- `ftp_config`: Returns context manager for FTP config (`vendor.FOO.ftp`)

### Specialized Fixtures

- `configure_sftp_ssh_key_file`: Configures SFTP with SSH key file auth
- `configure_sftp_ssh_key_content`: Configures SFTP with SSH key content auth
