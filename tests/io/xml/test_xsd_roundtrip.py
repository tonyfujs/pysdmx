"""XSD round-trip tests.

Each test takes a pysdmx model, serialises it with ``write_sdmx`` and
validates the resulting SDMX-ML against the matching SDMX XSD shipped
by ``sdmxschemas``. The tests act as regression locks for the writer,
ensuring that the XML we emit is accepted by tooling that speaks the
standard (including FMR).
"""

import pytest

sdmxschemas = pytest.importorskip("sdmxschemas")
etree = pytest.importorskip("lxml.etree")

from pysdmx.io.format import Format  # noqa: E402
from pysdmx.io.writer import write_sdmx  # noqa: E402
from pysdmx.model import (  # noqa: E402
    Code,
    Codelist,
    Concept,
    ConceptScheme,
    RepresentationMap,
    ValueMap,
)

pytestmark = pytest.mark.xml


_CODELIST_URN_PREFIX = "urn:sdmx:org.sdmx.infomodel.codelist.Codelist="
_CL_SRC_URN = f"{_CODELIST_URN_PREFIX}AGY:CL_SRC(1.0)"
_CL_TGT_URN = f"{_CODELIST_URN_PREFIX}AGY:CL_TGT(1.0)"


def _validate(xml: str, schema_path: str) -> etree.XMLSchema:
    schema = etree.XMLSchema(etree.parse(schema_path))
    doc = etree.fromstring(xml.encode("utf-8"))
    if not schema.validate(doc):
        errors = "\n".join(str(e) for e in schema.error_log)
        pytest.fail(f"XSD validation failed:\n{errors}")
    return schema


def _codelist() -> Codelist:
    return Codelist(
        id="CL_FREQ",
        agency="AGY",
        name="Frequency",
        version="1.0",
        items=[Code(id="A", name="Annual"), Code(id="M", name="Monthly")],
    )


def _concept_scheme() -> ConceptScheme:
    return ConceptScheme(
        id="CS_TEST",
        agency="AGY",
        name="Test concepts",
        version="1.0",
        items=[Concept(id="FREQ", name="Frequency")],
    )


@pytest.mark.parametrize(
    ("sdmx_format", "schema_path"),
    [
        (Format.STRUCTURE_SDMX_ML_2_1, sdmxschemas.SDMX_ML_21_MESSAGE_PATH),
        (Format.STRUCTURE_SDMX_ML_3_0, sdmxschemas.SDMX_ML_30_MESSAGE_PATH),
        (Format.STRUCTURE_SDMX_ML_3_1, sdmxschemas.SDMX_ML_31_MESSAGE_PATH),
    ],
)
def test_codelist_validates_against_xsd(sdmx_format, schema_path):
    xml = write_sdmx([_codelist()], sdmx_format)
    _validate(xml, schema_path)


def test_concept_scheme_validates_against_sdmx30_xsd():
    xml = write_sdmx([_concept_scheme()], Format.STRUCTURE_SDMX_ML_3_0)
    _validate(xml, sdmxschemas.SDMX_ML_30_MESSAGE_PATH)


def test_write_sdmx_validate_true_passes_on_valid_artefact():
    xml = write_sdmx(
        [_codelist()], Format.STRUCTURE_SDMX_ML_3_0, validate=True
    )
    _validate(xml, sdmxschemas.SDMX_ML_30_MESSAGE_PATH)


def test_representation_map_with_datatype_source_uses_correct_tag():
    """Regression for pysdmx PR #556 / commit 417488a.

    A RepresentationMap whose ``source`` is a plain SDMX DataType name
    (e.g. ``String``) must be serialised as ``<str:SourceDataType>``,
    not ``<str:SourceCodelist>``. Downstream projects previously had
    to patch the output with string replacement (tidysdmx
    ``fix_sdmx_xml_datatype_tags``).
    """
    rm = RepresentationMap(
        id="RM_TEST",
        agency="AGY",
        name="Test Rep Map",
        version="1.0",
        source="String",
        target=_CL_TGT_URN,
        maps=[ValueMap(source="a", target="X")],
    )
    xml = write_sdmx([rm], Format.STRUCTURE_SDMX_ML_3_0)
    assert "<str:SourceDataType>String</str:SourceDataType>" in xml, (
        "DataType source must use <str:SourceDataType> tag"
    )
    assert "<str:SourceCodelist>String" not in xml
    _validate(xml, sdmxschemas.SDMX_ML_30_MESSAGE_PATH)


def test_representation_map_with_codelist_source_uses_correct_tag():
    rm = RepresentationMap(
        id="RM_CL",
        agency="AGY",
        name="Rep Map",
        version="1.0",
        source=_CL_SRC_URN,
        target=_CL_TGT_URN,
        maps=[ValueMap(source="a", target="X")],
    )
    xml = write_sdmx([rm], Format.STRUCTURE_SDMX_ML_3_0)
    assert "<str:SourceCodelist>" in xml
    _validate(xml, sdmxschemas.SDMX_ML_30_MESSAGE_PATH)
