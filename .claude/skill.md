# pysdmx Skill

pysdmx is an opinionated Python library for working with
[SDMX](https://sdmx.io) (Statistical Data and Metadata eXchange) — an ISO
standard used by central banks, statistical agencies, and international
organisations to exchange statistical data and metadata.

- **Version**: 1.12.0
- **License**: Apache 2.0
- **Python**: ≥3.9
- **Package manager**: Poetry 2.0+

---

## Mental Model

pysdmx has three layers. Everything else is support:

```
┌─────────────────────────────────────────┐
│  api/   REST service clients            │  fetch bytes from services
│         query builders                  │
├─────────────────────────────────────────┤
│  io/    read_sdmx() / write_sdmx()      │  bytes ↔ Message / Dataset
├─────────────────────────────────────────┤
│  model/ domain classes (Struct)         │  the primary public API
└─────────────────────────────────────────┘
     toolkit/  Pandas + VTL utilities
     util/     URN parsing + helpers
     errors/   exception hierarchy
```

**Data flow** when reading:
1. `RestService.structure(query)` → `bytes`
2. `read_sdmx(bytes)` → `Message`
3. `msg.get_codelists()`, `msg.get_dataflow(short_urn)`, … → model objects

**Data flow** when writing:
1. Build/modify model objects
2. `write_sdmx(objects, Format.STRUCTURE_SDMX_ML_3_0)` → `str` or file

---

## Module Index

| Module | Reference | Purpose |
|--------|-----------|---------|
| `pysdmx.errors` | [modules/errors.md](modules/errors.md) | Custom exception hierarchy |
| `pysdmx.model` | [modules/model.md](modules/model.md) | SDMX domain model classes (primary public API) |
| `pysdmx.io` | [modules/io.md](modules/io.md) | Read and write SDMX files in all formats |
| `pysdmx.api` | [modules/api.md](modules/api.md) | REST service clients and query builders |
| `pysdmx.toolkit` | [modules/toolkit.md](modules/toolkit.md) | Pandas type mapping and VTL processing |
| `pysdmx.util` | [modules/util.md](modules/util.md) | URN parsing and artefact lookup |

---

## Optional Extras

| Extra | Key packages | Unlocks |
|-------|-------------|---------|
| `data` | pandas, numpy | CSV I/O, DataFrame in `Dataset.data`, `toolkit.pd` |
| `dc` | python-dateutil | Data Collection connector protocol |
| `vtl` | vtlengine, numpy | VTL validation and script generation |
| `json` | sdmxschemas, jsonschema | JSON schema validation (`validate=True`) |
| `xml` | lxml, xmltodict, sdmxschemas | All XML I/O |
| `all` | all of the above | Everything |

```bash
# Development: install all extras
poetry install --extras all

# Production: install only what you need
pip install "pysdmx[xml,data]"
```

---

## Core Conventions

### Frozen model classes

All model classes are `msgspec.Struct(frozen=True)` — **immutable**. Never
assign to fields. To "update" a struct:

```python
import msgspec.structs
updated = msgspec.structs.replace(my_codelist, name="New Name")
```

`Dataset` is the **only** non-frozen model class.

### Type annotations

Use Python 3.9-compatible syntax throughout:

```python
# correct
from typing import Optional, Sequence, Union
field: Optional[str] = None
def fn(x: Union[str, int]) -> Optional[str]: ...

# wrong (Python 3.10+ syntax — rejected by CI)
field: str | None = None
def fn(x: str | int) -> str | None: ...
```

### Error handling

Always raise from `pysdmx.errors`, never bare `Exception`:

```python
from pysdmx.errors import Invalid, NotFound, Unavailable
raise Invalid("title", "longer description with tips", csi={"key": val})
```

Only `Unavailable` is retriable. See [modules/errors.md](modules/errors.md).

### Docstrings

Google-style, required on every public symbol:

```python
def my_func(arg: str) -> int:
    """One-line summary.

    Args:
        arg: Description.

    Returns:
        Description.

    Raises:
        Invalid: When arg is empty.
    """
```

### Line length

Hard limit 79 characters. Ruff handles formatting.

---

## Most Common Workflows

### Read a local or remote SDMX file

```python
from pysdmx.io.reader import read_sdmx

msg = read_sdmx("path/to/structure.xml")          # local file
msg = read_sdmx("https://example.org/sdmx/...")   # remote URL
msg = read_sdmx(my_bytes_io_object)               # BytesIO

# Navigate structures
codelists = msg.get_codelists()
dsd = msg.get_data_structure_definition(
    "DataStructure=BIS:BIS_CBS(1.0)"
)
```

Format is auto-detected. No format parameter needed.

### Read data with a structure

```python
from pysdmx.io.reader import get_datasets

datasets = get_datasets(
    data="data.csv",
    structure="structure.json",  # optional but needed for validation/VTL
)
for ds in datasets:
    print(ds.structure.short_urn)
    df = ds.data  # pandas DataFrame (requires data extra)
```

### Query a SDMX-REST service

```python
from pysdmx.api.qb.service import RestService
from pysdmx.api.qb.util import ApiVersion
from pysdmx.api.qb.structure import StructureQuery, StructureType
from pysdmx.io.reader import read_sdmx

svc = RestService(
    api_endpoint="https://sdmx.example.org/rest",
    api_version=ApiVersion.V2_0_0,
)
query = StructureQuery(
    artefact_type=StructureType.CODELIST,
    agency_id="BIS",
    resource_id="CL_FREQ",
)
msg = read_sdmx(svc.structure(query))
cl = msg.get_codelist("Codelist=BIS:CL_FREQ(1.0)")
```

### Write SDMX objects to a file

```python
from pysdmx.io.writer import write_sdmx
from pysdmx.io.format import Format

# Returns string
xml_str = write_sdmx([my_codelist, my_dsd], Format.STRUCTURE_SDMX_ML_3_0)

# Writes to file
write_sdmx(my_dataset, Format.DATA_SDMX_CSV_2_1_0, output_path="out.csv")
```

### Parse a URN

```python
from pysdmx.util import parse_urn, find_by_urn

ref = parse_urn("Codelist=BIS:CL_FREQ(1.0)")
print(ref.agency, ref.id, ref.version)  # BIS CL_FREQ 1.0

cl = find_by_urn(msg.structures, "Codelist=BIS:CL_FREQ(1.0)")
```

---

## Development Quality Checks

Run in this order before every commit:

```bash
poetry run ruff format --no-cache
poetry run ruff check --fix
poetry run mypy --show-error-codes --pretty
poetry run pytest --cov=pysdmx --cov-branch --cov-report=term-missing \
    --verbose --tb=short --strict-markers tests/
```

100% branch coverage is enforced in CI.
