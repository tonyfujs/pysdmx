# pysdmx.errors

**Location**: `src/pysdmx/errors.py`
**No extras required.**

All pysdmx functions raise from this module. Never raise bare `Exception`.

---

## Exception Hierarchy

```
Exception
└── PysdmxError              base class; has title, description, csi
    ├── RetriableError        base for errors that CAN be retried
    │   └── Unavailable      service/resource not available — RETRIABLE
    ├── Invalid               bad input, validation failure — non-retriable
    ├── NotFound              resource does not exist — non-retriable
    ├── InternalError         valid request but cannot be fulfilled — non-retriable
    ├── NotImplemented        operation not supported — non-retriable
    └── Unauthorized          auth failure — non-retriable
```

Only `Unavailable` (and its parent `RetriableError`) should ever be caught
for retry logic.

---

## Constructor

All classes share the same signature:

```python
PysdmxError(
    title: str,
    description: Optional[str] = None,
    csi: Optional[Dict[str, Any]] = None,
)
```

- `title` — short, human-readable label (shown in tracebacks)
- `description` — longer explanation; include tips for resolution
- `csi` — context-specific info dict; arbitrary key/value pairs for debugging
- `str(err)` yields `"title: description"` if description is set, else `"title"`

---

## Each Exception

### `Invalid`

Raise when user input is wrong: missing field, unsupported combination,
constraint violation, bad format.

```python
from pysdmx.errors import Invalid

raise Invalid(
    "Missing agency",
    "Maintainable artefacts must reference an agency.",
    csi={"artefact_id": self.id},
)
```

Also raised by `__post_init__` methods in model classes (e.g. missing
`attachment_level` on an attribute `Component`, empty `Annotation`, missing
`agency` on a `MaintainableArtefact`).

### `Unavailable`

Raise (or catch for retry) when a service is unreachable, overloaded, or
temporarily down. This is the **only** retriable error.

```python
from pysdmx.errors import Unavailable

# The service layer raises this automatically for connection errors.
# Catch it for retry logic:
import time
for attempt in range(3):
    try:
        result = svc.data(query)
        break
    except Unavailable:
        time.sleep(2 ** attempt)
```

### `NotFound`

Raise when a resource simply does not exist and retrying will not help.

```python
from pysdmx.errors import NotFound

raise NotFound(
    "Codelist not found",
    f"CL_FREQ(1.0) not found in the registry.",
    csi={"urn": short_urn},
)
```

### `InternalError`

Raise when the request was valid but something went wrong during processing.
Signals a bug or server-side issue to investigate.

### `NotImplemented`

Raise when a feature or operation is not yet supported. Do **not** retry.

> **Warning**: `pysdmx.errors.NotImplemented` shadows Python's built-in
> `NotImplementedError`. Import carefully:
> ```python
> from pysdmx.errors import NotImplemented as SdmxNotImplemented
> ```

### `Unauthorized`

Raise for authentication or authorization failures. Do **not** retry before
verifying credentials.

---

## Retriable vs Non-Retriable

| Error class | Retry? | Recommended action |
|-------------|--------|--------------------|
| `Unavailable` | Yes | Exponential back-off; retry up to N times |
| `RetriableError` | Yes | Same as `Unavailable` (prefer `Unavailable`) |
| `Invalid` | No | Fix the request; check inputs |
| `NotFound` | No | Verify the resource ID exists |
| `InternalError` | No | Investigate or report the issue |
| `NotImplemented` | No | Use a different approach |
| `Unauthorized` | No | Fix credentials; do not send again |

```python
# Correct: only retry retriable errors
from pysdmx.errors import RetriableError

try:
    raw = svc.structure(query)
except RetriableError:
    raw = svc.structure(query)  # retry once

# Wrong: catching the base class retries non-retriable errors too
try:
    raw = svc.structure(query)
except PysdmxError:
    raw = svc.structure(query)  # BAD — do not do this
```

---

## Where Errors Are Raised

| Location | Error raised | Trigger |
|----------|-------------|---------|
| `model/__base.py` — `MaintainableArtefact.__post_init__` | `Invalid` | `agency` is empty |
| `model/__base.py` — `Annotation.__post_init__` | `Invalid` | All fields are `None` |
| `model/dataflow.py` — `Component.__post_init__` | `Invalid` | `attachment_level` rules violated |
| `model/__base.py` — `ItemScheme.search` | `Invalid` | Empty query string |
| `util/__init__.py` — `parse_urn` | `Invalid` | URN matches no known pattern |
| `util/__init__.py` — `find_by_urn` | `NotFound` | No artefact matches the URN |
| `io/reader.py` — `read_sdmx` | `Invalid` | Empty message |
| `io/reader.py` — `get_datasets` | `Invalid`, `NotFound` | No data or structure not found |
| `util/_net_utils.py` — `map_httpx_errors` | `NotFound`, `Invalid`, `InternalError`, `Unavailable` | HTTP error codes from services |
