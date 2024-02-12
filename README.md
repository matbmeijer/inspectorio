# Inspectorio API wrapper <img src="https://developers.inspectorio.com/img/logo.svg" align="right" height=15/>
[![CI/CD workflow](https://github.com/matbmeijer/inspectorio/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/matbmeijer/inspectorio/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![Python 3.8](https://img.shields.io/badge/python-3.8-blue)
![Python 3.9](https://img.shields.io/badge/python-3.9-blue)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)

The **Inspectorio API Wrapper** is an unofficial Python library designed to simplify interactions with the [Inspectorio API](https://developers.inspectorio.com). It provides an asynchronous interface to access Inspectorio's platform, offering features that streamline the process of integrating Inspectorio's capabilities into your Python applications.

## Features

- **Asynchronous Requests:** Leverage Python's async/await syntax to perform non-blocking API calls, enabling faster data retrieval and improved efficiency in I/O bound applications.
- **Automatic Pagination Handling:** Effortlessly manage API pagination with built-in methods to fetch all relevant data without manually handling page tokens or limits.
- **Swagger Documentation Support:** Directly based on [Inspectorio's Swagger documentation](https://sight.inspectorio.com/swagger/), ensuring comprehensive coverage of API endpoints and parameters.
- **Secure Authentication:** Simplified and secure handling of authentication tokens, abstracting the complexity of token management and headers.
- **Error Handling:** Provides structured error handling mechanisms, making it easier to debug issues related to API requests.

## Documentation

For detailed information about the library's API, including classes, methods, and usage examples, please refer to the [official documentation](https://matbmeijer.github.io/inspectorio/inspectorio.html) of the Python library.

## Installation

You can install **inspectorio** directly from the [Python Package Index (PyPI)](https://pypi.org/project/inspectorio/) following this `pip`
command:

``` bash
pip install inspectorio
```

## Code of Conduct

Please note that the **inspectorio** project is released with a [Contributor
Code of
Conduct](https://github.com/matbmeijer/inspectorio/blob/main/CODE_OF_CONDUCT.md).
By contributing to this project, you agree to abide by its terms.

## License

[MIT © Matthias
Brenninkmeijer](https://github.com/matbmeijer/inspectorio/blob/main/LICENSE)
