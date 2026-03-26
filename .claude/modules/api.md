# pysdmx.api

**Location**: `src/pysdmx/api/`
**No extras required for core; `dc` extra for Data Connector protocol.**

Service clients and query builders for SDMX-REST APIs, the Fusion Metadata
Registry (FMR), the Global Discovery Service (GDS), and a Data Connector
protocol.

---

## Sub-package Map

```
api/
├── qb/          # Query Builder — SDMX-REST and GDS-REST clients
│   ├── service.py      RestService, AsyncRestService, GdsRestService
│   ├── data.py         DataQuery, DataFormat, DataContext
│   ├── structure.py    StructureQuery, StructureType, StructureDetail, StructureFormat
│   ├── schema.py       SchemaQuery, SchemaFormat
│   ├── availability.py AvailabilityQuery, AvailabilityFormat
│   ├── refmeta.py      RefMeta*Query, RefMetaFormat
│   ├── registration.py Registration*Query, RegistryFormat
│   ├── gds.py          GdsQuery, GdsType
│   └── util.py         ApiVersion
├── fmr/         # Fusion Metadata Registry client
├── gds/         # Global Discovery Service client
└── dc/          # Data Connector protocol (requires dc extra)
    └── query/   # Filter model for data queries
```

---

## `RestService` — Synchronous SDMX-REST Client

**Location**: `src/pysdmx/api/qb/service.py`

```python
from pysdmx.api.qb.service import RestService
from pysdmx.api.qb.util import ApiVersion
from pysdmx.api.qb.data import DataFormat
from pysdmx.api.qb.structure import StructureFormat
from pysdmx.api.qb.schema import SchemaFormat
from pysdmx.api.qb.refmeta import RefMetaFormat
from pysdmx.api.qb.availability import AvailabilityFormat
from pysdmx.api.qb.registration import RegistryFormat

svc = RestService(
    api_endpoint="https://sdmx.example.org/rest",   # trailing slash stripped
    api_version=ApiVersion.V2_0_0,
    data_format=DataFormat.SDMX_JSON_2_0_0,          # default
    structure_format=StructureFormat.SDMX_JSON_2_0_0, # default
    schema_format=SchemaFormat.SDMX_JSON_2_0_0_STRUCTURE, # default
    refmeta_format=RefMetaFormat.SDMX_JSON_2_0_0,    # default
    avail_format=AvailabilityFormat.SDMX_JSON_2_0_0, # default
    registry_format=RegistryFormat.FUSION_JSON,       # default
    pem=None,       # path to PEM file for custom CA
    timeout=5.0,    # seconds; None = no timeout
)
```

All query methods return `bytes`. Pass the result to `read_sdmx()`:

```python
from pysdmx.io.reader import read_sdmx

raw = svc.structure(query)     # bytes
msg = read_sdmx(raw)           # Message
```

### Methods

| Method | Argument | Returns |
|--------|----------|---------|
| `svc.data(query)` | `DataQuery` | `bytes` |
| `svc.structure(query)` | `StructureQuery` | `bytes` |
| `svc.schema(query)` | `SchemaQuery` | `bytes` |
| `svc.availability(query)` | `AvailabilityQuery` | `bytes` |
| `svc.reference_metadata(query)` | `RefMetaBy*Query` | `bytes` |
| `svc.registration(query)` | `RegistrationBy*Query` | `bytes` |

---

## `AsyncRestService` — Asynchronous SDMX-REST Client

Identical interface to `RestService`; all methods are `async`:

```python
from pysdmx.api.qb.service import AsyncRestService
import asyncio

async def fetch_codelist():
    svc = AsyncRestService(
        api_endpoint="https://sdmx.example.org/rest",
        api_version=ApiVersion.V2_0_0,
    )
    raw = await svc.structure(query)
    return read_sdmx(raw)

msg = asyncio.run(fetch_codelist())
```

---

## `ApiVersion`

```python
from pysdmx.api.qb.util import ApiVersion
```

`IntEnum` — values are comparable with `<`, `>`, `==`:

| Value | Description |
|-------|-------------|
| `V1_0_0` | SDMX-REST 1.0.0 |
| `V1_5_0` | SDMX-REST 1.5.0 |
| `V2_0_0` | SDMX-REST 2.0.0 (most common modern version) |
| `V2_1_0` | SDMX-REST 2.1.0 |
| `V2_2_0` | SDMX-REST 2.2.0 |
| `V2_2_2` | SDMX-REST 2.2.2 |
| `LATEST` | Latest supported version |

V2.0.0+ features (raise `Invalid` if used with older version):
- `components` filter in `DataQuery`
- `as_of` parameter
- Multiple resource IDs in a single query
- New `StructureType` values

Query builders raise `Invalid` when a feature is used with an incompatible
`ApiVersion`.

---

## `DataQuery`

```python
from pysdmx.api.qb.data import DataQuery, DataContext

query = DataQuery(
    context=DataContext.DATAFLOW,      # DATAFLOW | DATA_STRUCTURE | PROVISION_AGREEMENT | ALL
    agency_id="BIS",
    resource_id="BIS_CBS",
    version="1.0",                     # "*" = all versions
    key="Q.5J.*.*.*.*.*.*.*.*.*.*.A",  # dimension filter; "*" or "all" = all values
    provider_ref=None,                 # specific data provider
    start_period=None,                 # e.g. "2020-Q1"
    end_period=None,
    updated_after=None,                # datetime for incremental updates
    first_n_obs=None,
    last_n_obs=4,                      # return only last N observations
    dimension_at_observation=None,     # e.g. "TIME_PERIOD"
    attributes=None,                   # "none" | "all" | specific ids
    measures=None,                     # "none" | "all" | specific ids
    include_history=False,
    components=None,                   # V2.0.0+ filter (MultiFilter etc.)
    as_of=None,                        # V2.0.0+ reference date
)
```

`DataContext` values: `DATAFLOW`, `DATA_STRUCTURE`, `PROVISION_AGREEMENT`,
`ALL`. Most queries use `DataContext.DATAFLOW`.

---

## `StructureQuery`

```python
from pysdmx.api.qb.structure import (
    StructureQuery, StructureType, StructureDetail, StructureReference
)

query = StructureQuery(
    artefact_type=StructureType.CODELIST,
    agency_id="BIS",
    resource_id="CL_FREQ",
    version="1.0",                          # "~" = latest
    item_id=None,                           # specific item within a scheme
    detail=StructureDetail.FULL,            # level of detail
    references=StructureReference.NONE,     # related artefacts to include
)
```

### Build from a reference or URN

```python
# From a Reference or ItemReference object
q = StructureQuery.from_ref(my_reference)

# From a short URN string
q = StructureQuery.from_ref("Codelist=BIS:CL_FREQ(1.0)")

# From a full URN
q = StructureQuery.from_ref(
    "urn:sdmx:org.sdmx.infomodel.codelist.Codelist=BIS:CL_FREQ(1.0)"
)
```

### `StructureType` values

`CODELIST`, `VALUE_LIST`, `CONCEPT_SCHEME`, `CATEGORY_SCHEME`,
`DATAFLOW`, `DATA_STRUCTURE`, `PROVISION_AGREEMENT`,
`HIERARCHY`, `HIERARCHY_ASSOCIATION`,
`METADATA_STRUCTURE`, `METADATAFLOW`,
`STRUCTURE_MAP`, `REPRESENTATION_MAP`,
`TRANSFORMATION_SCHEME`, `RULESET_SCHEME`,
`USER_DEFINED_OPERATOR_SCHEME`, `CUSTOM_TYPE_SCHEME`,
`NAME_PERSONALISATION_SCHEME`, `VTL_MAPPING_SCHEME`,
`AGENCY_SCHEME`, `DATA_PROVIDER_SCHEME`, `DATA_CONSUMER_SCHEME`,
`METADATA_PROVIDER_SCHEME`, `ALL`

### `StructureDetail` values

`FULL`, `ALL_STUBS`, `REFERENCE_STUBS`, `RAW`,
`ALL_COMPLETE_STUBS`, `MATCHED_ITEMS`, `CASCADE_ITEMS`

### `StructureReference` values

`NONE`, `PARENTS`, `PARENTSANDSIBLINGS`, `ANCESTORS`,
`CHILDREN`, `DESCENDANTS`, `ALL`; or a specific `StructureType` name.

---

## `SchemaQuery`

Queries the schema endpoint — returns the allowed component values for a
given dataflow, DSD, or provision agreement:

```python
from pysdmx.api.qb.schema import SchemaQuery, SchemaContext

query = SchemaQuery(
    context=SchemaContext.DATAFLOW,
    agency_id="BIS",
    resource_id="BIS_CBS",
    version="1.0",
    dimension_at_observation=None,
    explicit_measure=False,
)
```

The result (after `read_sdmx()`) is a `Message` with `structures` containing
a `DataStructureDefinition` with `Schema` information.

---

## Availability Query

```python
from pysdmx.api.qb.availability import AvailabilityQuery, AvailabilityMode

query = AvailabilityQuery(
    context=DataContext.DATAFLOW,
    agency_id="BIS",
    resource_id="BIS_CBS",
    version="1.0",
    key=None,
    component_id=None,      # which component to get availability for
    mode=AvailabilityMode.EXACT,  # EXACT | AVAILABLE
    references=StructureReference.NONE,
    start_period=None,
    end_period=None,
    updated_after=None,
    include_history=False,
)
```

---

## Reference Metadata Queries

```python
from pysdmx.api.qb.refmeta import (
    RefMetaByMetadataflowQuery,
    RefMetaByMetadatasetQuery,
    RefMetaByStructureQuery,
)

# By metadataflow
q = RefMetaByMetadataflowQuery(agency_id="BIS", resource_id="MDF_CBS")

# By metadata set ID
q = RefMetaByMetadatasetQuery(provider_id="BIS", resource_id="MS_001")

# By structure (artefact it describes)
q = RefMetaByStructureQuery(
    artefact_type=StructureType.DATAFLOW,
    agency_id="BIS",
    resource_id="BIS_CBS",
    version="1.0",
)
```

---

## Registration Queries

```python
from pysdmx.api.qb.registration import (
    RegistrationByContextQuery,
    RegistrationByIdQuery,
    RegistrationByProviderQuery,
)

q = RegistrationByContextQuery(
    context=DataContext.DATAFLOW,
    agency_id="BIS",
    resource_id="BIS_CBS",
)
q = RegistrationByIdQuery(registration_id="REG_001")
q = RegistrationByProviderQuery(provider_ref="BIS")
```

---

## GDS REST Service

```python
from pysdmx.api.qb.service import GdsRestService, GdsAsyncRestService
from pysdmx.api.qb.gds import GdsQuery, GdsType

svc = GdsRestService(
    api_endpoint="https://gds.sdmx.io",
    pem=None,
    timeout=5.0,
)
query = GdsQuery(resource_type=GdsType.AGENCIES, agency="BIS")
raw = svc.gds(query)
```

The GDS client in `api/gds/` provides a higher-level typed interface:

```python
from pysdmx.api.gds import GdsClient, GdsAsyncClient

client = GdsClient()               # defaults to public GDS endpoint
agencies = client.agencies("BIS")  # Sequence[Agency]
catalogs = client.catalogs("BIS")  # Sequence[GdsCatalog]
services = client.sdmx_apis("BIS") # Sequence[GdsService]
resolved = client.urn_resolver("urn:sdmx:...")
```

---

## FMR Client (`api/fmr/`)

Higher-level client for the Fusion Metadata Registry. Returns typed model
objects directly (not raw bytes):

```python
from pysdmx.api.fmr import RegistryClient, AsyncRegistryClient
from pysdmx.api.fmr import DataflowDetails

client = RegistryClient(api_endpoint="https://fmr.example.org/sdmx")

# Typed results — no need to call read_sdmx()
dataflows = client.dataflows(agency_id="BIS")        # Sequence[Dataflow]
cl = client.codelist("BIS", "CL_FREQ", "1.0")        # Codelist
dsd = client.data_structure("BIS", "BIS_CBS", "1.0") # DataStructureDefinition
df_info = client.dataflow(
    "BIS", "BIS_CBS", "1.0", DataflowDetails.ALL
)  # DataflowInfo

# Maintenance operations
from pysdmx.api.fmr.maintenance import submit
submit(client, [my_codelist])  # upload artefacts
```

`DataflowDetails` enum: `ALL`, `CORE`, `PROVIDERS`, `SCHEMA`.

---

## Data Connector Protocol (`api/dc/`)

Requires `dc` extra. A `runtime_checkable Protocol` that custom data sources
must implement to integrate with pysdmx:

```python
from pysdmx.api.dc import Connector
```

Methods to implement:

| Method | Returns |
|--------|---------|
| `dataflows(filter_query, provider)` | `Iterable[DataflowRef]` |
| `providers(filter_query)` | `Iterable[Organisation]` |
| `dataflow(dataflow, metrics)` | `DataflowInfo` |
| `series(dataflow, provider, filters, ...)` | `Generator[SeriesInfo, ...]` |
| `data(dataflow, provider, series, filters, ...)` | generator or `DataFrame` |

### Filter classes

```python
from pysdmx.api.dc.query import (
    TextFilter, NumberFilter, BooleanFilter, DateTimeFilter,
    NullFilter, NotFilter, MultiFilter, Operator, LogicalOperator, SortBy
)

# Text filter
f1 = TextFilter("COUNTRY", Operator.EQUALS, "US")

# Number filter
f2 = NumberFilter("VALUE", Operator.GREATER_THAN, 100.0)

# Combine with AND
combined = MultiFilter([f1, f2], LogicalOperator.AND)

# Negate
negated = NotFilter(f1)
```

`Operator` values: `EQUALS`, `NOT_EQUALS`, `LESS_THAN`, `GREATER_THAN`,
`LESS_THAN_OR_EQUAL`, `GREATER_THAN_OR_EQUAL`, `LIKE`, `IN`, `BETWEEN`,
`NOT_LIKE`, `NOT_IN`, `NOT_BETWEEN`.

`LogicalOperator` values: `AND`, `OR`.

---

## Error Mapping (HTTP → pysdmx errors)

The service layer in `util/_net_utils.py` (`map_httpx_errors`) converts
`httpx` exceptions to pysdmx errors:

| HTTP status | pysdmx error |
|-------------|-------------|
| 404 | `NotFound` |
| 4xx (other) | `Invalid` |
| 5xx | `InternalError` |
| Connection error | `Unavailable` (retriable) |
| Timeout | `Unavailable` (retriable) |

---

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Using raw `bytes` from service methods directly | Wrong type | Always pass through `read_sdmx()` |
| Using V2.0.0+ features (`components`, `as_of`) with `ApiVersion.V1_0_0` | `Invalid` | Check `ApiVersion` matches the service |
| Not handling `Unavailable` in production code | Unhandled exception | Wrap service calls in try/except with back-off |
| Calling `svc.structure(q)` for data | Empty `msg.data` | Use correct method: `svc.data(q)` for data |
| Passing a `DataContext.ALL` key without wildcard dimension | Invalid URL | Use `"*"` for all-values dimensions |
