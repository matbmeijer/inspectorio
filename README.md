# Inspectorio API wrapper <img src="https://developers.inspectorio.com/img/logo.svg" align="right" height=15/>
[![CI/CD workflow](https://github.com/matbmeijer/inspectorio/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/matbmeijer/inspectorio/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
![Python 3.8](https://img.shields.io/badge/python-3.8-blue)
![Python 3.9](https://img.shields.io/badge/python-3.9-blue)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)

The **Inspectorio API Wrapper** is an unofficial Python library designed to facilitate interactions with the [Inspectorio API](https://developers.inspectorio.com). This library offers a flexible interface supporting both synchronous and asynchronous operations to access *Inspectorio's* platform, making it easier to integrate *Inspectorio's* functionalities into your Python applications.

## Features

- **Synchronous and Asynchronous Requests:** Provides the flexibility to use Python's traditional synchronous or the async/await syntax for non-blocking API calls. This feature enables faster data retrieval, improved efficiency in I/O bound applications, and compatibility with various programming paradigms.
- **Automatic Pagination Handling:** Effortlessly manage API pagination with built-in methods to fetch all relevant data without manually handling page tokens or limits.
- **Swagger Documentation Support:** Directly based on [Inspectorio's Swagger documentation](https://sight.inspectorio.com/swagger/), ensuring comprehensive coverage of API endpoints and parameters.
- **Secure Authentication:** Simplified and secure handling of authentication tokens, abstracting the complexity of token management and headers.
- **Error Handling:** Provides structured error handling mechanisms, making it easier to debug issues related to API requests.

## Documentation

For detailed information about the library's API, including classes, methods, and usage examples, please refer to the [official documentation](https://matbmeijer.github.io/inspectorio/inspectorio.html) of the Python library.

## Installation

You can install **inspectorio** directly from the [Python Package Index (PyPI)](https://pypi.org/project/inspectorio/) following this `pip`
command:

```bash
pip install inspectorio
```

## Usage
The Inspectorio API Wrapper supports both synchronous and asynchronous interactions with the Inspectorio API. Here's how to get started with both:

### Synchronous Usage
For traditional blocking requests, you can use the InspectorioSight class. Here's a quick example to authenticate and list all reports:

```python
from inspectorio.sight import InspectorioSight

# Initialize the InspectorioSight
app = InspectorioSight()

# Login with your credentials
username = "username@mail.com"
password = "__password__"
app.login(username=username, password=password)

# Fetch and list all reports, the method deals with pagination
result = app.list_all_reports()
```

### Asynchronous Usage
If your application requires non-blocking calls, replace `InspectorioSight` with `AsyncInspectorioSight`. This class offers the same functionalities but operates asynchronously:
```python
from inspectorio.sight import AsyncInspectorioSight

# For asynchronous operations, use the AsyncInspectorioSight class
# Initialization and usage are similar to the synchronous version but with async/await syntax
async def main():
    app = AsyncInspectorioSight()
    await app.login(username="username@mail.com", password="__password__")
    result = await app.list_all_reports()

# Remember to run your async function in an event loop
```

Both examples demonstrate how to authenticate and retrieve data from the Inspectorio API. Choose the approach that best fits your application's architecture.

## Code of Conduct

Please note that the **inspectorio** project is released with a [Contributor
Code of
Conduct](https://github.com/matbmeijer/inspectorio/blob/main/CODE_OF_CONDUCT.md).
By contributing to this project, you agree to abide by its terms.

## License

[MIT © Matthias
Brenninkmeijer](https://github.com/matbmeijer/inspectorio/blob/main/LICENSE)
