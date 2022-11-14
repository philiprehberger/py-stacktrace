# philiprehberger-stacktrace

[![Tests](https://github.com/philiprehberger/py-stacktrace/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-stacktrace/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-stacktrace.svg)](https://pypi.org/project/philiprehberger-stacktrace/)
[![License](https://img.shields.io/github/license/philiprehberger/py-stacktrace)](LICENSE)

Turn Python stack traces into cleaner, more readable output.

## Installation

```bash
pip install philiprehberger-stacktrace
```

## Usage

### Global Install

```python
from philiprehberger_stacktrace import install

install()  # replaces sys.excepthook
```

### Manual Formatting

```python
from philiprehberger_stacktrace import format_exception

try:
    risky_operation()
except Exception as e:
    report = format_exception(e)
    print(report.short())     # one-line summary
    print(report.detailed())  # colored with source context
```

## API

| Function / Class | Description |
|------------------|-------------|
| `install(color=True, context=2, hide_stdlib=True)` | Replace `sys.excepthook` |
| `format_exception(exc)` | Returns `ExceptionReport` |
| `report.short()` | One-line summary |
| `report.detailed(color, context, hide_stdlib)` | Full formatted output |


## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
