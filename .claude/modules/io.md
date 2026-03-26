# pysdmx.io

**Location**: `src/pysdmx/io/`
**Extras required**: `xml` for XML I/O; `json` for JSON schema validation;
`data` for CSV I/O and Pandas DataFrames.

Provides universal read (`read_sdmx`, `get_datasets`) and write
(`write_sdmx`) functions that dispatch to format-specific implementations.
Format is auto-detected on read; specified via `Format` enum on write.

---

## Entry Points

```python
from pysdmx.io.reader import read_sdmx, get_datasets
from pysdmx.io.writer import write_sdmx
from pysdmx.io.format import Format
```

---

## `read_sdmx()` — Universal Reader

```python
def read_sdmx(
    sdmx_document: Union[str, Path, BytesIO],
    validate: bool = True,
    pem: Optional[Union[str, Path]] = None,
) -> Message:
```

**Arguments**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sdmx_document` | `str`, `Path`, or `BytesIO` | File path, URL, or in-memory bytes |
| `validate` | `bool` | Validate against SDMX schemas (XML/JSON only). Pass `False` to skip. |
| `pem` | `str` or `Path` | PEM file for custom SSL certificate authority (URL fetches only) |

**Returns**: `Message` with one of these populated:
- `msg.structures` — for structure messages (codelists, DSDs, dataflows, …)
- `msg.data` — for data messages (list of `Dataset`)
- `msg.reports` — for reference metadata messages
- `msg.submission` — for registry submission responses

**Format auto-detection**: The function inspects the raw content to determine
the format. No format parameter needed.

**Important**: When `validate=True` (the default):
- XML formats require the `xml` extra
- JSON formats require the `json` extra
- Pass `validate=False` to skip schema validation without these extras

```python
from pysdmx.io.reader import read_sdmx

# Local file
msg = read_sdmx("data/structure.xml")

# Remote URL
msg = read_sdmx("https://ws.sdmx.io/sdmx/v2/structure/codelist/SDMX/CL_FREQ")

# Without validation (no json/xml extra needed)
msg = read_sdmx("structure.json", validate=False)

# BytesIO (e.g. from a REST service response)
msg = read_sdmx(service_response_bytes)

# Navigate the result
codelists = msg.get_codelists()
dsd = msg.get_data_structure_definition("DataStructure=BIS:BIS_CBS(1.0)")
```

Raises `Invalid` if the document is empty or the format cannot be determined.

---

## `get_datasets()` — Data + Structure Reader

```python
def get_datasets(
    data: Union[str, Path, BytesIO],
    structure: Optional[Union[str, Path, BytesIO]] = None,
    validate: bool = True,
    pem: Optional[Union[str, Path]] = None,
) -> Sequence[Dataset]:
```

**Use this instead of `read_sdmx()` when you need**:
- Data validation against the structure
- SDMX-ML Structure-Specific write with custom `DimensionAtObservation`
- VTL script execution

When `structure` is provided, the function:
1. Reads the data message
2. Reads the structure message
3. For each `Dataset`, finds the matching `Schema` and assigns it to
   `dataset.structure`
4. Extracts dataset-level attributes (`attachment_level == "D"`) from data
   columns into `dataset.attributes`

```python
from pysdmx.io.reader import get_datasets

datasets = get_datasets(
    data="data.csv",
    structure="structure.json",
    validate=False,   # skip JSON schema validation
)
for ds in datasets:
    schema = ds.structure     # Schema object
    df = ds.data              # pandas DataFrame (requires data extra)
    attrs = ds.attributes     # dataset-level attributes dict
```

Raises:
- `Invalid` — data message is empty, or structure message contains no structures
- `NotFound` — the structure matching the dataset's reference cannot be found

---

## `write_sdmx()` — Universal Writer

```python
def write_sdmx(
    sdmx_objects: Any,
    sdmx_format: Format,
    output_path: str = "",
    **kwargs: Any,
) -> Optional[str]:
```

**Arguments**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `sdmx_objects` | model object or `Sequence` | Object(s) to serialise |
| `sdmx_format` | `Format` | Target format (see Format enum below) |
| `output_path` | `str` | File path to write; `""` returns a string |

**Keyword arguments** (passed through to format-specific writers):

| kwarg | Formats | Description |
|-------|---------|-------------|
| `prettyprint` | XML, JSON | Pretty-print output (default `True`) |
| `header` | all | Custom `Header` object |
| `dimension_at_observation` | SDMX-ML data | `Dict[str, str]` mapping `{short_urn: dimension_id}` |
| `labels` | CSV | Label style |
| `keys` | CSV | Key columns |
| `time_format` | CSV | Time period format |

**Object type constraints** (raises `Invalid` if violated):

| Format category | Accepted types |
|----------------|----------------|
| Structure formats | `MaintainableArtefact` instances |
| Data formats | `Dataset` instances |
| Reference metadata formats | `MetadataReport` instances |

```python
from pysdmx.io.writer import write_sdmx
from pysdmx.io.format import Format

# Return as string
xml_str = write_sdmx(
    [my_codelist, my_dsd],
    Format.STRUCTURE_SDMX_ML_3_0,
    prettyprint=True,
)

# Write to file
write_sdmx(my_dataset, Format.DATA_SDMX_CSV_2_1_0, output_path="out.csv")

# With custom header
from pysdmx.model import Header
from datetime import datetime, timezone

hdr = Header(id="MSG001", prepared=datetime.now(timezone.utc), sender="BIS")
write_sdmx([my_dsd], Format.STRUCTURE_SDMX_JSON_2_0_0, header=hdr)
```

---

## `Format` Enum — Complete Reference

Import: `from pysdmx.io.format import Format`

### Data formats

| Value | Description | Extra |
|-------|-------------|-------|
| `DATA_SDMX_CSV_1_0_0` | SDMX-CSV 1.0 | `data` |
| `DATA_SDMX_CSV_2_0_0` | SDMX-CSV 2.0 | `data` |
| `DATA_SDMX_CSV_2_1_0` | SDMX-CSV 2.1 | `data` |
| `DATA_SDMX_JSON_1_0_0` | SDMX-JSON data 1.0 | — |
| `DATA_SDMX_JSON_2_0_0` | SDMX-JSON data 2.0 | — |
| `DATA_SDMX_JSON_2_1_0` | SDMX-JSON data 2.1 | — |
| `DATA_SDMX_ML_2_1_GEN` | SDMX-ML 2.1 Generic data | `xml` |
| `DATA_SDMX_ML_2_1_STR` | SDMX-ML 2.1 Structure-Specific data | `xml` |
| `DATA_SDMX_ML_2_1_GENTS` | SDMX-ML 2.1 Generic time series | `xml` |
| `DATA_SDMX_ML_2_1_STRTS` | SDMX-ML 2.1 Str-Specific time series | `xml` |
| `DATA_SDMX_ML_3_0` | SDMX-ML 3.0 data | `xml` |
| `DATA_SDMX_ML_3_1` | SDMX-ML 3.1 data | `xml` |

### Structure formats

| Value | Description | Extra |
|-------|-------------|-------|
| `STRUCTURE_SDMX_JSON_1_0_0` | SDMX-JSON structure 1.0 | — |
| `STRUCTURE_SDMX_JSON_2_0_0` | SDMX-JSON structure 2.0 | — |
| `STRUCTURE_SDMX_JSON_2_1_0` | SDMX-JSON structure 2.1 | — |
| `STRUCTURE_SDMX_ML_2_1` | SDMX-ML 2.1 structure | `xml` |
| `STRUCTURE_SDMX_ML_3_0` | SDMX-ML 3.0 structure | `xml` |
| `STRUCTURE_SDMX_ML_3_1` | SDMX-ML 3.1 structure | `xml` |
| `FUSION_JSON` | Fusion Metadata Registry JSON | — |

### Reference metadata formats

| Value | Description |
|-------|-------------|
| `REFMETA_SDMX_CSV_2_0_0` | SDMX-CSV metadata 2.0 |
| `REFMETA_SDMX_CSV_2_1_0` | SDMX-CSV metadata 2.1 |
| `REFMETA_SDMX_JSON_2_0_0` | SDMX-JSON metadata 2.0 |
| `REFMETA_SDMX_JSON_2_1_0` | SDMX-JSON metadata 2.1 |
| `REFMETA_SDMX_ML_3_0` | SDMX-ML 3.0 metadata |
| `REFMETA_SDMX_ML_3_1` | SDMX-ML 3.1 metadata |

### Registry and schema formats

| Value | Description |
|-------|-------------|
| `REGISTRY_SDMX_ML_2_1` | SDMX-ML 2.1 registry |
| `REGISTRY_SDMX_ML_3_0` | SDMX-ML 3.0 registry |
| `REGISTRY_SDMX_ML_3_1` | SDMX-ML 3.1 registry |
| `SCHEMA_SDMX_JSON_*` | SDMX schema endpoints |
| `SCHEMA_SDMX_ML_*` | SDMX schema endpoints |
| `ERROR_SDMX_ML_2_1` | SDMX-ML 2.1 error message (read-only; auto-raises) |
| `GDS_JSON` | GDS JSON (internal) |

### Format-specific enums (for REST service defaults)

These live in `pysdmx.io.format` and are used by the API query builders:

- `DataFormat` — subset of data `Format` values
- `StructureFormat` — subset of structure `Format` values
- `SchemaFormat` — schema endpoint formats
- `RefMetaFormat` — reference metadata formats
- `AvailabilityFormat` — availability query formats
- `RegistryFormat` — registry submission formats

---

## Read/Write Capability Matrix

| Format category | Read | Write | Notes |
|----------------|------|-------|-------|
| SDMX-CSV 1.0/2.0/2.1 | Data | Data | requires `data` extra |
| SDMX-JSON data 1.0/2.0 | Data | — | read-only |
| SDMX-ML 2.1 Generic | Data | Data | requires `xml` |
| SDMX-ML 2.1/3.0/3.1 Str-Specific | Data | Data | requires `xml` |
| SDMX-ML 2.1/3.0/3.1 Structure | Structure | Structure | requires `xml` |
| SDMX-JSON 2.0/2.1 Structure | Structure | Structure | `json` for validation |
| SDMX-JSON 2.0/2.1 Ref Metadata | RefMeta | RefMeta | `json` for validation |
| SDMX-CSV 2.0/2.1 Ref Metadata | — | RefMeta | |
| SDMX-ML 3.0/3.1 Ref Metadata | — | RefMeta | requires `xml` |
| Fusion JSON | Structure | — | read-only |
| SDMX-ML 2.1 Registry | Submission | — | read-only |
| SDMX-ML 2.1 Error | (raises) | — | auto-converts to `InternalError` |

---

## Internal Sub-packages

| Sub-package | Formats |
|------------|---------|
| `io/csv/sdmx10/` | SDMX-CSV 1.0 reader/writer |
| `io/csv/sdmx20/` | SDMX-CSV 2.0 reader/writer |
| `io/csv/sdmx21/` | SDMX-CSV 2.1 reader/writer |
| `io/json/sdmxjson2/` | SDMX-JSON 2.0/2.1 structure + metadata reader/writer |
| `io/json/fusion/` | Fusion JSON structure reader |
| `io/json/gds/` | GDS JSON reader |
| `io/xml/sdmx21/` | SDMX-ML 2.1 structure + data reader/writer |
| `io/xml/sdmx30/` | SDMX-ML 3.0 data reader |
| `io/xml/sdmx31/` | SDMX-ML 3.1 data reader |

Supporting modules:
- `io/format.py` — `Format` and format-specific enums
- `io/input_processor.py` — normalises raw input (URL fetch, file read, BytesIO)
- `io/serde.py` — `msgspec`-based serialisation helpers
- `io/pd.py` — Pandas `DataFrame` ↔ `Dataset` utilities (requires `data`)

---

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Writing a `Dataset` to a structure format | `Invalid` | Use a data format (`DATA_*`) |
| Writing a `MaintainableArtefact` to a data format | `Invalid` | Use a structure format (`STRUCTURE_*`) |
| Using `validate=True` without `xml`/`json` extra installed | `ImportError` | Pass `validate=False` or install the extra |
| Not using `get_datasets()` for SDMX-ML structure-specific write | Missing schema | Use `get_datasets()` with `structure=` to assign `Schema` |
| Passing `Dataset.structure` as a string when writing SDMX-ML Generic | `Invalid` | Assign a `Schema` object first via `get_datasets()` |
| Expecting `msg.data` to contain `DataFrame` directly | `AttributeError` | Access `dataset.data` per `Dataset` in `msg.data` |
