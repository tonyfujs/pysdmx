.. _fmr-api:

FMR API Reference Guide
=======================

``pysdmx`` provides a high-level client — ``RegistryClient`` (synchronous) and
``AsyncRegistryClient`` (asynchronous) — for retrieving SDMX structural metadata
from any `SDMX-REST 2.0.0 <https://github.com/sdmx-twg/sdmx-rest>`_-compliant
service, including the
`Fusion Metadata Registry (FMR) <https://www.bis.org/innovation/bis_open_tech_sdmx.htm>`_.
This guide covers every method available on those clients. For task-oriented
tutorials that show how the client fits into broader workflows, see:
:ref:`fs`, :ref:`physical-model`, :ref:`validate`, :ref:`map`, and
:ref:`maintenance`.

Connecting to an FMR
--------------------

Instantiate a client by passing the SDMX-REST v2 base endpoint. For an FMR
instance, this is the service root URL followed by ``/sdmx/v2/``.

.. code-block:: python

    from pysdmx.api.fmr import RegistryClient

    client = RegistryClient("https://sdmx.data.unicef.org/sdmx/v2/")

Constructor parameters
^^^^^^^^^^^^^^^^^^^^^^

``api_endpoint`` (str)
    The SDMX-REST v2 base URL of the target service.

``format`` (StructureFormat, default ``StructureFormat.SDMX_JSON_2_0_0``)
    Wire format for responses. Only ``SDMX_JSON_2_0_0`` and ``FUSION_JSON``
    are accepted by the FMR client. Use ``FUSION_JSON`` if the server is an
    FMR instance and you want Fusion-JSON responses.

    .. code-block:: python

        from pysdmx.api.fmr import RegistryClient
        from pysdmx.io.format import StructureFormat

        client = RegistryClient(
            "https://sdmx.data.unicef.org/sdmx/v2/",
            format=StructureFormat.FUSION_JSON,
        )

``pem`` (str, optional)
    Path to a PEM file for a custom certificate authority. Use this when the
    target service presents a certificate signed by a private CA.

``timeout`` (float, default ``10.0``)
    Maximum number of seconds to wait for a response before raising
    ``Unavailable``.

Sync vs async
^^^^^^^^^^^^^

``AsyncRegistryClient`` exposes an identical method surface. Swap the import
and prefix every call with ``await``:

.. code-block:: python

    from pysdmx.api.fmr import AsyncRegistryClient

    client = AsyncRegistryClient("https://sdmx.data.unicef.org/sdmx/v2/")
    flows = await client.get_dataflows("UNICEF")

See :ref:`fmr-api-async` for a complete async example.

Browsing the catalogue
-----------------------

Listing dataflows
^^^^^^^^^^^^^^^^^

``get_dataflows`` returns every dataflow matching the supplied filters. All
three parameters default to a wildcard, so calling it with no arguments
returns every dataflow published by every agency.

.. code-block:: python

    # All dataflows from all agencies
    all_flows = client.get_dataflows()

    # All UNICEF dataflows (latest version of each)
    unicef_flows = client.get_dataflows(agency="UNICEF")

    # A specific dataflow by ID
    flow = client.get_dataflows(agency="UNICEF", id="IMMUNISATION_COVERAGE")

    for df in unicef_flows:
        print(df.id, df.name, df.version)

Browsing categories
^^^^^^^^^^^^^^^^^^^

Category schemes group dataflows into thematic areas. ``get_categories``
returns a ``CategoryScheme`` whose ``dataflows`` property gives the flat set
of all dataflows attached at any level in the hierarchy.

.. code-block:: python

    cs = client.get_categories("UNICEF", "UNICEF_STATS", "+")

    # Iterate over top-level categories
    for cat in cs:
        print(cat.id, cat.name)

    # Flat set of every dataflow referenced in the scheme
    for flow_ref in cs.dataflows:
        print(flow_ref.id)

Retrieving a categorisation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``Categorisation`` links an individual dataflow to a category. Retrieve one
when you need to inspect or process that link directly.

.. code-block:: python

    cat = client.get_categorisation("UNICEF", "CAT_IMMUNISATION", "+")
    print(cat.artefact)   # the categorised artefact
    print(cat.category)   # the target category

Dataflow details
----------------

``get_dataflow_details`` returns a ``DataflowInfo`` object that bundles
core dataflow metadata with optional additional information controlled by
the ``detail`` parameter.

.. code-block:: python

    from pysdmx.api.fmr import DataflowDetails

    # All available information (default)
    info = client.get_dataflow_details(
        "UNICEF", "IMMUNISATION_COVERAGE", detail=DataflowDetails.ALL
    )

    # Core metadata only (name, description, DSD reference)
    core = client.get_dataflow_details(
        "UNICEF", "IMMUNISATION_COVERAGE", detail=DataflowDetails.CORE
    )

    # Core + list of data providers
    with_provs = client.get_dataflow_details(
        "UNICEF", "IMMUNISATION_COVERAGE", detail=DataflowDetails.PROVIDERS
    )

    # Core + validation schema
    with_schema = client.get_dataflow_details(
        "UNICEF", "IMMUNISATION_COVERAGE", detail=DataflowDetails.SCHEMA
    )

``DataflowDetails`` values
^^^^^^^^^^^^^^^^^^^^^^^^^^

``CORE``
    ID, name, description, and the reference to the underlying data structure.

``PROVIDERS``
    ``CORE`` plus the list of organisations that provide data for this flow.

``SCHEMA``
    ``CORE`` plus the validation schema (equivalent to calling
    ``get_schema("dataflow", ...)``, see below).

``ALL``
    Combines all three of the above.

Validation schema
-----------------

``get_schema`` calls the SDMX-REST ``schema`` endpoint, which the registry
uses to apply all applicable constraints and return the effective set of
allowed values for each component.

.. code-block:: python

    # Schema in the context of a dataflow (most constrained)
    schema = client.get_schema(
        "dataflow", "UNICEF", "IMMUNISATION_COVERAGE", "1.0"
    )

    # Schema in the context of a data structure (no flow-level constraints)
    schema = client.get_schema(
        "datastructure", "UNICEF", "DSD_IMMUNISATION", "1.0"
    )

    # Schema in the context of a provision agreement
    schema = client.get_schema(
        "provisionagreement", "UNICEF", "PA_IMMUNISATION_WHO", "1.0"
    )

Working with schema components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The returned ``Schema`` object exposes a ``components`` collection with one
entry per component defined in the data structure.

.. code-block:: python

    # Iterate over all components
    for comp in schema.components:
        print(comp.id, comp.role, comp.dtype, comp.required)

    # Access a component by ID
    freq = schema.components["FREQ"]
    print(freq.dtype)       # e.g. DataType.STRING
    print(freq.required)    # True / False

    # Coded component: list of allowed code IDs
    if freq.codes:
        allowed = [c.id for c in freq.codes]
        print(allowed)      # e.g. ['A', 'Q', 'M', 'D']

    # Facets (additional type constraints such as max_length)
    comment = schema.components["COMMENT_OBS"]
    if comment.facets:
        print(comment.facets.max_length)

    # Components by role
    for dim in schema.components.dimensions:
        print(dim.id)
    for attr in schema.components.attributes:
        print(attr.id)

Structural metadata
-------------------

Data structures
^^^^^^^^^^^^^^^

``get_data_structures`` returns data structure definitions (DSDs).

.. code-block:: python

    # All DSDs from all agencies
    all_dsds = client.get_data_structures()

    # DSDs from UNICEF
    unicef_dsds = client.get_data_structures(agency="UNICEF")

    for dsd in unicef_dsds:
        print(dsd.id, dsd.name, dsd.version)

Codelists and value lists
^^^^^^^^^^^^^^^^^^^^^^^^^

``get_codes`` retrieves a ``Codelist`` (or a ``ValueList`` if the artefact
is stored as such on the server — the method handles the fallback
transparently).

.. code-block:: python

    cl = client.get_codes("UNICEF", "CL_COUNTRY", "+")

    print(cl.id, cl.name)
    for code in cl:
        print(code.id, code.name)

Concept schemes
^^^^^^^^^^^^^^^

.. code-block:: python

    cs = client.get_concepts("UNICEF", "CS_COMMON", "+")

    for concept in cs:
        print(concept.id, concept.name, concept.dtype)

Hierarchies
^^^^^^^^^^^

``get_hierarchy`` returns a ``Hierarchy`` — a tree of ``HierarchicalCode``
objects. Each node carries its own children via the ``codes`` attribute.

.. code-block:: python

    hier = client.get_hierarchy("UNICEF", "HCL_COUNTRY_REF_AREA", "+")

    def walk(codes, depth=0):
        for hc in codes:
            print("  " * depth + hc.id, hc.name)
            if hc.codes:
                walk(hc.codes, depth + 1)

    walk(hier.codes)

Organisations
-------------

Agencies
^^^^^^^^

``get_agencies`` returns all sub-agencies defined within the agency scheme
maintained by the supplied parent agency.

.. code-block:: python

    agencies = client.get_agencies("SDMX")
    for agency in agencies:
        print(agency.id, agency.name)

Data providers
^^^^^^^^^^^^^^

``get_providers`` returns the data providers belonging to a provider scheme.
Pass ``with_flows=True`` to include the list of dataflows each provider
supplies data for.

.. code-block:: python

    # Provider list only
    providers = client.get_providers("UNICEF")

    # Providers with their associated dataflows
    providers = client.get_providers("UNICEF", with_flows=True)
    for prov in providers:
        print(prov.id, prov.name)
        for flow in prov.dataflows:
            print("  ->", flow.id)

Metadata providers
^^^^^^^^^^^^^^^^^^

``get_metadata_providers`` follows the same pattern but returns the scheme
of organisations that supply reference metadata reports.

.. code-block:: python

    meta_provs = client.get_metadata_providers("UNICEF", with_flows=True)
    for prov in meta_provs:
        print(prov.id)
        for mflow in prov.dataflows:
            print("  ->", mflow.id)

Provisioning metadata
---------------------

Provision agreements
^^^^^^^^^^^^^^^^^^^^

A ``ProvisionAgreement`` formalises the commitment of a specific data
provider to supply data for a specific dataflow.

.. code-block:: python

    pa = client.get_provision_agreement(
        "UNICEF", "PA_IMMUNISATION_WHO", "+"
    )
    print(pa.id, pa.name)
    print(pa.dataflow)          # dataflow reference
    print(pa.data_provider)     # provider reference

Metadata provision agreements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``get_metadata_provision_agreement`` is the reference-metadata counterpart,
linking a metadata provider to a metadataflow.

.. code-block:: python

    mpa = client.get_metadata_provision_agreement(
        "UNICEF", "MPA_COUNTRY_NOTES_UNICEF", "+"
    )
    print(mpa.id, mpa.metadataflow, mpa.metadata_provider)

Reference metadata
------------------

Metadataflows
^^^^^^^^^^^^^

.. code-block:: python

    mflows = client.get_metadataflows(agency="UNICEF")
    for mf in mflows:
        print(mf.id, mf.name)

Metadata structures (MSDs)
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    msds = client.get_metadata_structures(agency="UNICEF")
    for msd in msds:
        print(msd.id, msd.name)

Metadata reports
^^^^^^^^^^^^^^^^

``get_reports`` retrieves all metadata reports attached to a given
structure artefact (e.g. a dataflow). ``artefact_type`` is the lowercase
SDMX artefact class name, such as ``"dataflow"`` or ``"codelist"``.

.. code-block:: python

    reports = client.get_reports(
        "dataflow", "UNICEF", "IMMUNISATION_COVERAGE", "+"
    )
    for report in reports:
        print(report.id)
        for attr in report.attributes:
            print(" ", attr.id, "=", attr.value)

``get_report`` retrieves a single, known report by its provider and ID.

.. code-block:: python

    report = client.get_report("UNICEF", "MR_IMMUNISATION_NOTES", "+")
    for attr in report.attributes:
        print(attr.id, "=", attr.value)

Mappings
--------

Structure maps
^^^^^^^^^^^^^^

``get_mapping`` returns a ``StructureMap`` that describes how components in
one data structure map to components in another.

.. code-block:: python

    smap = client.get_mapping("UNICEF", "SM_IMMUNISATION_TO_SDMX", "+")
    print(smap.id, smap.name)
    print(smap.source)   # source structure reference
    print(smap.target)   # target structure reference
    for cm in smap.component_maps:
        print(cm.source, "->", cm.target)

Representation maps (code maps)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``get_code_map`` returns a ``RepresentationMap`` (or ``MultiRepresentationMap``
for many-to-many mappings).

.. code-block:: python

    rmap = client.get_code_map("UNICEF", "RM_CL_COUNTRY_ISO3", "+")
    for mapping in rmap:
        print(mapping.source, "->", mapping.target)

.. _fmr-api-async:

Async usage
-----------

``AsyncRegistryClient`` is a drop-in replacement for ``RegistryClient``.
Every method is a coroutine — prefix each call with ``await`` and run inside
an async context.

.. code-block:: python

    import asyncio
    from pysdmx.api.fmr import AsyncRegistryClient

    async def main() -> None:
        client = AsyncRegistryClient(
            "https://sdmx.data.unicef.org/sdmx/v2/"
        )

        flows = await client.get_dataflows(agency="UNICEF")
        for df in flows:
            print(df.id, df.name)

        schema = await client.get_schema(
            "dataflow", "UNICEF", "IMMUNISATION_COVERAGE", "1.0"
        )
        for comp in schema.components:
            print(comp.id, comp.dtype, comp.required)

    asyncio.run(main())

Use ``AsyncRegistryClient`` in async web applications or when fetching
multiple artefacts concurrently with ``asyncio.gather``.

.. code-block:: python

    async def fetch_all(client: AsyncRegistryClient) -> None:
        flows, agencies = await asyncio.gather(
            client.get_dataflows(agency="UNICEF"),
            client.get_agencies("SDMX"),
        )

Error handling
--------------

All client methods raise subclasses of ``pysdmx.errors.PysdmxError``. Import
the specific classes you need:

.. code-block:: python

    from pysdmx.errors import (
        Invalid,
        InternalError,
        NotFound,
        NotImplemented,
        Unauthorized,
        Unavailable,
    )

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Exception
     - Retriable
     - When it is raised
   * - ``Unavailable``
     - Yes
     - Network failure, connection timeout, or service temporarily down.
       The same request may succeed on retry.
   * - ``NotFound``
     - No
     - The requested artefact does not exist on the server (HTTP 404).
   * - ``Invalid``
     - No
     - The request itself is malformed or violates a constraint (HTTP 400 /
       409). Investigate the parameters before retrying.
   * - ``InternalError``
     - No
     - The request was valid but the server could not fulfil it (HTTP 5xx).
       Report to the service operator.
   * - ``Unauthorized``
     - No
     - Authentication failed or access to the resource was denied (HTTP 401 /
       403).
   * - ``NotImplemented``
     - No
     - The operation is not supported by the targeted service.

Example
^^^^^^^

.. code-block:: python

    from pysdmx.api.fmr import RegistryClient
    from pysdmx.errors import NotFound, Unavailable

    client = RegistryClient("https://sdmx.data.unicef.org/sdmx/v2/")

    try:
        schema = client.get_schema(
            "dataflow", "UNICEF", "IMMUNISATION_COVERAGE", "1.0"
        )
    except NotFound:
        print("Dataflow not found — check the agency, ID, and version.")
    except Unavailable:
        print("Service unreachable — retry later.")

Summary
-------

This guide covered all metadata retrieval methods on ``RegistryClient`` and
``AsyncRegistryClient``:

- **Catalogue browsing**: ``get_dataflows``, ``get_categories``,
  ``get_categorisation``
- **Dataflow details**: ``get_dataflow_details`` with ``DataflowDetails``
- **Schema**: ``get_schema`` for structural validation rules
- **Structural artefacts**: ``get_data_structures``, ``get_codes``,
  ``get_concepts``, ``get_hierarchy``
- **Organisations**: ``get_agencies``, ``get_providers``,
  ``get_metadata_providers``
- **Provisioning**: ``get_provision_agreement``,
  ``get_metadata_provision_agreement``
- **Reference metadata**: ``get_metadataflows``,
  ``get_metadata_structures``, ``get_reports``, ``get_report``
- **Mappings**: ``get_mapping``, ``get_code_map``

For complete API documentation, including all parameters and return types,
see :doc:`/api/fmr`.
