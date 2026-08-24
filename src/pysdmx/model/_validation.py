"""Publish-readiness validation for maintainable SDMX artefacts.

These checks complement the structural invariants enforced in each
artefact's ``__post_init__``. They describe rules that an artefact must
satisfy **before it is published** to a registry such as FMR, but that
may legitimately not hold for artefacts round-tripped from a registry
(e.g. partial or draft records). For that reason the checks are opt-in
and are not moved into ``__post_init__``.

The public entry points are :func:`validate` and :func:`validate_many`,
plus the :class:`ValidationIssue` and :class:`ValidationError` types.
"""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
)

from msgspec import Struct

from pysdmx.errors import Invalid
from pysdmx.model.__base import ItemScheme, MaintainableArtefact
from pysdmx.model.category import CategoryScheme
from pysdmx.model.code import Codelist, Hierarchy
from pysdmx.model.concept import ConceptScheme
from pysdmx.model.dataflow import Dataflow, DataStructureDefinition, Role
from pysdmx.model.map import MultiRepresentationMap, RepresentationMap
from pysdmx.model.organisation import AgencyScheme


class ValidationIssue(
    Struct, frozen=True, omit_defaults=True, repr_omit_defaults=True
):
    """A single publish-readiness validation failure.

    Attributes:
        rule_id: Stable identifier of the broken rule (e.g. ``M001``).
        path: Short URN of the offending artefact.
        message: Human-readable description of the problem.
        field: Name of the field in error, if applicable.
        severity: ``error`` (blocks publishing) or ``warning``.
    """

    rule_id: str
    path: str
    message: str
    field: Optional[str] = None
    severity: Literal["error", "warning"] = "error"


class ValidationError(Invalid):
    """Raised when one or more artefacts fail publish-readiness checks.

    Subclasses :class:`pysdmx.errors.Invalid` so existing ``except
    Invalid:`` handlers keep working.

    Attributes:
        issues: The collected :class:`ValidationIssue` instances.
    """

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        """Build an aggregated error message from the supplied issues."""
        self.issues = tuple(issues)
        lines = [
            f"  - [{i.rule_id}] {i.path}"
            + (f".{i.field}" if i.field else "")
            + f": {i.message}"
            for i in self.issues
        ]
        description = "\n".join(["The following issues were found:", *lines])
        super().__init__("Artefact(s) not ready to publish", description)


def _issue(
    rule_id: str,
    artefact: MaintainableArtefact,
    message: str,
    field: Optional[str] = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        path=artefact.short_urn,
        message=message,
        field=field,
    )


def _check_common(a: MaintainableArtefact) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not a.id:
        issues.append(_issue("M001", a, "id must be non-empty.", "id"))
    if not a.version:
        issues.append(
            _issue("M002", a, "version must be non-empty.", "version")
        )
    if a.name is None or not a.name.strip():
        issues.append(
            _issue("M003", a, "name must be a non-empty string.", "name")
        )
    return issues


def _items_rule(
    rule_id: str, a: ItemScheme, label: str
) -> List[ValidationIssue]:
    if not a.items:
        return [
            _issue(
                rule_id,
                a,
                f"{label} must contain at least one item.",
                "items",
            )
        ]
    return []


def _check_codelist(a: Codelist) -> List[ValidationIssue]:
    return _items_rule("C001", a, "Codelist")


def _check_concept_scheme(a: ConceptScheme) -> List[ValidationIssue]:
    return _items_rule("CS001", a, "ConceptScheme")


def _check_category_scheme(a: CategoryScheme) -> List[ValidationIssue]:
    return _items_rule("CAT001", a, "CategoryScheme")


def _check_agency_scheme(a: AgencyScheme) -> List[ValidationIssue]:
    return _items_rule("AS001", a, "AgencyScheme")


def _check_hierarchy(a: Hierarchy) -> List[ValidationIssue]:
    if not a.codes:
        return [
            _issue(
                "H001",
                a,
                "Hierarchy must contain at least one code.",
                "codes",
            )
        ]
    return []


def _check_representation_map(a: RepresentationMap) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not a.source:
        issues.append(_issue("R001", a, "source must be populated.", "source"))
    if not a.target:
        issues.append(_issue("R002", a, "target must be populated.", "target"))
    if not a.maps:
        issues.append(
            _issue(
                "R003",
                a,
                "maps must contain at least one value mapping.",
                "maps",
            )
        )
    return issues


def _check_multi_representation_map(
    a: MultiRepresentationMap,
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not a.source:
        issues.append(_issue("R001", a, "source must be populated.", "source"))
    if not a.target:
        issues.append(_issue("R002", a, "target must be populated.", "target"))
    if not a.maps:
        issues.append(
            _issue(
                "R003",
                a,
                "maps must contain at least one value mapping.",
                "maps",
            )
        )
    return issues


def _check_dsd(a: DataStructureDefinition) -> List[ValidationIssue]:
    components = list(a.components) if a.components else []
    if not components:
        return [
            _issue(
                "D001",
                a,
                "DataStructureDefinition must define at least one component.",
                "components",
            )
        ]
    if not any(c.role == Role.DIMENSION for c in components):
        return [
            _issue(
                "D002",
                a,
                "DataStructureDefinition must define at least one dimension.",
                "components",
            )
        ]
    return []


def _check_dataflow(a: Dataflow) -> List[ValidationIssue]:
    if a.structure is None:
        return [
            _issue(
                "DF001",
                a,
                "Dataflow must reference a data structure.",
                "structure",
            )
        ]
    return []


_SPECIFIC: Dict[
    Type[MaintainableArtefact],
    Callable[[Any], List[ValidationIssue]],
] = {
    Codelist: _check_codelist,
    ConceptScheme: _check_concept_scheme,
    CategoryScheme: _check_category_scheme,
    AgencyScheme: _check_agency_scheme,
    Hierarchy: _check_hierarchy,
    RepresentationMap: _check_representation_map,
    MultiRepresentationMap: _check_multi_representation_map,
    DataStructureDefinition: _check_dsd,
    Dataflow: _check_dataflow,
}


def validate(artefact: MaintainableArtefact) -> List[ValidationIssue]:
    """Check that an artefact is ready to be published.

    Runs the common maintainable rules and any type-specific rules
    registered for the artefact's concrete class.

    Args:
        artefact: The artefact to validate.

    Returns:
        The list of :class:`ValidationIssue` found (empty if the
        artefact is publish-ready).
    """
    issues = _check_common(artefact)
    checker = _SPECIFIC.get(type(artefact))
    if checker is not None:
        issues.extend(checker(artefact))
    return issues


def validate_many(
    artefacts: Sequence[MaintainableArtefact],
) -> List[ValidationIssue]:
    """Validate a sequence of artefacts.

    Args:
        artefacts: The artefacts to validate.

    Returns:
        The concatenated list of issues across every artefact, in
        input order. Empty if every artefact is publish-ready.
    """
    out: List[ValidationIssue] = []
    for a in artefacts:
        out.extend(validate(a))
    return out
