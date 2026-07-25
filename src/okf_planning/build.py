"""Deterministic OKF v0.2 bundle compiler for UK planning metadata."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import shutil
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from okf_planning.model import (
    OKFPlanningAlternative,
    OKFPlanningRecord,
    OKFPlanningRelationship,
    OKFPlanningResource,
)
from okf_planning.sources import get_all_augmented_datasets

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://chris-page-gov.github.io/okf-planning/"
SNAPSHOT_ID = "planning-2026-07-25-r1"
SOURCE_CAPTURED_AT = "2026-07-25T08:00:00Z"
GENERATED_AT = "2026-07-25T11:25:00Z"
STALE_AFTER = "2026-10-25"
GENERATOR_ACTOR = "okf-planning/0.2.0"
OKF_SPEC = (
    "https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/"
    "3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/SPEC.md"
)
ACTOR_PATTERN = re.compile(
    r"^(?:(?:human|process):[^\s:]+|[^/\s:]+/[^/\s]+)$"
)

GENERATED_DIRECTORIES = ("concepts", "context", "data")
GENERATED_ROOT_FILES = (
    "checksums.json",
    "index.md",
    "log.md",
    "okf-bundle.jsonld",
    "okf-bundle.yamlld",
    "okf-explorer.json",
)


def fnv1a_32(text: str) -> int:
    """Compute 32-bit FNV-1a for deterministic search bucket compatibility."""
    value = 2166136261
    for byte in text.encode("utf-8"):
        value ^= byte
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def compute_sha256(filepath: str | Path) -> str:
    """Calculate a file's SHA-256 digest."""
    digest = hashlib.sha256()
    with open(filepath, "rb") as source:
        while chunk := source.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "record"


def _clean_generated_output(bundle_dir: Path) -> None:
    """Remove only paths owned by the generator, retaining hand-authored UI assets."""
    for relative in GENERATED_DIRECTORIES:
        target = bundle_dir / relative
        if target.is_symlink():
            raise ValueError(f"Refusing to replace generated symlink: {target}")
        if target.exists():
            shutil.rmtree(target)
    for relative in GENERATED_ROOT_FILES:
        target = bundle_dir / relative
        if target.is_symlink():
            raise ValueError(f"Refusing to replace generated symlink: {target}")
        if target.exists():
            target.unlink()


def _resource(
    *,
    dataset_id: str,
    suffix: str,
    title: str,
    url: str,
    resource_type: str,
    description: str,
) -> OKFPlanningResource:
    return OKFPlanningResource(
        id=f"{dataset_id}-{suffix}",
        title=title,
        url=url,
        format="html",
        media_type="text/html",
        dcat_type="landing-page" if resource_type == "landing-page" else "documentation",
        resource_type=resource_type,
        description=description,
    )


def build_okf_planning_records(
    raw_datasets: list[dict[str, Any]], base_url: str
) -> tuple[list[OKFPlanningRecord], list[OKFPlanningRelationship]]:
    """Normalize source records without inventing access or download endpoints."""
    del base_url  # Retained in the public function signature for compatibility.
    records: list[OKFPlanningRecord] = []
    relationships: list[OKFPlanningRelationship] = []

    for dataset in sorted(raw_datasets, key=lambda item: str(item.get("dataset", ""))):
        dataset_id = str(dataset.get("dataset", "")).strip()
        if not dataset_id:
            continue

        name = str(dataset.get("name") or dataset_id)
        description = str(
            dataset.get("description")
            or dataset.get("text")
            or f"Planning metadata record for {name}."
        )
        typology = str(dataset.get("typology") or "geography")
        collection = str(dataset.get("collection") or "planning-data")
        phase = str(dataset.get("phase") or "beta")
        themes = sorted({str(theme) for theme in dataset.get("themes", ["development"])})
        source_adapter = str(dataset.get("source_adapter") or "planning-data-gov-uk")
        source_url = str(
            dataset.get("source_url")
            or f"https://www.planning.data.gov.uk/dataset/{dataset_id}"
        )
        documentation_url = str(dataset.get("documentation_url") or source_url)
        publisher_url = str(
            dataset.get("source_publisher") or "https://www.planning.data.gov.uk/"
        )
        publisher_id = str(dataset.get("publisher_id") or "planning-data-england")
        publisher_name = str(
            dataset.get("publisher_name") or "Planning Data England / MHCLG"
        )

        resources = [
            _resource(
                dataset_id=dataset_id,
                suffix="source",
                title=f"Official source page for {name}",
                url=source_url,
                resource_type="landing-page",
                description=(
                    "Source landing page carried for discovery. This bundle does not "
                    "assert that the page is a machine-readable data endpoint."
                ),
            )
        ]
        if documentation_url != source_url:
            resources.append(
                _resource(
                    dataset_id=dataset_id,
                    suffix="documentation",
                    title=f"Documentation for {name}",
                    url=documentation_url,
                    resource_type="documentation",
                    description="Source-published documentation or guidance.",
                )
            )

        alternatives: list[OKFPlanningAlternative] = []
        if "listed-building" in dataset_id:
            alternatives.append(
                OKFPlanningAlternative(
                    record_id="historic-england-nhle-heritage",
                    title="Historic England NHLE Statutory List",
                    route="dataset/historic-england-nhle-heritage",
                    differences=[
                        {
                            "field": "scope",
                            "selected": "Planning Data England catalogue representation",
                            "alternative": "Historic England source representation",
                        }
                    ],
                )
            )
        elif "conservation-area" in dataset_id:
            alternatives.append(
                OKFPlanningAlternative(
                    record_id="article-4-direction-area",
                    title="Article 4 Direction Areas",
                    route="dataset/article-4-direction-area",
                    differences=[
                        {
                            "field": "legal_basis",
                            "selected": "Conservation area designation",
                            "alternative": "Article 4 direction",
                        }
                    ],
                )
            )

        record = OKFPlanningRecord(
            id=dataset_id,
            route=f"dataset/{dataset_id}",
            title=name,
            description=description,
            record_type=typology,
            collection=collection,
            typology=typology,
            phase=phase,
            themes=themes,
            entity_count=int(dataset.get("entity-count") or 0),
            licence=str(dataset.get("licence") or "ogl3"),
            licence_text=str(
                dataset.get("licence-text")
                or "Licensed under the Open Government Licence v3.0"
            ),
            attribution=str(dataset.get("attribution") or "crown-copyright"),
            attribution_text=str(
                dataset.get("attribution-text")
                or "© Crown copyright and database right 2026"
            ),
            source_url=source_url,
            documentation_url=documentation_url,
            source_adapter=source_adapter,
            publisher=publisher_url,
            publisher_id=publisher_id,
            publisher_name=publisher_name,
            confidence=str(dataset.get("confidence") or "observed"),
            wikidata=str(dataset.get("wikidata") or ""),
            wikipedia=str(dataset.get("wikipedia") or ""),
            github_discussion=int(dataset.get("github-discussion") or 0),
            entity_minimum=int(dataset.get("entity-minimum") or 0),
            entity_maximum=int(dataset.get("entity-maximum") or 0),
            consideration=str(dataset.get("consideration") or ""),
            replacement_dataset=str(dataset.get("replacement-dataset") or ""),
            resources=resources,
            alternatives=alternatives,
            tags=sorted({typology, collection, phase, *themes}),
            metadata_created=GENERATED_AT,
            metadata_modified=GENERATED_AT,
            generated_by=GENERATOR_ACTOR,
            status="draft",
            stale_after=STALE_AFTER,
        )
        records.append(record)

        if collection == "historic-england":
            relationships.append(
                OKFPlanningRelationship(
                    source_id=dataset_id,
                    target_id="town-and-country-planning-act-1990",
                    relationship_type="governed-by",
                    note=(
                        "Rule-based catalogue linkage to the principal planning "
                        "legislation represented in this bundle."
                    ),
                )
            )
        elif collection == "local-plan":
            relationships.extend(
                [
                    OKFPlanningRelationship(
                        source_id=dataset_id,
                        target_id="nppf-framework-policy",
                        relationship_type="conforms-to-policy",
                        note="Rule-based linkage for local-plan catalogue records.",
                    ),
                    OKFPlanningRelationship(
                        source_id=dataset_id,
                        target_id="levelling-up-and-regeneration-act-2023",
                        relationship_type="governed-by",
                        note="Rule-based linkage for local-plan catalogue records.",
                    ),
                ]
            )
        elif collection == "design-code":
            relationships.append(
                OKFPlanningRelationship(
                    source_id=dataset_id,
                    target_id="nppf-framework-policy",
                    relationship_type="derived-from-policy",
                    note="Rule-based linkage for design-code catalogue records.",
                )
            )

    records.sort(key=lambda record: record.id)
    existing_ids = {record.id for record in records}
    relationships = sorted(
        (
            relationship
            for relationship in relationships
            if relationship.source_id in existing_ids
            and relationship.target_id in existing_ids
        ),
        key=lambda relationship: (
            relationship.source_id,
            relationship.target_id,
            relationship.relationship_type,
        ),
    )
    return records, relationships


def build_okf_static_search(
    records: list[OKFPlanningRecord], search_dir: str | Path, snapshot_id: str
) -> None:
    """Generate a deterministic ``okf-static-search.v1`` index."""
    search_path = Path(search_dir)
    result_docs: list[dict[str, Any]] = []
    doc_map: dict[str, list[Any]] = {}
    postings_map: dict[str, list[list[int]]] = {}
    prefix_map: dict[str, list[dict[str, Any]]] = {}
    filter_postings: dict[str, dict[str, list[int]]] = {
        key: {}
        for key in ("collection", "licence", "phase", "publisher", "typology")
    }
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }

    for ordinal, record in enumerate(sorted(records, key=lambda item: item.id)):
        result_docs.append(
            {
                "collection": record.collection,
                "name": record.id,
                "open": record.route,
                "ordinal": ordinal,
                "phase": record.phase,
                "publisher": record.publisher_name,
                "publisher_title": record.publisher_name,
                "resource_count": len(record.resources),
                "route": record.route,
                "summary": record.description[:200],
                "title": record.title,
                "typology": record.typology,
            }
        )
        doc_map[str(ordinal)] = [record.route, record.title, 1.0]
        for key, value in (
            ("typology", record.typology),
            ("collection", record.collection),
            ("phase", record.phase),
            ("publisher", record.publisher_name),
            ("licence", record.licence),
        ):
            if value:
                filter_postings[key].setdefault(value, []).append(ordinal)

        title_tokens = set(re.findall(r"[a-z0-9]+", record.title.lower()))
        description_tokens = set(
            re.findall(r"[a-z0-9]+", record.description.lower())
        )
        tag_tokens = set(re.findall(r"[a-z0-9]+", " ".join(record.tags).lower()))
        for token in sorted(title_tokens | description_tokens | tag_tokens):
            if len(token) < 2 or token in stop_words:
                continue
            weight = 1
            mask = 0
            if token in title_tokens:
                weight += 4
                mask |= 1
            if token in tag_tokens:
                weight += 2
                mask |= 2
            postings_map.setdefault(token, []).append([ordinal, weight, mask])

    for token in sorted(postings_map):
        if len(token) >= 3:
            prefix_map.setdefault(token[:3], []).append(
                {
                    "df": len(postings_map[token]),
                    "label": token.title(),
                    "query": token,
                    "token": token,
                }
            )
    for entries in prefix_map.values():
        entries.sort(key=lambda entry: (-entry["df"], entry["token"]))

    _write_json(search_path / "docs-0.json", result_docs)
    _write_json(search_path / "doc-map.json", doc_map)
    _write_json(search_path / "postings-0.json", {"tokens": postings_map})
    _write_json(
        search_path / "lexicon/default.json",
        [
            {
                "df": len(postings_map[token]),
                "postings": "data/search/postings-0.json",
                "token": token,
            }
            for token in sorted(postings_map)
        ],
    )
    _write_json(search_path / "prefixes/default.json", prefix_map)

    filter_entrypoints: dict[str, str] = {}
    for key in sorted(filter_postings):
        values = {
            value: filter_postings[key][value]
            for value in sorted(filter_postings[key])
        }
        _write_json(search_path / f"filters/{key}.json", {"values": values})
        filter_entrypoints[key] = f"data/search/filters/{key}.json"

    _write_json(
        search_path / "manifest.json",
        {
            "counts": {
                "documents": len(records),
                "max_postings_per_token": max(
                    (len(postings) for postings in postings_map.values()),
                    default=0,
                ),
                "postings": sum(len(postings) for postings in postings_map.values()),
                "tokens": len(postings_map),
            },
            "entrypoints": {
                "doc_map": "data/search/doc-map.json",
                "filter_postings": filter_entrypoints,
                "lexicon": {"_": "data/search/lexicon/default.json"},
                "postings": ["data/search/postings-0.json"],
                "prefixes": {"_": "data/search/prefixes/default.json"},
                "result_docs": ["data/search/docs-0.json"],
            },
            "lexicon_shard_length": 2,
            "prefix_min_length": 3,
            "result_doc_chunk_size": 1000,
            "result_limit": 200,
            "schema": "okf-static-search.v1",
            "snapshot": snapshot_id,
            "snapshot_id": snapshot_id,
            "token_min_length": 2,
        },
    )


def _frontmatter(fields: dict[str, Any]) -> str:
    """Serialize a human-readable YAML subset whose values are valid JSON."""
    lines = ["---"]
    for key, value in fields.items():
        lines.append(
            f"{key}: {json.dumps(value, ensure_ascii=False, separators=(',', ':'))}"
        )
    lines.append("---")
    return "\n".join(lines)


def _concept_path(record: OKFPlanningRecord) -> str:
    return f"concepts/{_slugify(record.typology)}/{_slugify(record.id)}.md"


def _write_markdown_bundle(bundle_dir: Path, records: list[OKFPlanningRecord]) -> None:
    """Write the normative OKF v0.2 Markdown layer."""
    groups: dict[str, list[OKFPlanningRecord]] = {}
    for record in records:
        groups.setdefault(record.typology, []).append(record)
        fields = {
            "type": record.concept_type,
            "title": record.title,
            "description": record.description,
            "resource": record.source_url,
            "tags": record.tags,
            "generated": {
                "by": record.generated_by,
                "at": record.metadata_modified,
            },
            "status": record.status,
            "stale_after": record.stale_after,
            "sources": [record.source_entry],
            "okf_explorer": {
                "collection": record.collection,
                "entity_count": record.entity_count,
                "phase": record.phase,
                "publisher": record.publisher_id,
                "route": record.route,
                "typology": record.typology,
            },
        }
        documentation = ""
        if record.documentation_url != record.source_url:
            documentation = (
                f"\n- [Source documentation]({record.documentation_url})"
            )
        body = f"""{_frontmatter(fields)}

# Overview

{record.description}

# Access

- [Source record or landing page]({record.source_url}){documentation}
- Licence: {record.licence_text}
- Attribution: {record.attribution_text}

# Provenance

This independently generated metadata concept derives from the source record
above.[^source-record] It has not been recorded as human-verified, and it does
not imply endorsement by the source publisher.

[^source-record]: {record.source_entry["title"]}
"""
        _write_text(bundle_dir / _concept_path(record), body)

    root_lines = [
        _frontmatter({"okf_version": "0.2"}),
        "",
        "# UK Planning & Housing Data",
        "",
        "A frozen, independently generated metadata catalogue. The Markdown files "
        "are the normative OKF v0.2 layer; JSON, YAML-LD, DCAT, PROV, SKOS, "
        "federation and Explorer files are additive projections.",
        "",
        "# Concepts",
        "",
        "* [Planning concepts](concepts/) - browse by source typology.",
        "",
        "# Extensions",
        "",
        "* [OKF Explorer descriptor](okf-explorer.json)",
        "* [Semantic YAML-LD projection](okf-bundle.yamlld)",
        "* [JSON-LD projection](okf-bundle.jsonld)",
        "* [Integrity catalogue](checksums.json)",
    ]
    _write_text(bundle_dir / "index.md", "\n".join(root_lines))
    _write_text(
        bundle_dir / "log.md",
        """# Bundle Update Log

## 2026-07-25

* **Migration**: Published the normative OKF v0.2 Markdown layer and retained
  the Explorer, YAML-LD, DCAT, SKOS, PROV and federation projections.
""",
    )

    concept_index = ["# Planning Concepts", ""]
    for typology in sorted(groups):
        slug = _slugify(typology)
        concept_index.append(
            f"* [{typology.replace('-', ' ').title()}]({slug}/) - "
            f"{len(groups[typology])} concepts."
        )
        group_lines = [f"# {typology.replace('-', ' ').title()}", ""]
        for record in sorted(groups[typology], key=lambda item: item.title.lower()):
            group_lines.append(
                f"* [{record.title}]({_slugify(record.id)}.md) - "
                f"{record.description}"
            )
        _write_text(
            bundle_dir / f"concepts/{slug}/index.md", "\n".join(group_lines)
        )
    _write_text(bundle_dir / "concepts/index.md", "\n".join(concept_index))


def validate_okf_v02_markdown(bundle_dir: str | Path) -> dict[str, Any]:
    """Validate core structure and every optional v0.2 family we emit."""
    root = Path(bundle_dir)
    markdown_files = sorted(root.rglob("*.md"))
    errors: list[str] = []
    checked = 0
    for path in markdown_files:
        if path.name in {"index.md", "log.md"}:
            text = path.read_text(encoding="utf-8")
            body = text
            if path.name == "index.md" and path == root / "index.md":
                if not text.startswith("---\n") or "\n---\n" not in text[4:]:
                    errors.append("index.md: invalid version frontmatter")
                    continue
                block, body = text[4:].split("\n---\n", 1)
                if block.strip() != 'okf_version: "0.2"':
                    errors.append("index.md: root frontmatter may only declare v0.2")
            elif text.startswith("---"):
                errors.append(
                    f"{path.relative_to(root)}: reserved file must not have frontmatter"
                )
            if not any(line.startswith("# ") for line in body.splitlines()):
                errors.append(f"{path.relative_to(root)}: missing title heading")
            if path.name == "log.md":
                for line in body.splitlines():
                    if line.startswith("## "):
                        try:
                            date.fromisoformat(line.removeprefix("## ").strip())
                        except ValueError:
                            errors.append(
                                f"{path.relative_to(root)}: invalid ISO date heading"
                            )
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors.append(f"{path.relative_to(root)}: missing frontmatter")
            continue
        block = text.split("---\n", 2)[1]
        parsed: dict[str, Any] = {}
        for line in block.splitlines():
            if not line.strip():
                continue
            key, separator, raw_value = line.partition(": ")
            if not separator:
                errors.append(
                    f"{path.relative_to(root)}: invalid frontmatter line {line!r}"
                )
                continue
            try:
                parsed[key] = json.loads(raw_value)
            except json.JSONDecodeError:
                errors.append(
                    f"{path.relative_to(root)}: invalid YAML/JSON value for {key}"
                )
        if not isinstance(parsed.get("type"), str) or not parsed["type"].strip():
            errors.append(f"{path.relative_to(root)}: missing non-empty type")
        generated = parsed.get("generated")
        if generated is not None:
            if not isinstance(generated, dict) or not generated.get("by"):
                errors.append(f"{path.relative_to(root)}: invalid generated.by")
            else:
                if not ACTOR_PATTERN.fullmatch(str(generated["by"])):
                    errors.append(
                        f"{path.relative_to(root)}: generated.by violates actor convention"
                    )
                try:
                    if "T" not in str(generated.get("at", "")):
                        raise ValueError
                    datetime.fromisoformat(
                        str(generated.get("at", "")).replace("Z", "+00:00")
                    )
                except ValueError:
                    errors.append(f"{path.relative_to(root)}: invalid generated.at")
        sources = parsed.get("sources")
        if sources is not None:
            if not isinstance(sources, list):
                errors.append(f"{path.relative_to(root)}: invalid sources")
            else:
                for index, source in enumerate(sources):
                    if not isinstance(source, dict) or not source.get("resource"):
                        errors.append(
                            f"{path.relative_to(root)}: invalid sources[{index}]"
                        )
                        continue
                    author = source.get("author")
                    if author and not ACTOR_PATTERN.fullmatch(str(author)):
                        errors.append(
                            f"{path.relative_to(root)}: invalid sources[{index}].author"
                        )
                    usage_count = source.get("usage_count")
                    if usage_count is not None and (
                        isinstance(usage_count, bool)
                        or not isinstance(usage_count, int)
                        or usage_count < 0
                    ):
                        errors.append(
                            f"{path.relative_to(root)}: invalid sources[{index}].usage_count"
                        )
                    if source.get("last_modified"):
                        try:
                            date.fromisoformat(str(source["last_modified"]))
                        except ValueError:
                            errors.append(
                                f"{path.relative_to(root)}: invalid "
                                f"sources[{index}].last_modified"
                            )
        if parsed.get("status", "stable") not in {"draft", "stable", "deprecated"}:
            errors.append(f"{path.relative_to(root)}: invalid status")
        if parsed.get("stale_after"):
            try:
                date.fromisoformat(str(parsed["stale_after"]))
            except ValueError:
                errors.append(f"{path.relative_to(root)}: invalid stale_after")
        verified = parsed.get("verified")
        if verified is not None:
            events = [verified] if isinstance(verified, dict) else verified
            if not isinstance(events, list) or any(
                not isinstance(event, dict)
                or not event.get("by")
                or not event.get("at")
                for event in events
            ):
                errors.append(f"{path.relative_to(root)}: invalid verified")
            else:
                for index, event in enumerate(events):
                    if not ACTOR_PATTERN.fullmatch(str(event["by"])):
                        errors.append(
                            f"{path.relative_to(root)}: invalid verified[{index}].by"
                        )
                    try:
                        if "T" not in str(event["at"]):
                            raise ValueError
                        datetime.fromisoformat(
                            str(event["at"]).replace("Z", "+00:00")
                        )
                    except ValueError:
                        errors.append(
                            f"{path.relative_to(root)}: invalid verified[{index}].at"
                        )
    root_index = root / "index.md"
    if not root_index.exists() or 'okf_version: "0.2"' not in root_index.read_text(
        encoding="utf-8"
    ):
        errors.append("index.md: missing okf_version 0.2 declaration")
    return {
        "checked_concepts": checked,
        "errors": errors,
        "okf_version": "0.2",
        "status": "conformant" if not errors else "non-conformant",
    }


def _write_shards(
    directory: Path, stem: str, rows: list[dict[str, Any]], shard_size: int
) -> list[str]:
    paths: list[str] = []
    for offset in range(0, len(rows), shard_size):
        shard_number = len(paths)
        relative = f"data/{stem}-{shard_number}.json"
        _write_json(directory / f"{stem}-{shard_number}.json", rows[offset : offset + shard_size])
        paths.append(relative)
    return paths


def _publisher_rows(records: list[OKFPlanningRecord]) -> list[dict[str, Any]]:
    grouped: dict[str, list[OKFPlanningRecord]] = {}
    for record in records:
        grouped.setdefault(record.publisher_id, []).append(record)
    return [
        {
            "dataset_count": len(grouped[publisher_id]),
            "description": (
                "Source publisher attribution carried from frozen metadata. "
                "It does not imply endorsement of this OKF bundle."
            ),
            "id": publisher_id,
            "name": publisher_id,
            "resource_count": sum(
                len(record.resources) for record in grouped[publisher_id]
            ),
            "route": f"publisher/{publisher_id}",
            "title": grouped[publisher_id][0].publisher_name,
            "url": grouped[publisher_id][0].publisher,
        }
        for publisher_id in sorted(grouped)
    ]


def _resource_rows(records: list[OKFPlanningRecord]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        for position, resource in enumerate(record.resources):
            name = _slugify(resource.id)
            rows.append(
                {
                    "dataset": record.id,
                    "dataset_id": record.id,
                    "dataset_route": record.route,
                    "description": resource.description,
                    "documentation": record.documentation_url,
                    "format": resource.format,
                    "host": re.sub(r"^https?://", "", resource.url).split("/", 1)[0],
                    "id": resource.id,
                    "media_type": resource.media_type,
                    "name": name,
                    "position": position,
                    "publisher": record.publisher_id,
                    "resource_type": resource.resource_type,
                    "route": f"resource/{name}",
                    "title": resource.title,
                    "url": resource.url,
                }
            )
    return sorted(rows, key=lambda row: (row["dataset"], row["position"], row["id"]))


def _metadata_evaluation(records: list[OKFPlanningRecord]) -> dict[str, Any]:
    checks = {
        "description": lambda record: bool(record.description),
        "licence": lambda record: bool(record.licence and record.licence_text),
        "publisher": lambda record: bool(record.publisher and record.publisher_name),
        "resources": lambda record: bool(record.resources),
        "source": lambda record: bool(record.source_url),
        "themes": lambda record: bool(record.themes),
        "title": lambda record: bool(record.title),
        "typology": lambda record: bool(record.typology),
    }
    field_counts = {
        field: sum(1 for record in records if check(record))
        for field, check in checks.items()
    }
    possible = len(records) * len(checks)
    present = sum(field_counts.values())
    return {
        "audited_records": len(records),
        "field_counts": field_counts,
        "field_presence_ratio": round(present / possible, 4) if possible else 0,
        "label": "metadata-field-presence",
        "possible_fields": possible,
        "present_fields": present,
        "quality_evaluated": False,
        "quality_score": None,
        "schema": "okf-evaluation-report.v1",
        "statistical_accuracy_evaluated": False,
        "status": "measured",
        "warning": (
            "This score measures presence of declared metadata fields. It is not "
            "a certification of source accuracy, completeness or fitness for use."
        ),
    }


def _facet_analysis(
    key: str, label: str, values: Counter[str], record_count: int, control: str
) -> dict[str, Any]:
    probabilities = [count / record_count for count in values.values()] if record_count else []
    entropy = -sum(probability * math.log2(probability) for probability in probabilities)
    max_entropy = math.log2(len(values)) if len(values) > 1 else 0
    top_share = max(values.values(), default=0) / record_count if record_count else 0
    return {
        "cardinality": len(values),
        "coverage": 1.0 if record_count else 0,
        "entropy": round(entropy / max_entropy, 4) if max_entropy else 0,
        "expected_reduction": round(1 - top_share, 4),
        "key": key,
        "label": label,
        "recommendation": "primary",
        "recommended_control": control,
        "top_share": round(top_share, 4),
        "values": [
            {"count": count, "value": value}
            for value, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def _source_snapshot_metadata(cache_dir: str | None) -> list[dict[str, Any]]:
    if not cache_dir:
        return []
    source_root = Path(cache_dir)
    sources = []
    for filename, url in (
        ("dataset.json", "https://www.planning.data.gov.uk/dataset.json"),
        ("organisation.json", "https://www.planning.data.gov.uk/organisation.json"),
    ):
        path = source_root / filename
        if path.exists():
            sources.append(
                {
                    "captured_at": SOURCE_CAPTURED_AT,
                    "captured_at_basis": "declared snapshot release timestamp",
                    "path": f"source/{filename}",
                    "resource": url,
                    "sha256": compute_sha256(path),
                }
            )
    return sources


def _generated_files(bundle_dir: Path) -> list[Path]:
    files = [
        bundle_dir / filename
        for filename in GENERATED_ROOT_FILES
        if filename != "checksums.json" and (bundle_dir / filename).is_file()
    ]
    for directory in GENERATED_DIRECTORIES:
        root = bundle_dir / directory
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(bundle_dir).as_posix())


def build_bundle(
    output_dir: str,
    base_url: str = DEFAULT_BASE_URL,
    cache_dir: str | None = None,
) -> dict[str, str]:
    """Build the normative v0.2 Markdown bundle and all extension projections."""
    if not cache_dir:
        raise ValueError("A pinned source cache is required for an offline-safe build")
    base_url = base_url.rstrip("/") + "/"
    bundle_dir = Path(output_dir).resolve()
    bundle_dir.mkdir(parents=True, exist_ok=True)
    _clean_generated_output(bundle_dir)

    raw_datasets = get_all_augmented_datasets(cache_dir)
    records, relationships = build_okf_planning_records(raw_datasets, base_url)
    if not records:
        raise ValueError("The pinned source snapshot produced no planning records")
    logger.info(
        "Normalized %d records and %d rule-derived relationships",
        len(records),
        len(relationships),
    )

    _write_markdown_bundle(bundle_dir, records)
    conformance = validate_okf_v02_markdown(bundle_dir)
    if conformance["status"] != "conformant":
        raise ValueError(f"Generated non-conformant OKF bundle: {conformance['errors']}")

    context = {
        "@context": {
            "Catalog": "dcat:Catalog",
            "Dataset": "dcat:Dataset",
            "Resource": "dcat:Resource",
            "alignmentClaim": "okf:alignmentClaim",
            "bundlePublisher": {"@id": "okf:bundlePublisher", "@type": "@id"},
            "conformsTo": {"@id": "dct:conformsTo", "@type": "@id"},
            "contextSet": {"@id": "okf:contextSet", "@type": "@id"},
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
            "description": "dct:description",
            "identifier": "dct:identifier",
            "landingPage": {"@id": "dcat:landingPage", "@type": "@id"},
            "nonEndorsementStatement": "okf:nonEndorsementStatement",
            "notEndorsedBySource": "okf:notEndorsedBySource",
            "okf": f"{base_url}vocab/",
            "okfEntrypoint": {"@id": "okf:entrypoint", "@type": "@id"},
            "okfVersion": "okf:version",
            "prov": "http://www.w3.org/ns/prov#",
            "record": {"@id": "dcat:resource", "@type": "@id"},
            "reviewedBy": {"@id": "okf:reviewedBy", "@type": "@id"},
            "semanticAuthority": {"@id": "okf:semanticAuthority", "@type": "@id"},
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "sourcePublisher": {"@id": "okf:sourcePublisher", "@type": "@id"},
            "title": "dct:title",
            "wasAttributedTo": {"@id": "prov:wasAttributedTo", "@type": "@id"},
            "wasDerivedFrom": {"@id": "prov:wasDerivedFrom", "@type": "@id"},
            "wasGeneratedBy": {"@id": "prov:wasGeneratedBy", "@type": "@id"},
        }
    }
    _write_json(bundle_dir / "context/okf-planning.jsonld", context)

    semantic_graph = {
        "@context": f"{base_url}context/okf-planning.jsonld",
        "@id": f"{base_url}okf-bundle.jsonld",
        "@type": "Catalog",
        "alignmentClaim": (
            "This is an additive semantic mapping of the generated catalogue. "
            "It does not certify upstream services against DCAT, PROV or SKOS."
        ),
        "bundlePublisher": base_url,
        "conformsTo": [
            OKF_SPEC,
            "https://www.w3.org/TR/vocab-dcat-3/",
            "https://www.w3.org/TR/prov-o/",
            "https://www.w3.org/TR/skos-reference/",
        ],
        "contextSet": "data/governance/context-set.json",
        "okfEntrypoint": "index.md",
        "okfVersion": "0.2",
        "description": (
            "Additive YAML-LD/JSON-LD projection of the normative OKF v0.2 "
            "Markdown planning catalogue."
        ),
        "record": [record.to_yaml_ld_dict(base_url) for record in records],
        "semanticAuthority": base_url,
        "title": "UK Planning & Housing Data semantic projection",
    }
    _write_json(bundle_dir / "okf-bundle.yamlld", semantic_graph)
    _write_json(bundle_dir / "okf-bundle.jsonld", semantic_graph)

    dataset_rows = [record.to_explorer_dict(base_url) for record in records]
    resource_rows = _resource_rows(records)
    publisher_rows = _publisher_rows(records)
    relationship_rows = [
        relationship.to_explorer_dict() for relationship in relationships
    ]
    data_dir = bundle_dir / "data"
    dataset_shards = _write_shards(data_dir, "datasets", dataset_rows, 50)
    resource_shards = _write_shards(data_dir, "resources", resource_rows, 100)
    publisher_shards = _write_shards(data_dir, "publishers", publisher_rows, 100)
    relationship_shards = _write_shards(
        data_dir, "relationships", relationship_rows, 100
    )
    build_okf_static_search(records, data_dir / "search", SNAPSHOT_ID)

    typology_counts = Counter(record.typology for record in records)
    collection_counts = Counter(record.collection for record in records)
    phase_counts = Counter(record.phase for record in records)
    publisher_counts = Counter(record.publisher_name for record in records)
    source_counts = Counter(record.source_adapter for record in records)
    relationship_counts = Counter(
        relationship.relationship_type for relationship in relationships
    )
    format_counts = Counter(resource["format"] for resource in resource_rows)
    total_entities = sum(record.entity_count for record in records)
    counts = {
        "datasets": len(records),
        "entities": total_entities,
        "publishers": len(publisher_rows),
        "records": len(records),
        "relationships": len(relationship_rows),
        "resources": len(resource_rows),
        "sources": len(source_counts),
    }
    record_type_counts = Counter(record.concept_type for record in records)
    overview = {
        "counts": counts,
        "coverage": "data/coverage/ledger.json",
        "evaluation": "data/evaluation/report.json",
        "recordTypeCounts": dict(sorted(record_type_counts.items())),
        "schema": "okf-planning-overview.v1",
        "snapshot": SNAPSHOT_ID,
        "snapshotId": SNAPSHOT_ID,
        "sourceCounts": dict(sorted(source_counts.items())),
        "status": "draft-demonstrator",
        "title": "UK Planning & Housing Data OKF",
    }
    _write_json(data_dir / "overview.json", overview)

    manifest = {
        "chunks": {
            "datasets": dataset_shards,
            "publishers": publisher_shards,
            "records": dataset_shards,
            "relationships": relationship_shards,
            "resources": resource_shards,
        },
        "counts": {
            **counts,
            "dataset_shards": len(dataset_shards),
            "publisher_shards": len(publisher_shards),
            "relationship_shards": len(relationship_shards),
            "resource_shards": len(resource_shards),
        },
        "generated": {"at": GENERATED_AT, "by": GENERATOR_ACTOR},
        "okf_version": "0.2",
        "indexes": {
            "analysis": "data/analysis/overview.json",
            "context_set": "data/governance/context-set.json",
            "coverage": "data/coverage/ledger.json",
            "evaluation": "data/evaluation/report.json",
            "governance": "data/governance/release.json",
            "integrity": "checksums.json",
            "overview": "data/overview.json",
            "reconciliation": "data/reconciliation/report.json",
            "search": "data/search/manifest.json",
        },
        "schema": "okf-explorer-data-manifest.v1",
        "snapshot": SNAPSHOT_ID,
        "title": "UK Planning & Housing Data Manifest",
    }
    _write_json(data_dir / "manifest.json", manifest)

    hierarchy_labels = {
        "category": "Categories & Designations",
        "document": "Planning Documents",
        "geography": "Spatial Geographies",
        "legal-instrument": "Legal Instruments",
        "organisation": "Planning Organisations",
        "policy": "National Policies",
    }
    analysis = {
        "facet_analysis": [
            _facet_analysis("typology", "Typology", typology_counts, len(records), "chips"),
            _facet_analysis(
                "collection",
                "Collection",
                collection_counts,
                len(records),
                "searchable-select",
            ),
            _facet_analysis(
                "phase", "Development Phase", phase_counts, len(records), "chips"
            ),
            _facet_analysis(
                "publisher",
                "Provider / Publisher",
                publisher_counts,
                len(records),
                "searchable-select",
            ),
        ],
        "generated": {"at": GENERATED_AT, "by": GENERATOR_ACTOR},
        "graph_overview": {
            "edges": [
                {
                    "count": typology_counts[typology],
                    "label": "contains",
                    "source": "corpus/overview",
                    "target": f"facet/typology/{typology}",
                }
                for typology in sorted(hierarchy_labels)
            ],
            "nodes": [
                {
                    "count": len(records),
                    "id": "corpus/overview",
                    "label": "UK Planning Data",
                    "type": "corpus",
                },
                *[
                    {
                        "count": typology_counts[typology],
                        "id": f"facet/typology/{typology}",
                        "label": hierarchy_labels[typology],
                        "type": "typology",
                    }
                    for typology in sorted(hierarchy_labels)
                ],
            ],
        },
        "hierarchies": [
            {
                "facet": "typology",
                "id": "typology-hierarchy",
                "label": "Planning Typology Hierarchy",
                "levels": ["typology"],
                "values": [
                    {
                        "count": typology_counts[typology],
                        "id": typology,
                        "label": hierarchy_labels[typology],
                        "route": f"facet/typology/{typology}",
                        "value": typology,
                    }
                    for typology in (
                        "geography",
                        "category",
                        "organisation",
                        "document",
                        "legal-instrument",
                        "policy",
                    )
                ],
            }
        ],
        "narrative": {
            "body": (
                "A frozen metadata discovery plane for planning datasets and "
                "source-published policy, legislation and guidance."
            ),
            "title": "UK Planning Data Discovery OKF",
        },
        "recordTypeCounts": overview["recordTypeCounts"],
        "relationship_overview": {
            "types": [
                {"count": count, "kind": kind}
                for kind, count in sorted(relationship_counts.items())
            ]
        },
        "resource_overview": {
            "distributions": {
                "format": [
                    {"count": count, "value": value}
                    for value, count in sorted(format_counts.items())
                ]
            },
            "total_resources": len(resource_rows),
        },
        "schema": "okf-explorer-analysis.v1",
        "sourceCounts": overview["sourceCounts"],
        "summary": {
            "description": (
                "Metadata-only discovery layer with a normative OKF v0.2 "
                "Markdown core and additive Explorer/semantic projections."
            ),
            "record_count": len(records),
            "relationship_count": len(relationships),
            "resource_count": len(resource_rows),
            "title": "UK Planning & Housing Data OKF",
        },
        "timeline_overview": {
            "buckets": [
                {
                    "count": len(records),
                    "id": "2026",
                    "label": "2026 snapshot",
                    "route": "timeline/2026",
                }
            ]
        },
    }
    _write_json(data_dir / "analysis/overview.json", analysis)

    standards = {
        "certification_performed": False,
        "conformance": {
            "dcat_3": {
                "status": "mapped-not-certified",
                "evidence": "okf-bundle.jsonld",
            },
            "okf_0_2": conformance,
            "prov_o": {
                "status": "mapped-not-certified",
                "evidence": "okf-bundle.jsonld",
            },
            "skos": {
                "status": "context-present-not-evaluated",
                "evidence": "context/okf-planning.jsonld",
            },
        },
        "evaluated_records": len(records),
        "schema": "okf-standards-evaluation.v1",
        "warning": "Semantic mappings are interoperability claims, not certification.",
    }
    _write_json(data_dir / "standards/evaluation.json", standards)

    evaluation = _metadata_evaluation(records)
    _write_json(data_dir / "evaluation/report.json", evaluation)
    _write_json(
        data_dir / "coverage/ledger.json",
        {
            "coverage_scope": (
                "Records present in the frozen Planning Data England snapshot "
                "plus ten explicitly curated source records."
            ),
            "dataset_count": len(records),
            "geographic_claim": "England where declared by the source catalogue",
            "schema": "okf-coverage-ledger.v1",
            "score": None,
            "status": "descriptive-not-evaluated",
            "themes_covered": sorted(collection_counts),
        },
    )
    _write_json(
        data_dir / "reconciliation/report.json",
        {
            "method": "deterministic collection rules",
            "reconciled_entities": None,
            "relationship_count": len(relationships),
            "schema": "okf-reconciliation-report.v1",
            "status": "not-evaluated",
            "warning": (
                "Rule-derived catalogue relationships are published, but no "
                "entity reconciliation or human review is claimed."
            ),
        },
    )
    _write_json(
        data_dir / "governance/context-set.json",
        {
            "contexts": [
                {"id": "dcat", "url": "http://www.w3.org/ns/dcat#"},
                {"id": "prov", "url": "http://www.w3.org/ns/prov#"},
                {"id": "skos", "url": "http://www.w3.org/2004/02/skos/core#"},
            ],
            "schema": "okf-context-set.v1",
        },
    )
    _write_json(
        data_dir / "governance/release.json",
        {
            "generated": {"at": GENERATED_AT, "by": GENERATOR_ACTOR},
            "freshness_policy": {
                "basis": (
                    "Project-declared quarterly review boundary for this "
                    "independent frozen metadata snapshot."
                ),
                "stale_after": STALE_AFTER,
                "status": "declared",
            },
            "integrity": {
                "algorithm": "sha256",
                "catalogue": "checksums.json",
                "scope": "generated bundle files excluding checksums.json",
            },
            "licence": (
                "https://github.com/chris-page-gov/okf-planning/blob/main/LICENSE"
            ),
            "okf_spec": OKF_SPEC,
            "publisher": "https://github.com/chris-page-gov/okf-planning",
            "schema": "okf-governance-release.v1",
            "snapshot_id": SNAPSHOT_ID,
            "source_snapshots": _source_snapshot_metadata(cache_dir),
            "status": "draft",
            "verified": [],
        },
    )
    _write_json(
        data_dir / "planning/mcp-bindings.json",
        {
            "authorises_execution": False,
            "execution_available": False,
            "kind": "capability-discovery-metadata",
            "schema": "okf-mcp-bindings.v1",
            "server": None,
            "tools": [
                {
                    "description": "Potential downstream entity lookup capability.",
                    "name": "get_planning_entity",
                    "read_only": True,
                    "status": "candidate-only",
                },
                {
                    "description": "Potential downstream planning search capability.",
                    "name": "search_planning_entities",
                    "read_only": True,
                    "status": "candidate-only",
                },
            ],
            "warning": (
                "This file is discovery metadata, not an MCP server or executable "
                "binding. It declares no transport, endpoint or authorization."
            ),
        },
    )
    _write_json(
        data_dir / "planning/spatial-index.json",
        {
            "default_crs": "EPSG:27700",
            "extent_england": {
                "xmax": 655600,
                "xmin": 82600,
                "ymax": 657500,
                "ymin": 5300,
            },
            "geometry_included": False,
            "schema": "okf-spatial-index.v1",
            "status": "descriptive",
            "supported_crs": ["EPSG:27700", "EPSG:4326"],
        },
    )

    descriptor = {
        "@context": (
            "https://chris-page-gov.github.io/okf-explorer/"
            "profile/bundle-wiki/v1/context.jsonld"
        ),
        "@id": f"{base_url}okf-explorer.json",
        "authority": {
            "bundlePublisher": {
                "id": "https://github.com/chris-page-gov/okf-planning",
                "name": "OKF Planning project",
                "url": "https://github.com/chris-page-gov/okf-planning",
            },
            "decisionAuthority": "accountable external person or institution",
            "nonEndorsementStatement": (
                "This experimental metadata bundle is independently published "
                "and is not endorsed by its source producers."
            ),
            "notEndorsedBySource": True,
            "operationalAuthority": "external live-data services",
            "reviewedBy": [],
            "semanticAuthority": {
                "id": "https://github.com/chris-page-gov/okf-planning",
                "name": "OKF Planning project",
                "scope": "this generated bundle release only",
                "url": "https://github.com/chris-page-gov/okf-planning",
            },
        },
        "counts": counts,
        "description": (
            "OKF v0.2 Markdown bundle for UK planning metadata with additive "
            "Explorer, YAML-LD, DCAT, PROV, SKOS and discovery extensions."
        ),
        "display": {
            "facets": {
                "default_mode": "suggested",
                "order": ["typology", "collection", "phase", "publisher", "licence"],
                "pinned": ["typology", "collection", "phase"],
            }
        },
        "entrypoints": {
            "analysis_overview": "data/analysis/overview.json",
            "context_set": "data/governance/context-set.json",
            "coverage": "data/coverage/ledger.json",
            "data_manifest": "data/manifest.json",
            "evaluation": "data/evaluation/report.json",
            "governance": "data/governance/release.json",
            "integrity": "checksums.json",
            "mcp_bindings": "data/planning/mcp-bindings.json",
            "okf_root": "index.md",
            "overview_index": "data/overview.json",
            "reconciliation": "data/reconciliation/report.json",
            "search_manifest": "data/search/manifest.json",
            "spatial_index": "data/planning/spatial-index.json",
            "standards": "data/standards/evaluation.json",
            "viewer": "https://chris-page-gov.github.io/okf-explorer/",
        },
        "extensions": {
            "okf-core.v0.2": {
                "conformance": "data/standards/evaluation.json",
                "entrypoint": "okf_root",
                "status": conformance["status"],
                "verified_events_recorded": False,
            },
            "okf-explorer-analysis.v1": {
                "entrypoint": "analysis_overview",
                "mode": "external",
            },
            "okf-governed-knowledge-contract.v1": {
                "authorises_execution": False,
                "entrypoint": "governance",
                "status": "experimental",
            },
            "okf-mcp-binding.v1": {
                "entrypoint": "mcp_bindings",
                "execution_available": False,
                "status": "discovery-only",
            },
            "okf-planning-discovery.v1": {
                "compare_alternatives": True,
                "mode": "metadata-only-demonstrator",
                "not_endorsed_by_source": True,
            },
            "okf-semantic-projection.v1": {
                "certification_claimed": False,
                "formats": ["YAML-LD", "JSON-LD", "DCAT", "PROV", "SKOS"],
            },
        },
        "generated": {"at": GENERATED_AT, "by": GENERATOR_ACTOR},
        "generated_at": GENERATED_AT,
        "kind": "okf-large-corpus",
        "okf_version": "0.2",
        "core_conformance": "OKF v0.2 Markdown concept layer",
        "performance": {
            "full_record_hydration": "lazy",
            "relationship_hydration": "lazy",
            "search": "static worker-compatible shards",
            "startup_mode": "overview-first",
        },
        "profile": (
            "https://chris-page-gov.github.io/okf-explorer/"
            "profile/bundle-wiki/v1/"
        ),
        "publisher": "https://github.com/chris-page-gov/okf-planning",
        "rights": {
            "recordLevel": True,
            "statement": (
                "Rights and attribution are carried per record from the source "
                "snapshot or curated source entry."
            ),
            "status": "mixed-record-level",
        },
        "schema": "okf-explorer-large-corpus.v1",
        "semantic_descriptor": f"{base_url}okf-bundle.yamlld",
        "snapshot": SNAPSHOT_ID,
        "sources": [
            {
                "id": "planning-data-snapshot",
                "resource": (
                    "https://www.planning.data.gov.uk/dataset.json"
                ),
                "title": "Planning Data England dataset catalogue snapshot",
            }
        ],
        "status": "draft-demonstrator",
        "title": "UK Planning & Housing Data OKF",
        "version": "0.2.0",
        "vocabulary": {
            "publisher_plural": "publishers",
            "publisher_singular": "publisher",
            "record_plural": "Planning metadata records",
            "record_singular": "Planning metadata record",
            "resource_plural": "access resources",
            "resource_singular": "access resource",
            "search_placeholder": (
                "Search UK planning datasets, policy, legislation, and guidance"
            ),
        },
    }
    _write_json(bundle_dir / "okf-explorer.json", descriptor)

    checksums = {
        path.relative_to(bundle_dir).as_posix(): compute_sha256(path)
        for path in _generated_files(bundle_dir)
    }
    _write_json(bundle_dir / "checksums.json", checksums)
    logger.info(
        "Bundle build complete with %d checksummed generated files", len(checksums)
    )
    return checksums
