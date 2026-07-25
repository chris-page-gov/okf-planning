"""Domain models for the OKF Planning bundle and its Explorer projection."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OKFPlanningResource:
    """Resource entry representing an endpoint, download, or documentation page."""

    id: str
    title: str
    url: str
    format: str = "json"
    media_type: str = "application/json"
    dcat_type: str = "access-service"
    resource_type: str = "api-endpoint"
    description: str = ""


@dataclass
class OKFPlanningAlternative:
    """Confusable or substitute dataset alternative with recorded differences."""

    record_id: str
    title: str
    route: str
    relationship_type: str = "cross-source-alternative"
    differences: list[dict[str, str]] = field(default_factory=list)


@dataclass
class OKFPlanningRecord:
    """Normalized OKF Planning Record (dataset, policy, legal instrument, or geography)."""

    id: str
    route: str
    title: str
    description: str
    record_type: str
    collection: str
    typology: str
    phase: str
    themes: list[str]
    entity_count: int
    licence: str
    licence_text: str
    attribution: str
    attribution_text: str
    source_url: str
    documentation_url: str
    source_adapter: str
    publisher: str
    publisher_id: str
    publisher_name: str
    confidence: str = "observed"
    wikidata: str = ""
    wikipedia: str = ""
    github_discussion: int = 0
    entity_minimum: int = 0
    entity_maximum: int = 0
    consideration: str = ""
    replacement_dataset: str = ""
    resources: list[OKFPlanningResource] = field(default_factory=list)
    alternatives: list[OKFPlanningAlternative] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    spatial_coverage: dict[str, Any] = field(default_factory=dict)
    metadata_created: str = "2026-07-25T08:00:00Z"
    metadata_modified: str = "2026-07-25T08:00:00Z"
    generated_by: str = "okf-planning/0.2.0"
    status: str = "draft"
    stale_after: str = "2026-10-25"

    @property
    def concept_type(self) -> str:
        """Return a descriptive, deliberately unregistered OKF concept type."""
        return {
            "organisation": "Planning Organisation",
            "document": "Planning Document",
            "legal-instrument": "Legal Instrument",
            "policy": "Planning Policy",
        }.get(self.typology, "Planning Dataset")

    @property
    def source_entry(self) -> dict[str, Any]:
        """Return the OKF v0.2 provenance source for this concept."""
        if self.source_adapter == "planning-data-gov-uk":
            resource = "https://www.planning.data.gov.uk/dataset.json"
            title = "Planning Data England dataset catalogue snapshot"
        else:
            resource = self.source_url
            title = f"Curated source for {self.title}"
        return {
            "id": "source-record",
            "resource": resource,
            "title": title,
        }

    def to_explorer_dict(self, base_url: str) -> dict[str, Any]:
        """Convert to Explorer runtime JSON format."""
        return {
            "id": self.id,
            "name": self.id,
            "route": self.route,
            "open": self.route,
            "title": self.title,
            "description": self.description,
            "summary": (
                self.description[:200] + "..."
                if len(self.description) > 200
                else self.description
            ),
            "record_type": self.record_type,
            "collection": self.collection,
            "typology": self.typology,
            "phase": self.phase,
            "themes": self.themes,
            "entity_count": self.entity_count,
            "licence_id": self.licence,
            "licence_title": self.licence_text,
            "attribution": self.attribution_text,
            "source": self.source_adapter,
            "source_url": self.source_url,
            "documentation_url": self.documentation_url,
            "publisher": self.publisher_id,
            "publisher_title": self.publisher_name,
            "publisher_url": self.publisher,
            "confidence": self.confidence,
            "wikidata": self.wikidata,
            "tags": self.tags,
            "resources": [
                {
                    "id": r.id,
                    "title": r.title,
                    "url": r.url,
                    "format": r.format,
                    "media_type": r.media_type,
                    "dcat_type": r.dcat_type,
                    "resource_type": r.resource_type,
                    "description": r.description,
                }
                for r in self.resources
            ],
            "alternatives": [
                {
                    "record_id": a.record_id,
                    "title": a.title,
                    "route": a.route,
                    "relationship_type": a.relationship_type,
                    "differences": a.differences,
                }
                for a in self.alternatives
            ],
            "node_json": {
                "@id": f"{base_url}dataset/{self.id}",
                "@type": self._dcat_type(),
                "dct:identifier": f"planning:{self.id}",
                "dct:title": self.title,
                "dct:description": self.description,
                "dcat:theme": self.themes,
                "okf:typology": self.typology,
                "okf:collection": self.collection,
                "okf:phase": self.phase,
                "okf:entityCount": self.entity_count,
                "okf:notEndorsedBySource": True,
                "prov:wasAttributedTo": self.publisher,
            },
            "generated": {"by": self.generated_by, "at": self.metadata_modified},
            "sources": [self.source_entry],
            "status": self.status,
            "stale_after": self.stale_after,
            "trust_tier": "unverified",
            "provenance": {
                "schema": "okf-provenance.v1",
                "source_adapter": self.source_adapter,
                "source_record_url": self.source_url,
                "source_url": self.source_entry["resource"],
                "snapshot_id": "planning-2026-07-25-r1",
                "generated_at": self.metadata_modified,
            },
            "authority": {
                "bundlePublisher": {
                    "id": "https://github.com/chris-page-gov/okf-planning",
                    "name": "OKF Planning project",
                    "url": "https://github.com/chris-page-gov/okf-planning",
                },
                "sourcePublisher": [
                    {
                        "id": self.publisher_id,
                        "name": self.publisher_name,
                        "url": self.publisher,
                    }
                ],
                "notEndorsedBySource": True,
                "reviewedBy": [],
            },
        }

    def to_yaml_ld_dict(self, base_url: str) -> dict[str, Any]:
        """Convert to canonical OKF 0.2 YAML-LD / JSON-LD document node."""
        return {
            "@id": f"{base_url}dataset/{self.id}",
            "@type": self._dcat_type().removeprefix("dcat:"),
            "identifier": f"planning:{self.id}",
            "title": self.title,
            "description": self.description,
            "landingPage": self.source_url,
            "sourcePublisher": [self.publisher],
            "bundlePublisher": f"{base_url}",
            "semanticAuthority": f"{base_url}",
            "wasAttributedTo": f"{base_url}",
            "wasDerivedFrom": self.source_url,
            "wasGeneratedBy": f"{base_url}data/governance/release.json",
            "notEndorsedBySource": True,
            "reviewedBy": [],
        }

    def _dcat_type(self) -> str:
        """Return the closest DCAT type without claiming all concepts are datasets."""
        if self.typology == "organisation":
            return "prov:Agent"
        if self.typology in {"document", "policy", "legal-instrument"}:
            return "dcat:Resource"
        return "dcat:Dataset"


@dataclass
class OKFPlanningRelationship:
    """Graph relationship edge between two nodes in the bundle."""

    source_id: str
    target_id: str
    relationship_type: str
    evidence_type: str = "deterministic-collection-rule"
    confidence: str = "inferred"
    note: str = ""

    def to_explorer_dict(self) -> dict[str, Any]:
        return {
            "source": f"dataset/{self.source_id}",
            "target": f"dataset/{self.target_id}",
            "kind": self.relationship_type,
            "evidence_type": self.evidence_type,
            "confidence": self.confidence,
            "note": self.note,
        }
