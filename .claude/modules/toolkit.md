# pysdmx.toolkit

**Location**: `src/pysdmx/toolkit/`

Higher-level utilities built on top of the model and I/O layers. Two
sub-packages:

- `pysdmx.toolkit.pd` — Pandas type mapping (requires `data` extra)
- `pysdmx.toolkit.vtl` — VTL validation and transformation (requires `vtl` extra)

---

## Pandas Toolkit (`pysdmx.toolkit.pd`)

**Requires**: `data` extra (`pip install "pysdmx[data]"`)
**Location**: `src/pysdmx/toolkit/pd/`

```python
from pysdmx.toolkit.pd import to_pandas_type, to_pandas_schema
```

### `to_pandas_type(comp: Component) -> str`

Maps a single `Component` to its pandas dtype string:

- If the component has an enumeration (codelist), returns `"category"`
- Otherwise maps `DataType` → pandas dtype, accounting for `required`:

| DataType | required=True | required=False |
|----------|--------------|----------------|
| `SHORT` | `"int16"` | `"Int16"` |
| `INTEGER` | `"int32"` | `"Int32"` |
| `LONG` | `"int64"` | `"Int64"` |
| `FLOAT` | `"float32"` | `"Float32"` |
| `DOUBLE` | `"float64"` | `"Float64"` |
| `BOOLEAN` | `"bool"` | `"boolean"` |
| `DATE_TIME` | `"datetime64[ns]"` | `"datetime64[ns]"` |
| `DATE` | `"datetime64[D]"` | `"datetime64[D]"` |
| `YEAR` | `"datetime64[Y]"` | `"datetime64[Y]"` |
| `YEAR_MONTH` | `"datetime64[M]"` | `"datetime64[M]"` |
| All others | `"string"` | `"string"` |

Required components use non-nullable numpy types; optional use nullable
pandas extension types (`Int16`, `Float32`, `boolean`, etc.).

```python
from pysdmx.model import Component, Role, Concept, DataType
from pysdmx.toolkit.pd import to_pandas_type

comp = Component(
    id="OBS_VALUE",
    required=True,
    role=Role.MEASURE,
    concept=Concept(id="OBS_VALUE", dtype=DataType.DOUBLE),
)
to_pandas_type(comp)  # "float64"

optional_comp = Component(
    id="OBS_VALUE",
    required=False,
    role=Role.MEASURE,
    concept=Concept(id="OBS_VALUE", dtype=DataType.DOUBLE),
)
to_pandas_type(optional_comp)  # "Float64"
```

### `to_pandas_schema(components: Iterable[Component]) -> Dict[str, str]`

Maps a collection of components to a `{component_id: pandas_dtype}` dict.
Use with `DataFrame.astype()` to cast columns:

```python
from pysdmx.toolkit.pd import to_pandas_schema

schema_dict = to_pandas_schema(dataflow_info.components)
# e.g. {"FREQ": "category", "OBS_VALUE": "Float64", "TIME_PERIOD": "string"}

df = df.astype(schema_dict)
```

Typically you only want to cast specific component roles:

```python
# Cast only dimensions and measures (exclude attributes)
comps = dataflow_info.components
relevant = list(comps.dimensions) + list(comps.measures)
schema_dict = to_pandas_schema(relevant)
df = df.astype(schema_dict)
```

---

## VTL Toolkit (`pysdmx.toolkit.vtl`)

**Requires**: `vtl` extra (`pip install "pysdmx[vtl]"`)
**Location**: `src/pysdmx/toolkit/vtl/`

```python
from pysdmx.toolkit.vtl import (
    model_validations,
    generate_vtl_script,
    convert_dataset_to_vtl,
    convert_dataset_to_sdmx,
)
```

### `model_validations(dataset, schema)`

Validates a `Dataset` against its `Schema` using the VTL engine. Returns
a list of validation errors (empty list = no errors):

```python
from pysdmx.toolkit.vtl import model_validations

errors = model_validations(my_dataset, my_schema)
if errors:
    for err in errors:
        print(err)
```

The dataset must already have its `structure` set to a `Schema` object
(use `get_datasets()` to ensure this).

### `generate_vtl_script(transformation_scheme)`

Generates a VTL script string from a `TransformationScheme` model object:

```python
from pysdmx.toolkit.vtl import generate_vtl_script

vtl_script = generate_vtl_script(transformation_scheme)
print(vtl_script)  # VTL code as a string
```

### `convert_dataset_to_vtl(dataset)`

Converts a pysdmx `Dataset` (with a pandas DataFrame in `dataset.data`)
to VTL engine-compatible format:

```python
from pysdmx.toolkit.vtl import convert_dataset_to_vtl

vtl_dataset = convert_dataset_to_vtl(my_dataset)
# vtl_dataset is now ready for the vtlengine library
```

### `convert_dataset_to_sdmx(vtl_dataset, schema)`

Converts VTL engine output back to a pysdmx `Dataset`:

```python
from pysdmx.toolkit.vtl import convert_dataset_to_sdmx

sdmx_dataset = convert_dataset_to_sdmx(vtl_result, my_schema)
# sdmx_dataset is a Dataset with .data as a pandas DataFrame
```

---

## Relationships

- `to_pandas_type` / `to_pandas_schema` use `Component.dtype` and
  `Component.enumeration` from `pysdmx.model.dataflow`
- VTL functions work with `Dataset`, `Schema`, `TransformationScheme` from
  `pysdmx.model`
- VTL conversion functions bridge between SDMX `Dataset` objects and the
  `vtlengine` library's internal format
- `get_datasets()` (in `pysdmx.io`) assigns `Schema` to datasets —
  always call it before running VTL or validation

---

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Importing `pysdmx.toolkit.pd` without `data` extra | `ImportError` | Install `pysdmx[data]` |
| Importing `pysdmx.toolkit.vtl` without `vtl` extra | `ImportError` | Install `pysdmx[vtl]` |
| Running `model_validations` with `dataset.structure` as a string | `AttributeError` | Use `get_datasets(data=..., structure=...)` first |
| Calling `to_pandas_schema` on all components including attributes | Wrong column types | Filter: use `comps.dimensions + comps.measures` |
| Assuming `to_pandas_type` returns nullable types for required components | Wrong dtype | Required = non-nullable (`int64`); optional = nullable (`Int64`) |
