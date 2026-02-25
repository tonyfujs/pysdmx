# CLAUDE.md — pysdmx Codebase Guide

This file provides AI assistants with a comprehensive overview of the `pysdmx`
repository: its purpose, structure, conventions, and development workflows.

---

## Project Overview

**pysdmx** is an opinionated Python library for working with
[SDMX](https://sdmx.io) (Statistical Data and Metadata eXchange) — an ISO
standard used by central banks, statistical agencies, and international
organisations to exchange statistical data and metadata.

- **Version**: 1.12.0
- **License**: Apache 2.0
- **Python**: ≥3.9
- **Package manager**: Poetry 2.0+
- **Source layout**: `src/` layout (PEP 517)
- **Repository**: https://github.com/bis-med-it/pysdmx
- **Docs**: https://bis-med-it.github.io/pysdmx

### What the library does

- Provides immutable Python dataclasses (via `msgspec.Struct`) that model
  SDMX artefacts (codelists, concepts, dataflows, data structures, etc.)
- Reads and writes SDMX files in CSV (1.0/2.0/2.1), JSON (SDMX-JSON 2.0/2.1,
  Fusion JSON), and XML (SDMX-ML 2.1/3.0/3.1) formats
- Provides synchronous and asynchronous SDMX-REST API clients
- Integrates with pandas and supports VTL (Validation and Transformation
  Language) processing

---

## Repository Layout

```
pysdmx/
├── src/pysdmx/          # Main package source
│   ├── __init__.py      # Package version
│   ├── errors.py        # Custom exception hierarchy
│   ├── model/           # SDMX domain model classes
│   ├── io/              # Format readers and writers
│   ├── api/             # SDMX-REST service clients
│   ├── toolkit/         # Pandas/VTL utilities
│   └── util/            # Internal helpers
├── tests/               # pytest test suite (~370 files)
├── docs/                # Sphinx documentation
│   └── dev_checks.md    # Development command reference
├── .github/workflows/   # GitHub Actions CI/CD
├── pyproject.toml       # Project metadata, tool config
├── pytest.ini           # pytest settings
├── poetry.toml          # Poetry local venv config
├── poetry.lock          # Locked dependency tree
├── README.rst           # Project overview
└── CHANGELOG.rst        # Version history
```

---

## Source Code Structure (`src/pysdmx/`)

### `model/` — SDMX information model

All domain classes. These are the primary public API of the library.

| File | Key classes |
|------|-------------|
| `__base.py` | `Annotation`, `AnnotableArtefact`, `IdentifiableArtefact`, `MaintainableArtefact` |
| `code.py` | `Code`, `Codelist`, `Hierarchy`, `HierarchicalCode` |
| `concept.py` | `Concept`, `ConceptScheme`, `DataType` (enum) |
| `category.py` | `Category`, `CategoryScheme`, `Categorisation` |
| `dataflow.py` | `Dataflow`, `DataStructureDefinition`, `Component`, `Schema` |
| `constraint.py` | Data constraint artefacts |
| `map.py` | Mapping/crosswalk structures |
| `metadata.py` | Reference metadata structures |
| `organisation.py` | `Agency`, `DataProvider`, `DataConsumer`, scheme classes |
| `vtl.py` | VTL transformation mappings |
| `message.py` | Message envelope structures |
| `dataset.py` | `Dataset`, `SeriesInfo` |
| `gds.py` | Global Discovery Service structures |
| `submission.py` | `SubmissionResult` |

### `io/` — Format I/O

- `reader.py` — `read_sdmx()` entry point; dispatches to format-specific readers
- `writer.py` — `write_sdmx()` entry point
- `format.py` — `Format` enum and format detection
- `input_processor.py` — Pre-processes raw input (bytes, str, path)
- `serde.py` — msgspec-based serialisation helpers
- `pd.py` — Pandas DataFrame ↔ Dataset conversion
- `csv/` — SDMX-CSV (sdmx10, sdmx20, sdmx21 sub-packages)
- `json/` — SDMX-JSON (fusion, sdmxjson2 sub-packages; GDS)
- `xml/` — SDMX-ML (sdmx21, sdmx30, sdmx31 sub-packages)

### `api/` — REST clients

- `qb/` — Query Builder:
  - `service.py` — `RestService`, `AsyncRestService`
  - `data.py` — `DataQuery`, `DataFormat`
  - `structure.py` — `StructureQuery`, `StructureFormat`
  - `schema.py` — `SchemaQuery`, `SchemaFormat`
  - `availability.py`, `registration.py`, `refmeta.py`, `gds.py`
- `fmr/` — Fusion Metadata Registry integration
- `gds/` — Global Discovery Service integration
- `dc/` — Data Collection queries (requires `dc` extra)
  - `query/` — `_sql_parser.py`, `_py_parser.py`, `_model.py`

### `toolkit/` — Higher-level utilities

- `pd/` — Pandas integration utilities
- `vtl/` — VTL support (requires `vtl` extra):
  - `validation.py`, `script_generation.py`, `convert.py`

### `util/` — Internal helpers

- `__init__.py` — Core utilities
- `_model_utils.py` — Model helpers (private)
- `_net_utils.py` — HTTP/network helpers (private)
- `_date_pattern_map.py` — Date pattern lookup (private)

---

## Key Conventions

### Model classes use `msgspec.Struct`

All domain model classes inherit from `msgspec.Struct` with these flags:

```python
class MyArtefact(
    Struct, frozen=True, omit_defaults=True, repr_omit_defaults=True
):
    """One-line summary.

    Longer description.

    Attributes:
        field_name: Description.
    """

    field_name: Optional[str] = None
```

- **`frozen=True`** — instances are immutable; never add mutation logic
- **`omit_defaults=True`** — serialisation skips fields with default values
- **`kw_only=True`** used on classes with many optional fields
- Validation in `__post_init__`; raise `Invalid` (from `pysdmx.errors`)
- Custom `__str__` and `__repr__` that omit empty sequences

### Type annotations are mandatory and strict

MyPy is run in **strict mode**. Every function, method, and class attribute
must be fully typed. Common patterns:

```python
from typing import Any, Dict, Optional, Sequence, Union
```

- Prefer `Sequence[T]` over `List[T]` for read-only collections
- Prefer `Optional[T]` over `T | None` for compatibility with Python 3.9
- Use `Union[A, B]` rather than `A | B` for the same reason
- Never use bare `dict` or `list` — always parameterise
- Do not use `Any` unless there is no alternative, and document why

### Docstrings follow Google style

Enforced by Ruff rule `D` with `pydocstyle.convention = "google"`:

```python
def my_function(arg: str) -> int:
    """Short one-line summary.

    Longer description if needed.

    Args:
        arg: Description of arg.

    Returns:
        Description of return value.

    Raises:
        Invalid: When arg is empty.
    """
```

- Every public class, method, function, and module must have a docstring
- Tests are exempt from most docstring rules (`D100`, `D103`, `D104`)

### Error handling

Use the custom error hierarchy from `pysdmx.errors`:

```python
from pysdmx.errors import Invalid, NotFound, InternalError, Unauthorized

raise Invalid(
    "Short title",
    "Detailed human-readable description with tips.",
    csi={"context_key": "context_value"},  # optional
)
```

| Error class | Use case |
|-------------|----------|
| `Invalid` | Bad input; non-retriable |
| `NotFound` | Resource does not exist; non-retriable |
| `InternalError` | Valid request, cannot be fulfilled; non-retriable |
| `NotImplemented` | Operation not supported; non-retriable |
| `Unauthorized` | Auth failure; non-retriable |
| `Unavailable` | Service temporarily unavailable; **retriable** |
| `RetriableError` | Base for retriable errors; prefer `Unavailable` |

### Module naming

- Private modules and helpers: prefix with `_` (e.g., `_model_utils.py`)
- Public exports defined in `__init__.py` via `__all__`
- Format-specific code lives in a dedicated sub-package
  (e.g., `io/xml/sdmx21/`)

### Async support

- Every synchronous REST client class has an `Async` counterpart
  (e.g., `RestService` / `AsyncRestService`)
- Use `httpx` (with HTTP/2) for all network I/O
- Write async tests with `pytest-asyncio`

### Line length and formatting

- Hard limit: **79 characters** (Ruff / PEP 8)
- Ruff handles both formatting and linting; do not use Black separately

---

## Optional Dependencies (extras)

The library has an intentionally minimal core. Heavy dependencies are optional:

| Extra | Packages | Unlocks |
|-------|----------|---------|
| `data` | pandas, numpy | DataFrame integration, CSV I/O |
| `dc` | python-dateutil | Data Collection queries |
| `vtl` | vtlengine, numpy | VTL validation and processing |
| `json` | sdmxschemas, jsonschema | JSON schema validation |
| `xml` | lxml, xmltodict, sdmxschemas | XML I/O |
| `all` | All of the above | Everything |

Install locally for full development: `poetry install --extras all`

---

## Development Workflow

### Setup

```bash
# Install Poetry 2.0+ first
pip install poetry

# Install all dependencies (including dev and all extras)
poetry install --extras all

# Activate virtual environment
poetry shell
```

### Quality checks (run in this order before every commit)

```bash
# 1. Format code
poetry run ruff format --no-cache

# 2. Lint (auto-fix safe issues)
poetry run ruff check --fix

# 3. Type-check (must have zero errors)
poetry run mypy --show-error-codes --pretty

# 4. Run tests with coverage
poetry run pytest --cov=pysdmx --cov-branch --cov-report=term-missing --verbose --tb=short --strict-markers --strict-config --durations=10 tests/

# 5. Generate HTML coverage report and verify 100%
coverage html
```

All five steps are enforced in CI. **Code will not merge if any step fails.**

### Running specific test subsets

Tests are grouped by the optional extras they require. Use `-m` marker flags:

```bash
# Only model tests (no extras needed)
poetry run pytest -m noextra tests/

# Only XML tests
poetry run pytest -m xml tests/

# Only CSV/data tests
poetry run pytest -m data tests/

# Only JSON tests
poetry run pytest -m json tests/

# Only VTL tests
poetry run pytest -m vtl tests/

# Only data-collection tests
poetry run pytest -m dc tests/
```

`conftest.py` automatically applies markers based on file path; you do not
need to decorate individual test functions.

---

## Testing Conventions

- **Framework**: pytest + pytest-asyncio
- **HTTP mocking**: `respx` (never make real network calls in tests)
- **Coverage requirement**: 100% branch coverage (enforced with
  `--fail-under=100`). Every new code path needs a corresponding test.
- **Fixtures**: defined in `conftest.py` or at test-file level
- **Test file naming**: `test_<thing>.py` matching the module under test
- **No docstrings required** in test files (relaxed by Ruff per-file ignores)
- **Assertions**: use plain `assert`; avoid `unittest` style
- `__extras_check.py` is excluded from coverage (cannot be tested with all
  extras installed)

---

## CI/CD Pipelines (`.github/workflows/`)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR to `develop`/`main` | Ruff, MyPy, pytest on Ubuntu+Windows+macOS × Python 3.9–3.13 |
| `cd.yml` | Release published / manual | Build and publish to PyPI |
| `sphinx.yml` | Push to `main` / manual | Build and deploy Sphinx docs to GitHub Pages |

CI matrix uses `fail-fast: false` so all platform/version combinations always
run to completion.

---

## Adding New Features — Checklist

1. **Model changes**: add/modify classes in `src/pysdmx/model/`; keep all
   classes frozen `msgspec.Struct` with full type annotations and Google
   docstrings.
2. **I/O changes**: implement in the appropriate sub-package under
   `src/pysdmx/io/`; register new formats in `format.py`.
3. **API changes**: extend `qb/` query builders or `fmr/`/`gds/` clients.
4. **Exports**: update the relevant `__init__.py` and `__all__` list.
5. **Tests**: add tests achieving 100% branch coverage for all new code.
6. **Docs**: update or add docstrings; update `docs/` if user-facing behaviour
   changed.
7. **Run all quality checks** (see Development Workflow above).
8. **No commented-out code** — the `ERA` Ruff rule will reject it.

---

## Common Pitfalls

- **Mutating frozen structs**: `msgspec.Struct` with `frozen=True` will raise
  `TypeError` on attribute assignment. To "update" a struct, use
  `msgspec.structs.replace(obj, field=new_value)`.
- **Missing type annotations**: MyPy strict mode rejects any untyped
  definition. Always annotate, even trivial helpers.
- **Bare exceptions**: Ruff `B` rules reject `except Exception:` without
  re-raise or logging. Catch specific errors.
- **Security issues**: Ruff `S` (bandit) rules are enabled for source code.
  Avoid `subprocess`, `eval`, `exec`, hard-coded credentials.
- **Complexity**: McCabe complexity limit is 10. Refactor functions that exceed
  it into smaller helpers.
- **Commented-out code**: Ruff `ERA` rule rejects commented-out code. Remove
  it entirely.

---

## Key Entry Points

| Symbol | Location | Description |
|--------|----------|-------------|
| `read_sdmx()` | `src/pysdmx/io/reader.py` | Parse any SDMX file |
| `write_sdmx()` | `src/pysdmx/io/writer.py` | Serialise to any SDMX format |
| `RestService` | `src/pysdmx/api/qb/service.py` | Sync SDMX-REST client |
| `AsyncRestService` | `src/pysdmx/api/qb/service.py` | Async SDMX-REST client |
| All model classes | `src/pysdmx/model/__init__.py` | 200+ exported model classes |
| Error classes | `src/pysdmx/errors.py` | Custom exception hierarchy |
