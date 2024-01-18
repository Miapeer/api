# Miapeer API
This is the Miapeer API.

Check out the front-end [here](https://github.com/Miapeer).

## Table of Contents
- [User Permission list](#user-permission-list)
- [License](#license)
- [Installation](#installation)
- [Copyright](#copyright-notice)

## User Permission list
### Miapeer
#### Unauthenticated
Can access the home page in order to register or log in

#### User
Can access their applications

#### Admin
Can create users
Can assign applications to users

#### Super User
Can create applications

### Quantum
#### Unauthenticated
No access - Sign in first

#### User
Can access their associated portfolios

#### Admin
Can add users to their portfolios

#### Super User
Can add admins to their portfolios


## License
No license is currently offered

## Installation
If error on Mac:
```
Building wheels for collected packages: pyodbc
  Building wheel for pyodbc (setup.py) ... error
  error: subprocess-exited-with-error

  × python setup.py bdist_wheel did not run successfully.
  │ exit code: 1
...
```
Explanation: https://stackoverflow.com/questions/72142381/unable-to-pip-install-pyodbc-on-mac
- `brew install unixodbc`
- `export LDFLAGS="-L/opt/homebrew/Cellar/unixodbc/[your version]/lib"`
- `export CPPFLAGS="-I/opt/homebrew/Cellar/unixodbc/[your version]/include"`
- `task install-local`

## Copyright Notice
Copyright © 2023 Miapeer LLC

All rights reserved. This [software/product/content] is the property of Miapeer LLC and is protected by copyright and other intellectual property laws. You may not reproduce, distribute, or create derivative works without explicit written consent from Miapeer LLC.

For inquiries, please contact [Jeff Navarra](mailto:jeff.navarra@miapeer.com).
