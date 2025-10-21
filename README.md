# Earthlings on Mars Foundation

[![PyPI - Version](https://img.shields.io/pypi/v/earthlings-on-mars-foundation.svg)](https://pypi.org/project/earthlings-on-mars-foundation)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/earthlings-on-mars-foundation.svg)](https://pypi.org/project/earthlings-on-mars-foundation)

______________________________________________________________________

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install earthlings-on-mars-foundation
```

## Run Locally

```shell
nix develop --command $SHELL
cd src/earthlings_on_mars_foundation
./manage.py migrate
DEBUG=true ./manage.py runserver
```

## License

`earthlings-on-mars-foundation` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
