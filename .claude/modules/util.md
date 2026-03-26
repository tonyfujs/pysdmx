# pysdmx.util

**Location**: `src/pysdmx/util/`
**No extras required.**

Public utility functions for URN parsing and artefact lookup. Used throughout
the library and commonly needed by callers working with SDMX URNs.

---

## Public API

```python
from pysdmx.util import (
    parse_urn,
    parse_maintainable_urn,
    parse_item_urn,
    parse_short_urn,
    parse_short_item_urn,
    find_by_urn,
    convert_dpm,          # date pattern map conversion
    map_httpx_errors,     # internal; exposed for library authors
    Reference,            # re-exported from pysdmx.model
    ItemReference,        # re-exported from pysdmx.model
)
```

---

## URN Formats

SDMX supports four URN patterns. Use the right parser for each:

| Pattern | Example | Parser |
|---------|---------|--------|
| Full maintainable URN | `urn:sdmx:org.sdmx.infomodel.codelist.Codelist=BIS:CL_FREQ(1.0)` | `parse_maintainable_urn()` |
| Full item URN | `urn:sdmx:org.sdmx.infomodel.codelist.Codelist=BIS:CL_FREQ(1.0).A` | `parse_item_urn()` |
| Short maintainable URN | `Codelist=BIS:CL_FREQ(1.0)` | `parse_short_urn()` |
| Short item URN | `Codelist=BIS:CL_FREQ(1.0).A` | `parse_short_item_urn()` |

When in doubt about which format you have, use `parse_urn()` — it tries all
four patterns in order.

---

## `parse_urn(urn: str) -> Union[ItemReference, Reference]`

Universal parser. Tries all four patterns; raises `Invalid` if none match.

Returns `Reference` for maintainable URNs and `ItemReference` for item URNs:

```python
from pysdmx.util import parse_urn

# Short maintainable URN → Reference
ref = parse_urn("Codelist=BIS:CL_FREQ(1.0)")
ref.sdmx_type  # "Codelist"
ref.agency     # "BIS"
ref.id         # "CL_FREQ"
ref.version    # "1.0"
str(ref)       # "Codelist=BIS:CL_FREQ(1.0)"

# Short item URN → ItemReference
iref = parse_urn("Codelist=BIS:CL_FREQ(1.0).A")
iref.item_id   # "A"
str(iref)      # "Codelist=BIS:CL_FREQ(1.0).A"

# Full URN → Reference
ref2 = parse_urn(
    "urn:sdmx:org.sdmx.infomodel.codelist.Codelist=BIS:CL_FREQ(1.0)"
)
```

Raises `Invalid` when the string matches none of the four patterns.

---

## Individual Parsers

Use these when you know exactly which URN format to expect:

### `parse_maintainable_urn(urn: str) -> Reference`

Parses a full maintainable URN (starts with `urn:sdmx:`).
Raises `Invalid` if the string is not a full maintainable URN.

### `parse_item_urn(urn: str) -> ItemReference`

Parses a full item URN (starts with `urn:sdmx:`, ends with `.item_id`).
Raises `Invalid` if the string is not a full item URN.

### `parse_short_urn(urn: str) -> Reference`

Parses a short maintainable URN (`Type=Agency:Id(Version)`).
Raises `Invalid` if the string is not a short maintainable URN.

### `parse_short_item_urn(urn: str) -> ItemReference`

Parses a short item URN (`Type=Agency:Id(Version).item_id`).
Raises `Invalid` if the string is not a short item URN.

---

## `find_by_urn(artefacts: Sequence[Any], urn: str) -> Any`

Searches a sequence of `MaintainableArtefact` objects and returns the first
one matching the supplied URN. Supports both `str` and `Agency` object as
`agency` field on the artefact.

```python
from pysdmx.util import find_by_urn

# Find a codelist in a message's structures
cl = find_by_urn(msg.structures, "Codelist=BIS:CL_FREQ(1.0)")

# Works with full URNs too
cl = find_by_urn(
    msg.structures,
    "urn:sdmx:org.sdmx.infomodel.codelist.Codelist=BIS:CL_FREQ(1.0)",
)
```

Raises `NotFound` if no artefact matches, with a helpful message listing
all available artefacts.

Matching logic:
- `artefact.agency == ref.agency` (string comparison), OR
- `artefact.agency.id == ref.agency` (when `agency` is an `Agency` object)
- AND `artefact.id == ref.id`
- AND `artefact.version == ref.version`

---

## `convert_dpm(date_pattern: str, period: str) -> str`

Converts a date pattern map token and period string to a normalised date
string. Used internally by the I/O layer when processing `DatePatternMap`
structures; rarely called directly.

```python
from pysdmx.util import convert_dpm

normalised = convert_dpm("YYYY", "2024")
```

---

## Return Types

### `Reference`

```python
Reference(
    sdmx_type: str,   # e.g. "Codelist", "DataStructure"
    agency: str,      # e.g. "BIS"
    id: str,          # e.g. "CL_FREQ"
    version: str,     # e.g. "1.0"
)
str(ref)  # "Codelist=BIS:CL_FREQ(1.0)"
```

### `ItemReference`

```python
ItemReference(
    sdmx_type: str,
    agency: str,
    id: str,
    version: str,
    item_id: str,     # e.g. "A" (the item within the scheme)
)
str(iref)  # "Codelist=BIS:CL_FREQ(1.0).A"
```

Both are `msgspec.Struct(frozen=True)` — immutable.

---

## Internal Helpers (Not for Direct Use)

These are internal to the library but exposed in `__all__` for library
authors extending pysdmx:

### `map_httpx_errors(e)` — `util/_net_utils.py`

Converts `httpx.RequestError` and `httpx.HTTPStatusError` to pysdmx errors:

| Condition | pysdmx error |
|-----------|-------------|
| 404 | `NotFound` |
| 4xx (other) | `Invalid` |
| 5xx | `InternalError` |
| Connection/timeout error | `Unavailable` (retriable) |

Used by `RestService`, `AsyncRestService`, and the GDS service classes.

### `schema_generator(msg, ref)` — `util/_model_utils.py`

Builds a `Schema` from a `Message` by locating the structure matching `ref`.
Used by `get_datasets()` during structure assignment.

### `_date_pattern_map.py`

Internal lookup tables for date pattern conversion. Contains
`convert_dpm()` implementation.

---

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Calling `parse_short_urn()` with a full URN | `Invalid` | Use `parse_urn()` instead |
| Calling `parse_maintainable_urn()` with a short URN | `Invalid` | Use `parse_urn()` instead |
| Expecting `parse_urn()` on `"Type=A:B(v).item"` to return `Reference` | Wrong type | It returns `ItemReference` (has `.item_id`) |
| Passing a list without `.agency`/`.id`/`.version` to `find_by_urn()` | `AttributeError` | Only pass `MaintainableArtefact` instances |
| Using `find_by_urn()` when version is unknown | `NotFound` | Use `msg.get_codelist(short_urn)` which supports version wildcards |
