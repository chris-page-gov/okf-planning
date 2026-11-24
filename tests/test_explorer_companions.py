"""Protect full source coverage and the inferred policy boundary."""

import importlib.util
import json
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "planning_companions", ROOT / "scripts/build_explorer_companions.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_complete_ai_context_preserves_sources_and_qualifications():
    output = module.build()
    context = json.loads(output["ai-context.json"])
    assert len(context["concepts"]) == 230 and len(context["domain_relationships"]) == 40
    assert context["core_assertions"] == [] and context["execution_available"] is False
    semantic_raw = (ROOT / "bundle/okf-bundle.jsonld").read_bytes()
    assert context["semantic_graph_identity"]["sha256"] == sha256(semantic_raw).hexdigest()
    assert context["semantic_graph"] == json.loads(semantic_raw)
    assert all(
        row["status"] == "draft" and row["stale_after"] == "2026-10-25"
        for row in context["concepts"]
    )
    assert all(
        row["confidence"] == "inferred" and row["evidence_type"] == "deterministic-collection-rule"
        for row in context["domain_relationships"]
    )
    assert len({row["route"] for row in context["concepts"]}) == 230
    assert all(
        row["front_matter"]["resource"] == row["resource"] and "[^source-record]" in row["body"]
        for row in context["concepts"]
    )


def test_question_rejects_promoted_or_missing_graph_evidence():
    output = module.build()
    context = json.loads(output["ai-context.json"])
    question = context["question"]
    concepts = {row["route"]: row for row in context["concepts"]}
    edges = context["domain_relationships"]
    selected = module.selected_edges(question, concepts, edges)
    promoted = [dict(row, confidence="official") if row == selected[0] else row for row in edges]
    with pytest.raises(ValueError, match="cannot promote"):
        module.selected_edges(question, concepts, promoted)
    with pytest.raises(ValueError, match="exactly one"):
        module.selected_edges(question, concepts, [row for row in edges if row != selected[0]])


def test_guide_has_real_reader_source_and_no_root_icon_fallback():
    output = module.build()
    html = output["walkthrough.html"].decode()
    evidence = json.loads(output["walkthrough-evidence.json"])
    assert 'data-reader-link="primary"' in html and "&amp;view=reader#dataset/design-code" in html
    assert evidence["primary_source_url"] == "https://www.planning.data.gov.uk/dataset/design-code"
    assert "data:image/svg+xml" in html and "Review overdue" in html
    assert len(evidence["question_edges"]) == 3 and len(evidence["source_concepts"]) == 230


def test_graph_connectors_cannot_default_to_filled_polygons():
    files = module.build()
    for name in ("walkthrough-desktop.svg", "walkthrough-mobile.svg"):
        root = ET.fromstring(files[name])
        connectors = [
            node
            for node in root.iter("{http://www.w3.org/2000/svg}path")
            if "marker-end" in node.attrib
        ]
        assert len(connectors) == 3
        assert all(node.attrib.get("fill") == "none" for node in connectors)
