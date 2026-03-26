# pysdmx.model

**Location**: `src/pysdmx/model/`
**No extras required.**

The primary public API of pysdmx. All SDMX domain objects live here as
`msgspec.Struct` subclasses. Import everything from the package root:

```python
from pysdmx.model import (
    Codelist, Code, Concept, ConceptScheme,
    Dataflow, DataStructureDefinition, Component, Components,
    Role, Schema, DataType, Facets,
    Message, Header, Dataset, ActionType,
    DataConstraint, Reference, ItemReference,
    # ... 88 symbols total
)
```

---

## Design

### Immutability

All classes use `msgspec.Struct(frozen=True, omit_defaults=True)`. Instances
are immutable. **Never assign to fields after creation.** To produce a
modified copy:

```python
import msgspec.structs as mss

updated = mss.replace(my_codelist, name="New Name", version="2.0")
```

`Dataset` is the **only** exception — it is mutable (`frozen=False`).

### Defaults are omitted

`omit_defaults=True` means fields set to their default value are skipped
during serialisation. A field with `Optional[str] = None` is omitted from
the output when `None`.

### Keyword-only fields

Classes with many optional fields use `kw_only=True` — all arguments must be
passed by name.

---

## Inheritance Chain

```
msgspec.Struct
└── AnnotableArtefact           annotations: Sequence[Annotation] = ()
    └── IdentifiableArtefact    + id: str, uri, urn
        └── NameableArtefact    + name, description
            └── VersionableArtefact  + version="1.0", valid_from, valid_to
                ├── Item             leaf item inside a scheme
                └── MaintainableArtefact  + agency (required!), is_final
                    └── ItemScheme   + items, is_partial, search()
```

`MaintainableArtefact.__post_init__` raises `Invalid` if `agency` is empty.

Every `MaintainableArtefact` has a `short_urn` property:

```python
cl.short_urn  # "Codelist=BIS:CL_FREQ(1.0)"
dsd.short_urn # "DataStructure=BIS:BIS_CBS(1.0)"
```

Format: `ClassName=Agency:Id(Version)`.

---

## Annotations

`Annotation` — extra information attached to any SDMX artefact.

```python
Annotation(
    id: Optional[str] = None,
    title: Optional[str] = None,
    text: Optional[str] = None,   # also accessible as .value
    url: Optional[str] = None,
    type: Optional[str] = None,
)
```

At least one field must be set (raises `Invalid` if all are `None`).

---

## References

### `Reference`

Coordinates of a maintainable artefact:

```python
Reference(sdmx_type="Codelist", agency="BIS", id="CL_FREQ", version="1.0")
str(ref)  # "Codelist=BIS:CL_FREQ(1.0)"
```

### `ItemReference`

Like `Reference` but with an `item_id` for items within a scheme:

```python
ItemReference(sdmx_type="Codelist", agency="BIS", id="CL_FREQ",
              version="1.0", item_id="A")
str(ref)  # "Codelist=BIS:CL_FREQ(1.0).A"
```

### `DataflowRef`

Lightweight reference to a dataflow with optional `name`:

```python
DataflowRef(agency="BIS", id="BIS_CBS", version="1.0", name="CBS")
str(ref)  # "Dataflow=BIS:BIS_CBS(1.0)"
```

---

## Codes and Codelists

### `Code`

Single code; inherits `Item` (which inherits `NameableArtefact`):

```python
Code(id="A", name="Annual", valid_from=datetime(...), valid_to=None)
```

### `Codelist`

Flat, iterable collection of `Code` objects. Also used for SDMX value lists:

```python
cl = Codelist(
    id="CL_FREQ",
    agency="BIS",
    name="Frequency",
    items=[Code(id="A", name="Annual"), Code(id="Q", name="Quarterly")],
    sdmx_type="codelist",  # or "valuelist"
)

for code in cl:          # iterable
    print(code.id)

cl["A"]                  # get by id
"Q" in cl                # membership test
len(cl)                  # count
cl.search("ann")         # search by name/description substring
```

### `Hierarchy` and `HierarchicalCode`

Hierarchical organisation of codes. `HierarchicalCode` has
`codes: Sequence[HierarchicalCode]` for nesting. `HierarchyAssociation` links
a `Hierarchy` to a `Codelist`.

---

## Concepts

### `DataType`

Enum (35+ values) for value types. Default is `DataType.STRING`.

Key values:

| DataType | Description |
|----------|-------------|
| `STRING` | Default; arbitrary text |
| `ALPHA` | Letters only |
| `ALPHA_NUM` | Letters and digits |
| `INTEGER` | 32-bit integer |
| `LONG` | 64-bit integer |
| `SHORT` | 16-bit integer |
| `DOUBLE` | 64-bit float |
| `FLOAT` | 32-bit float |
| `BOOLEAN` | True/False |
| `DATE` | Calendar date |
| `DATE_TIME` | Date + time |
| `YEAR` | Gregorian year (e.g. 2024) |
| `YEAR_MONTH` | Gregorian year-month (e.g. 2024-03) |
| `PERIOD` | Reporting period |
| `DURATION` | ISO 8601 duration |
| `URI` | URI/URL |
| `XHTML` | XHTML markup |

### `Facets`

Constraints on a concept's values:

```python
Facets(
    min_length=1,
    max_length=10,
    min_value=0,
    max_value=100,
    pattern=r"\d{4}",
    decimals=2,
    is_sequence=False,
    interval=None,
    start_value=None,
    end_value=None,
    start_time=None,
    end_time=None,
)
```

### `Concept`

Describes a statistical concept:

```python
Concept(
    id="FREQ",
    name="Frequency",
    dtype=DataType.STRING,   # effective data type
    facets=Facets(max_length=3),
    codes=my_codelist,       # enumeration values
    enum_ref=Reference(...), # reference to external codelist
)
```

### `ConceptScheme`

`ItemScheme` subclass holding `Concept` items. Supports iteration,
`__getitem__`, `__contains__`, and `.search()`.

---

## Dataflows and Data Structures

### `Role`

```python
class Role(str, Enum):
    DIMENSION = "D"
    MEASURE   = "M"
    ATTRIBUTE = "A"
```

### `Component`

A variable in a dataset:

```python
Component(
    id="FREQ",
    required=True,
    role=Role.DIMENSION,
    concept=Concept(id="FREQ", dtype=DataType.STRING),
    local_dtype=None,       # overrides concept dtype if set
    local_facets=None,
    local_codes=None,       # overrides concept codelist if set
    attachment_level=None,  # REQUIRED when role == ATTRIBUTE; MUST be absent otherwise
)
```

**`attachment_level` rules** (enforced by `__post_init__`, raises `Invalid`):
- `Role.ATTRIBUTE` → `attachment_level` must be set (e.g. `"O"` for
  observation, `"S"` for series, `"D"` for dataset, `"G"` for group)
- `Role.DIMENSION` or `Role.MEASURE` → `attachment_level` must be `None`

Convenience properties:
- `.dtype` — effective `DataType` (local → concept → `STRING`)
- `.facets` — effective `Facets` (local → concept → `None`)
- `.enumeration` — effective `Codelist` (local → concept → `None`)
- `.enum_ref` — effective `Reference` to codelist

### `Components`

A `UserList[Component]` with extra behaviour:

```python
comps = Components([freq_comp, obs_val, obs_status])

comps["FREQ"]       # get by id (str index)
comps[0]            # get by position (int index)
"FREQ" in comps     # membership test

comps.dimensions    # Sequence[Component] where role == DIMENSION
comps.measures      # Sequence[Component] where role == MEASURE
comps.attributes    # Sequence[Component] where role == ATTRIBUTE
```

Raises `Invalid` on duplicate `id` when appending, inserting, or extending.

### `DataStructureDefinition`

`MaintainableArtefact` holding a `Components` object. Has a `.to_schema()`
convenience method.

### `Schema`

The resolved structure for a given dataflow/DSD/provision agreement. Returned
by a schema query:

```python
Schema(
    context="dataflow",         # "datastructure" | "dataflow" | "provisionagreement"
    agency="BIS",
    id="BIS_CBS",
    version="1.0",
    components=Components([...]),
    is_ref=False,
    dimension_at_observation="TIME_PERIOD",
    explicit_measure=False,
    keys=None,              # KeySet of required data keys
    excluded_keys=None,     # KeySet of excluded data keys
)
```

`Dataset.structure` holds a `Schema` (or its short URN string before
structure assignment).

### `Dataflow`

References a `DataStructureDefinition` (by object or by short URN string):

```python
Dataflow(
    id="BIS_CBS",
    agency="BIS",
    name="BIS Consolidated Banking Statistics",
    structure="DataStructure=BIS:BIS_CBS(1.0)",  # str or DSD object
)
```

### `ProvisionAgreement`

Links a `DataProvider` to a `Dataflow`.

### `DataflowInfo`

Richer dataflow description with `components`, `providers`, `series_count`,
`obs_count`, etc. Returned by FMR client.

---

## Datasets and Messages

### `ActionType`

```python
class ActionType(str, Enum):
    Append      = "Append"
    Replace     = "Replace"
    Delete      = "Delete"
    Information = "Information"
```

### `Dataset`

The **only mutable** model class (`frozen=False`). Holds a collection of data
observations (typically a pandas DataFrame when the `data` extra is installed):

```python
Dataset(
    structure=my_schema,          # Schema or str short_urn
    attributes={},                # dataset-level attributes dict
    action=ActionType.Replace,
    valid_from=None,
    valid_to=None,
    publication_year=None,
    publication_period=None,
    data=None,                    # pandas DataFrame (or None)
)
```

- `dataset.data` is a pandas `DataFrame` when reading CSV/JSON data
- `dataset.attributes` is a `Dict[str, Optional[str]]` for dataset-level
  attributes extracted from the data

### `SeriesInfo`

Metadata about a single time series:

```python
SeriesInfo(
    id="...",
    name="...",
    obs_count=120,
    start_period="2010-Q1",
    end_period="2023-Q4",
    last_updated=datetime(...),
    is_active=True,
)
```

### `Header`

Message header:

```python
Header(
    id="MSG_001",
    prepared=datetime.now(timezone.utc),
    sender="BIS",
    receiver=None,
    dataset_action=ActionType.Replace,
    source=None,
    structure={},
    dataset_id=(),
    test=False,
)
```

### `Message`

Top-level container returned by `read_sdmx()`:

```python
msg.structures   # Sequence[MaintainableArtefact] — structure messages
msg.data         # Sequence[Dataset] — data messages
msg.reports      # Sequence[MetadataReport] — reference metadata messages
msg.submission   # Sequence[SubmissionResult] — registry submission results
msg.header       # Optional[Header]
```

Typed accessor methods (raise `NotFound` if missing):

```python
msg.get_codelists()                        # Sequence[Codelist]
msg.get_codelist("Codelist=BIS:CL_FREQ(1.0)")
msg.get_concept_schemes()
msg.get_concept_scheme(short_urn)
msg.get_data_structure_definitions()
msg.get_data_structure_definition(short_urn)
msg.get_dataflows()
msg.get_dataflow(short_urn)
msg.get_categorisations()
msg.get_category_schemes()
msg.get_hierarchies()
msg.get_structure_maps()
msg.get_dataset(short_urn)                 # Dataset by structure short_urn
```

---

## Organisations

```
Organisation (Item)
├── Agency          — maintains structural metadata
├── DataProvider    — provides data
├── MetadataProvider — provides reference metadata
└── DataConsumer    — collects data or metadata
```

Each has `contacts: Sequence[Contact]` and `dataflows: Sequence[DataflowRef]`.

`Contact` fields: `id`, `name`, `department`, `role`, `telephones`, `faxes`,
`uris`, `emails`.

Scheme wrappers (all `ItemScheme` subclasses):
- `AgencyScheme`, `DataProviderScheme`, `DataConsumerScheme`,
  `MetadataProviderScheme`

---

## Categories

- `Category` — nested grouping node; iterable over child `Category` objects
- `CategoryScheme` — `ItemScheme` of `Category` objects
- `Categorisation` — links a `Category` to a `Dataflow` (or other artefact)

---

## Constraints

- `DataConstraint` — allowed/excluded values for a dataflow or DSD
- `CubeRegion` — list of `CubeKeyValue` objects defining allowed values per
  component; has `included: bool`
- `DataKey` — specific combination of component values (a series key)
- `DataKeyValue` — single `(id, value)` pair within a `DataKey`
- `KeySet` — set of `DataKey` objects; has `included: bool`
- `ConstraintAttachment` — the artefacts to which the constraint is attached

---

## Maps

For cross-walk / structure mapping:

| Class | Purpose |
|-------|---------|
| `StructureMap` | Maps one structure to another |
| `ComponentMap` | Maps individual components |
| `MultiComponentMap` | Many-to-many component mapping |
| `RepresentationMap` | Maps code representations |
| `MultiRepresentationMap` | Many-to-many representation mapping |
| `ValueMap` | Maps specific values |
| `MultiValueMap` | Many-to-many value mapping |
| `FixedValueMap` | Maps a component to a fixed value |
| `ImplicitComponentMap` | Implicit (identity) mapping |
| `DatePatternMap` | Maps date strings using a pattern |

---

## Reference Metadata

| Class | Purpose |
|-------|---------|
| `MetadataStructure` | Formal definition of a metadata structure |
| `MetadataAttribute` | Attribute in the structure |
| `MetadataComponent` | Component defining metadata attribute |
| `Metadataflow` | Flow of metadata following a structure |
| `MetadataProvisionAgreement` | Links provider to metadataflow |
| `MetadataReport` | Actual metadata report content |

---

## VTL

VTL artefacts for Validation and Transformation Language support
(requires `vtl` extra to execute, but model classes are always available):

| Class | Purpose |
|-------|---------|
| `Transformation` | A VTL statement (expression + result assignment) |
| `TransformationScheme` | Collection of `Transformation` objects |
| `Ruleset` | Persistent set of rules |
| `RulesetScheme` | Collection of `Ruleset` objects |
| `UserDefinedOperator` | Custom VTL operator |
| `UserDefinedOperatorScheme` | Collection of custom operators |
| `NamePersonalisation` | Custom name for a VTL token |
| `NamePersonalisationScheme` | Collection of name personalisations |
| `CustomType` | Custom data type |
| `CustomTypeScheme` | Collection of custom types |
| `VtlMapping` | Base mapping class |
| `VtlMappingScheme` | Scheme of VTL mappings |
| `VtlDataflowMapping` | Maps a dataflow to a VTL alias |
| `VtlCodelistMapping` | Maps a codelist to a VTL alias |
| `VtlConceptMapping` | Maps a concept to a VTL alias |
| `ToVtlMapping` | Method: SDMX → VTL direction |
| `FromVtlMapping` | Method: VTL → SDMX direction |

---

## msgspec Serialisation

For `Components` (a `UserList`, not a `Struct`), use the custom hooks:

```python
import msgspec
from pysdmx.model import Components, encoders, decoders

encoder = msgspec.json.Encoder(enc_hook=encoders)
decoder = msgspec.json.Decoder(Components, dec_hook=decoders)

json_bytes = encoder.encode(my_components)
restored = decoder.decode(json_bytes)
```

For pure `Struct` classes, `msgspec` handles them natively without hooks.

---

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Assigning to a frozen struct field | `TypeError` | Use `msgspec.structs.replace()` |
| Missing `attachment_level` for `Role.ATTRIBUTE` | `Invalid` | Always set `attachment_level` for attributes |
| Setting `attachment_level` for non-attribute | `Invalid` | Remove it for dimensions and measures |
| Empty `agency` on `MaintainableArtefact` | `Invalid` | Always supply `agency` |
| Duplicate component `id` in `Components` | `Invalid` | Each component must have a unique `id` |
| Treating `Dataset` as frozen | Logic errors | `Dataset` is the only mutable class |
| Using `msg.structures[0]` directly | May be wrong type | Use typed getters: `msg.get_codelists()` etc. |
