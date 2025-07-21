---
layout: page
title: "Configuration"
toc: true
docs_area: "PolyNOM"
tags: configuration, settings, constants
lang: en
---

## Configuration

The `config` module manages all configurable options used by PolyNOM. It distinguishes between three types of values:

- **Internal constants** – Fixed values that cannot be modified by users but are accessible for reading.
- **User-configurable parameters** – Values that users can freely read and update to customize behavior.
- **Derived values** – Read-only values automatically computed from internal constants and user-configurable parameters. These are kept up to date whenever related user-configurable values change.

All values are managed as key value pairs. Methods are provided allowing to set and get values based on their keys. The keys themselves are provided as constants by the config.py. The config should only be modified if no application is active. Ignoring this might cause data corruption.
In the following the metods and keys available are discussed.

## Mathods

### `get(key: str) -> Any`

Retrieves the current value of a configuration parameter.

- Raises `KeyError` if the key is unknown.
- Accepts only defined key constants.

---

### `set(key: str, value: Any)`

Updates the value of a user-configurable parameter.

- Raises `KeyError` if the key is not user-configurable.
- Raises `RuntimeError` if an application is active.
- Automatically updates derived values.

---

### `set_config(config_dict: dict)`

Bulk-update configuration with a dictionary of key–value pairs.

- Only applies updates to keys that are user-configurable.
- Raises `RuntimeError` if the key is unknown.
- Useful for initializing from external sources or dynamic input.

---

### `all_config() -> dict`

Returns a merged view of all current configuration values, including internal constants, user-configurable values, and derived values. Intended for debugging and inspection only.

---

## Configuration Keys

Each configuration key is available as a named constant (e.g., `cfg.DEFAULT_USER`) for safe and readable use in your code.

### Internal Constants (Read-only)

- `INTERNAL_NAMESPACE`: `"internal"`  
  Namespace reserved for system-level metadata and tracking.

- `CHANGE_LOG_TABLE`: `"change_log"`  
  Name of the internal table that records data changes.

- `SYSTEM_USER_NAME`: `"SYSTEM"`  
  Reserved name for system-level actions in change logs.

- `SNAPSHOT_TABLE`: `"snapshot"`  
  Table used to store snapshots of schema and mapping metadata.

### User Configurable Keys

- `DEFAULT_NAMESPACE`:  
  Default namespace used for schema deployment. Default: `'public'`

- `POLYPHENY_CONTAINER_NAME`:  
  Name of the Docker container running Polypheny. Default: `'polypheny'`

- `POLYPHENY_IMAGE_NAME`:  
  Docker image name used to run Polypheny. Default: `'polypheny/polypheny'`

- `POLYPHENY_PORTS`:  
  Dictionary mapping exposed ports for Polypheny services. Default:
  ```python
  {
      "20590/tcp": 20590,
      "7659/tcp": 7659,
      "80/tcp": 80,
      "8081/tcp": 8081,
      "8082/tcp": 8082
  }
  ```

- `DEFAULT_TRANSPORT`:  
  Communication method with Polypheny. Default: `'plain'`

- `DEFAULT_USER`:  
  Username used for default authentication. Default: `'pa'`

- `DEFAULT_PASS`:  
  Password used for default authentication. Default: `''` (empty string)

### Derived Configuration

- `CHANGE_LOG_IDENTIFIER`:  
  Computed identifier combining `INTERNAL_NAMESPACE` and `CHANGE_LOG_TABLE`. Default: `'internal.change_log'`


## Example

```python
import config as cfg

# Retrieve a user setting
username = cfg.get(cfg.DEFAULT_USER)

# Set or override a value
cfg.set(cfg.DEFAULT_NAMESPACE, 'analytics')

# Apply a batch of settings
cfg.set_config({
    cfg.DEFAULT_USER: 'admin',
    cfg.DEFAULT_PASS: 'secret',
    cfg.DEFAULT_NAMESPACE: 'prod_ns'
})

# Get an internal or derived value
log_table = cfg.get(cfg.CHANGE_LOG_IDENTIFIER)

# Print all current values for debugging
print(cfg.all_config())
```

You should **always access keys using the predefined constants** in the `config` module (e.g., `cfg.DEFAULT_USER`) rather than string literals. This ensures forward compatibility and avoids accidental typos.