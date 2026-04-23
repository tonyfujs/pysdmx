import pytest

from pysdmx.errors import Invalid
from pysdmx.io.format import Format
from pysdmx.io.writer import write_sdmx
from pysdmx.model import (
    AgencyScheme,
    CategoryScheme,
    Code,
    Codelist,
    Component,
    Components,
    Concept,
    ConceptScheme,
    Dataflow,
    DataStructureDefinition,
    HierarchicalCode,
    Hierarchy,
    MultiRepresentationMap,
    MultiValueMap,
    RepresentationMap,
    Role,
    StructureMap,
    ValidationError,
    ValidationIssue,
    validate,
    validate_many,
)


def _codelist(**over):
    kw = {
        "id": "CL_TEST",
        "agency": "AGY",
        "name": "Test",
        "items": (Code(id="A"),),
    }
    kw.update(over)
    return Codelist(**kw)


def _dim(id_):
    return Component(
        id=id_,
        required=True,
        role=Role.DIMENSION,
        concept=Concept(id=id_),
    )


def _measure(id_):
    return Component(
        id=id_,
        required=True,
        role=Role.MEASURE,
        concept=Concept(id=id_),
    )


def test_validation_issue_has_expected_fields():
    issue = ValidationIssue(
        rule_id="M001", path="Codelist=A:B(1.0)", message="bad", field="id"
    )
    assert issue.rule_id == "M001"
    assert issue.path == "Codelist=A:B(1.0)"
    assert issue.field == "id"
    assert issue.severity == "error"


def test_validation_error_is_invalid_subclass():
    issue = ValidationIssue(rule_id="M001", path="p", message="m")
    err = ValidationError([issue])
    assert isinstance(err, Invalid)
    assert err.issues == (issue,)
    assert "[M001]" in str(err)


def test_validation_error_formats_field_when_present():
    with_field = ValidationIssue(
        rule_id="R001", path="p", message="m", field="source"
    )
    no_field = ValidationIssue(rule_id="DF001", path="q", message="m")
    err = ValidationError([with_field, no_field])
    msg = str(err)
    assert "p.source" in msg
    assert "q:" in msg


def test_check_common_flags_empty_id():
    cl = _codelist(id="")
    issues = validate(cl)
    assert any(i.rule_id == "M001" for i in issues)


def test_check_common_flags_empty_version():
    cl = _codelist(version="")
    issues = validate(cl)
    assert any(i.rule_id == "M002" for i in issues)


def test_check_common_flags_missing_name():
    cl = _codelist(name=None)
    issues = validate(cl)
    assert any(i.rule_id == "M003" for i in issues)


def test_check_common_flags_whitespace_name():
    cl = _codelist(name="   ")
    issues = validate(cl)
    assert any(i.rule_id == "M003" for i in issues)


def test_valid_codelist_has_no_issues():
    assert validate(_codelist()) == []


def test_empty_codelist_flagged():
    cl = _codelist(items=())
    assert any(i.rule_id == "C001" for i in validate(cl))


def test_empty_concept_scheme_flagged():
    cs = ConceptScheme(id="CS", agency="AGY", name="n", items=())
    assert any(i.rule_id == "CS001" for i in validate(cs))


def test_populated_concept_scheme_ok():
    cs = ConceptScheme(
        id="CS", agency="AGY", name="n", items=(Concept(id="X"),)
    )
    assert validate(cs) == []


def test_empty_category_scheme_flagged():
    cat = CategoryScheme(id="CAT", agency="AGY", name="n", items=())
    assert any(i.rule_id == "CAT001" for i in validate(cat))


def test_empty_agency_scheme_flagged():
    ag = AgencyScheme(id="AG", agency="AGY", name="n", items=())
    assert any(i.rule_id == "AS001" for i in validate(ag))


def test_empty_hierarchy_flagged():
    h = Hierarchy(id="H", agency="AGY", name="n", codes=())
    assert any(i.rule_id == "H001" for i in validate(h))


def test_populated_hierarchy_ok():
    h = Hierarchy(
        id="H",
        agency="AGY",
        name="n",
        codes=(HierarchicalCode(id="X"),),
    )
    assert validate(h) == []


def test_representation_map_missing_source_target_maps():
    rm = RepresentationMap(id="R", agency="AGY", name="n")
    ids = {i.rule_id for i in validate(rm)}
    assert {"R001", "R002", "R003"} <= ids


def test_representation_map_populated_ok():
    from pysdmx.model import ValueMap

    rm = RepresentationMap(
        id="R",
        agency="AGY",
        name="n",
        source="Codelist=AGY:SRC(1.0)",
        target="String",
        maps=[ValueMap(source="a", target="b")],
    )
    assert validate(rm) == []


def test_multi_representation_map_missing_fields():
    mrm = MultiRepresentationMap(id="MR", agency="AGY", name="n")
    ids = {i.rule_id for i in validate(mrm)}
    assert {"R001", "R002", "R003"} <= ids


def test_multi_representation_map_populated_ok():
    mrm = MultiRepresentationMap(
        id="MR",
        agency="AGY",
        name="n",
        source=["Codelist=AGY:SRC(1.0)"],
        target=["String"],
        maps=[MultiValueMap(source=["a"], target=["b"])],
    )
    assert validate(mrm) == []


def test_dsd_without_components_flagged():
    dsd = DataStructureDefinition(
        id="DSD",
        agency="AGY",
        name="n",
        components=Components([]),
    )
    assert any(i.rule_id == "D001" for i in validate(dsd))


def test_dsd_without_dimension_flagged():
    dsd = DataStructureDefinition(
        id="DSD",
        agency="AGY",
        name="n",
        components=Components([_measure("OBS_VALUE")]),
    )
    assert any(i.rule_id == "D002" for i in validate(dsd))


def test_dsd_with_dimension_ok():
    dsd = DataStructureDefinition(
        id="DSD",
        agency="AGY",
        name="n",
        components=Components([_dim("FREQ"), _measure("OBS_VALUE")]),
    )
    assert validate(dsd) == []


def test_dataflow_without_structure_flagged():
    df = Dataflow(id="DF", agency="AGY", name="n")
    assert any(i.rule_id == "DF001" for i in validate(df))


def test_dataflow_with_structure_ok():
    df = Dataflow(
        id="DF",
        agency="AGY",
        name="n",
        structure="DataStructure=AGY:DSD(1.0)",
    )
    assert validate(df) == []


def test_validate_on_artefact_without_specific_checker():
    sm = StructureMap(
        id="SM",
        agency="AGY",
        name="n",
        source="DataStructure=AGY:S(1.0)",
        target="DataStructure=AGY:T(1.0)",
    )
    assert validate(sm) == []


def test_validate_many_returns_empty_for_empty_input():
    assert validate_many([]) == []


def test_validate_many_concatenates_issues():
    bad_cl = _codelist(items=())
    bad_h = Hierarchy(id="H", agency="AGY", name="n", codes=())
    issues = validate_many([bad_cl, bad_h])
    assert {i.rule_id for i in issues} == {"C001", "H001"}


def test_write_sdmx_raises_validation_error_on_bad_artefact():
    empty = RepresentationMap(id="R", agency="AGY", name="n")
    with pytest.raises(ValidationError) as exc:
        write_sdmx([empty], Format.STRUCTURE_SDMX_ML_3_0, validate=True)
    assert any(i.rule_id == "R003" for i in exc.value.issues)
