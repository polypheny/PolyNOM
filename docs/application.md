---
layout: page
title: "Application"
toc: true
docs_area: "PolyNOM"
tags: application, connection, schema
lang: en
---

## Application

The `Application` class represents an individual application that interacts with a Polypheny instance to read and write data.
An `Application`:

- Operates on a single Polypheny `Instance`
- Manages one or more `Session` objects
- Provides authentication and configuration settings for the connection
- Handles optional Docker lifecycle management for isolated environments
- Can optionally trigger model migration (e.g., schema updates)

## Initialization Parameters
```python
Application(
    app_uuid: str,
    address,
    user: str = 'pa',
    password: str = '',
    transport: str = 'plain',
    use_docker: bool = True,
    migrate: bool = False,
    stop_container: bool = False,
    remove_container: bool = False
)
```

- `app_uuid` (`str`, required):  
  A unique identifier for the application. This identifier should be persitent across restarts and reboots and uniquely represent the product the application to be instantiated is used in. 

- `address`:  
  Besides TCP/IP Polypheny supports advanced transport methods such as unix sockets. This parameter specifies an adress matching the specified transport method. For TCP/IP the adress is a host, port tuple. For unix sockets this is a unix socket path specification.

- `user` (`str`, optional):  
  Username for authentication on the Polypheny instance. If not specified the default username 'pa' available on all polypheny deployments is used.

- `password` (`str`, optional):  
  Password for authentication on the Polpyheny instance. If not specified the password of the default user is used. This is the empty string.

- `transport` (`str`, optional):  
  Transport method to be used to communicate with the Polypheny instance. As of now 'plain' and 'unix' are available were 'plain' refers to TCP/IP.

- `use_docker` (`bool`, optional):  
  Wether to use Docker to manage the Polypheny instance. When set to 'True' PolyNOM searches for a Docker container running a Polypheny instance. If no container is found, a new one is created on which Polypheny is deployed automatically. If a container is present but stopped, the container will be started. If not specified, this defaults to 'True'. The container running Polypheny must be named 'polypheny'. 

- `migrate` (`bool`, optional):  
  Wether to trigger automatic schema migration. If enabled, PolyNOM automatically compares the schema of the application with the one currently present on the Polypheny instance. Adjustments to the schmea are then made on instantiation of this application object. Defaults to `False`.

- `stop_container` (`bool`, optional):  
  If `True`, stops the Docker container running the Polypheny instance when the application context ends. Defaults to `False`.

- `remove_container` (`bool`, optional):  
  If `True`, removes the Docker container running the Polypheny instance after stopping. Defaults to `False`.

## Examples
```python
from polynom.application import Application

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

# Create an application connected to a Polypheny Docker container. If absent, the container as well as Polypheny will be automatically deployed.

app = Application(APP_UUID, ('localhost', 20590))
with app:
   # do something

# Equivalent to the one above.

with Application(APP_UUID, ('localhost', 20590)) as app:
   # do something

# Create an application connected to a Polypheny instance running on localhost. As this instance is externally managed, the Docker features are disabled.

app = Application(APP_UUID, ('localhost', 20590), use_docker=False)
with app:
   # do something

# Use a specific username and password for authorization on the Polypheny instance.

app = Application(APP_UUID, ('localhost', 20590), user='admin', password='admin')
with app:
   # do something
```

Apart from the initialization the `Application` does not provide any functions or methods ot be called by the user.