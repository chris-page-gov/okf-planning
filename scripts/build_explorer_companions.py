"""Build one source-linked question and complete AI context for the planning bundle."""

from __future__ import annotations

import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import textwrap
from urllib.parse import quote

import yaml

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "bundle"
BASE = "https://chris-page-gov.github.io/okf-planning/"
READER = "https://chris-page-gov.github.io/okf-explorer/explore/"


def encode(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()


def read_concepts(bundle: Path) -> dict:
    concepts = {}
    for path in sorted((bundle / "concepts").rglob("*.md")):
        raw = path.read_bytes()
        if not raw.startswith(b"---\n"):
            continue
        head, separator, body = raw[4:].partition(b"\n---\n")
        if not separator:
            raise ValueError(f"Unclosed front matter: {path.name}")
        metadata = yaml.safe_load(head)
        if not isinstance(metadata, dict):
            raise ValueError("Front matter must be an object")
        route = metadata["okf_explorer"]["route"]
        if route in concepts:
            raise ValueError(f"Duplicate concept route: {route}")
        concepts[route] = {
            "route": route,
            "path": path.relative_to(bundle).as_posix(),
            "sha256": sha256(raw).hexdigest(),
            "front_matter": metadata,
            "body": body.decode(),
            **metadata,
        }
    return concepts


def selected_edges(spec: dict, concepts: dict, edges: list) -> list:
    selected = []
    for route in spec["source_routes"]:
        found = [
            row
            for row in edges
            if row["source"] == route
            and row["target"] == spec["target_route"]
            and row["kind"] == spec["kind"]
        ]
        if len(found) != 1:
            raise ValueError(f"Expected exactly one question edge for {route}")
        row = found[0]
        if (
            row["confidence"] != "inferred"
            or row["evidence_type"] != "deterministic-collection-rule"
        ):
            raise ValueError("Walkthrough cannot promote an inferred relationship")
        if row["source"] not in concepts or row["target"] not in concepts:
            raise ValueError("Question edge has a missing source concept")
        selected.append(row)
    return selected


def diagram(spec: dict, concepts: dict, edges: list, *, mobile: bool) -> bytes:
    width, height = (390, 1100) if mobile else (980, 600)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Design-code records and their inferred policy links</title>',
        '<desc id="desc">Three source records link to the same National Planning Policy Framework record. Every edge is inferred by a deterministic collection rule, not a compliance decision.</desc>',
        '<defs><marker id="arrow" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="#355a7b"/></marker></defs>',
        f'<rect width="{width}" height="{height}" fill="#f4f7fb"/>',
    ]

    def text(x: int, y: int, value: str, columns: int, size: int = 16):
        for i, line in enumerate(textwrap.wrap(value, columns)):
            out.append(
                f'<text x="{x}" y="{y + i * 22}" font-family="system-ui,sans-serif" font-size="{size}" fill="#172b4d">{escape(line)}</text>'
            )

    text(20, 35, "Source discovery, with qualified links", 30 if mobile else 70, 21)
    text(
        20,
        95 if mobile else 70,
        "July 2026 snapshot · October review overdue",
        36 if mobile else 80,
        14,
    )
    target = concepts[spec["target_route"]]["title"]
    for i, edge in enumerate(edges):
        source = concepts[edge["source"]]["title"]
        if mobile:
            y = 145 + i * 280
            for box_y in (y, y + 155):
                out.append(
                    f'<rect x="20" y="{box_y}" width="350" height="90" rx="12" fill="white" stroke="#355a7b"/>'
                )
            text(35, y + 32, source, 32, 17)
            text(35, y + 181, target, 34, 15)
            out.append(
                f'<path d="M195 {y + 96} V{y + 147}" stroke="#355a7b" stroke-width="2" marker-end="url(#arrow)"/>'
            )
            text(22, y + 120, "derived-from-policy", 30, 13)
            text(22, y + 141, "inferred · collection rule", 31, 12)
        else:
            y = 125 + i * 130
            out.append(
                f'<rect x="20" y="{y}" width="340" height="100" rx="12" fill="white" stroke="#355a7b"/>'
            )
            text(35, y + 35, source, 31, 18)
            out.append(
                f'<path d="M365 {y + 50} H520 L575 320" stroke="#355a7b" stroke-width="2" marker-end="url(#arrow)"/>'
            )
            text(375, y + 23, "derived-from-policy", 28, 13)
    if not mobile:
        out.append(
            '<rect x="585" y="260" width="375" height="140" rx="12" fill="white" stroke="#355a7b"/>'
        )
        text(600, 295, target, 32, 19)
        text(600, 370, "All three edges are inferred", 37, 14)
    text(
        20,
        height - (75 if mobile else 48),
        "A link does not establish compliance.",
        36 if mobile else 90,
        15,
    )
    text(
        20,
        height - 25,
        "Repeated NPPF boxes are the same record."
        if mobile
        else "Per-record sources and rights remain authoritative.",
        44 if mobile else 90,
        13,
    )
    out.append("</svg>")
    return ("\n".join(out) + "\n").encode()


def build(bundle: Path = BUNDLE) -> dict[str, bytes]:
    spec = json.loads((ROOT / "walkthroughs/design-code.json").read_bytes())
    descriptor_raw = (bundle / "okf-explorer.json").read_bytes()
    descriptor = json.loads(descriptor_raw)
    assert descriptor["okf_version"] == "0.3" and descriptor["version"] == "0.3.0"
    concepts = read_concepts(bundle)
    edges = [
        row
        for p in sorted((bundle / "data").glob("relationships-*.json"))
        for row in json.loads(p.read_bytes())
    ]
    if len(concepts) != 230 or len(edges) != 40:
        raise ValueError("Unexpected source coverage")
    selected = selected_edges(spec, concepts, edges)
    primary = concepts[spec["primary_route"]]
    reader_url = (
        READER
        + "?bundle="
        + quote(descriptor["@id"], safe="")
        + "&view=reader#"
        + spec["primary_route"]
    )
    sources = [
        {key: row[key] for key in ("route", "path", "title", "resource", "sha256")}
        for row in concepts.values()
    ]
    evidence = {
        "schema": "okf-planning-walkthrough-evidence.v1",
        **spec,
        "descriptor_sha256": sha256(descriptor_raw).hexdigest(),
        "primary_title": primary["title"],
        "primary_source_url": primary["resource"],
        "reader_url": reader_url,
        "source_concepts": sources,
        "question_edges": selected,
        "coverage": {"concepts": 230, "core_assertions": 0, "domain_relationships": 40},
        "source_snapshot": descriptor["snapshot"],
        "format_migration": descriptor["format_migration"],
    }
    context = {
        "schema": "okf-planning-ai-context.v1",
        "okf_version": "0.3",
        "semantic_profile": descriptor["profile"],
        "source_snapshot": descriptor["snapshot"],
        "concepts": list(concepts.values()),
        "core_assertions": [],
        "domain_relationships": edges,
        "question": spec,
        "source_identity": sources,
        "limits": spec["limitations"],
        "execution_available": False,
    }
    semantic_raw = (bundle / "okf-bundle.jsonld").read_bytes()
    context["semantic_graph"] = json.loads(semantic_raw)
    context["semantic_graph_identity"] = {
        "path": "okf-bundle.jsonld",
        "sha256": sha256(semantic_raw).hexdigest(),
        "authority": "generated projection; concept Markdown and frozen source inputs remain authoritative",
    }
    identity = {key: descriptor[key] for key in ("schema", "version", "snapshot")}
    identity["id"] = descriptor["@id"]
    journeys = []
    for route in (spec["primary_route"], spec["target_route"]):
        title = concepts[route]["title"]
        journeys.append(
            {
                "id": route.replace("/", "-"),
                "actions": [
                    {"type": "goto", "hash": "#" + route, "params": {"view": "reader"}},
                    {
                        "type": "wait_for",
                        "selector": ".right-panel h2:text-is(" + json.dumps(title) + ")",
                    },
                ],
                "assertions": [
                    {"type": "text", "selector": ".right-panel", "includes": title},
                    {"type": "console_clean"},
                ],
            }
        )
    journeys.append(
        {
            "id": "inferred-policy-graph-traversal",
            "actions": [
                {
                    "type": "goto",
                    "hash": "#" + spec["primary_route"],
                    "params": {"view": "graph", "graph.workspace": "1"},
                },
                {
                    "type": "wait_for",
                    "selector": 'svg.graph [data-route="' + spec["target_route"] + '"] .node-hit',
                },
                {
                    "type": "click",
                    "selector": 'svg.graph [data-route="' + spec["target_route"] + '"] .node-hit',
                },
                {"type": "click", "selector": 'button:has-text("Exit expanded graph")'},
            ],
            "assertions": [
                {"type": "url_hash", "equals": "#" + spec["target_route"]},
                {"type": "console_clean"},
            ],
        }
    )
    journeys.append(
        {
            "id": "policy-edge-keeps-inferred-derivation",
            "actions": [
                {
                    "type": "goto",
                    "hash": "#" + spec["primary_route"],
                    "params": {"view": "graph", "graph.workspace": "1"},
                },
                {
                    "type": "wait_for",
                    "selector": 'svg.graph .edge-hit[data-edge^="dataset/design-code>dataset/nppf-framework-policy:"]',
                },
                {
                    "type": "click",
                    "selector": 'svg.graph .edge-hit[data-edge^="dataset/design-code>dataset/nppf-framework-policy:"]',
                },
                {"type": "click", "selector": 'button:has-text("Exit expanded graph")'},
                {"type": "click", "selector": '.right-panel [role="tab"]:text-is("Relationship")'},
            ],
            "assertions": [
                {
                    "type": "attribute",
                    "selector": ".right-panel [data-relationship-authority]",
                    "name": "data-relationship-authority",
                    "equals": "derived",
                },
                {"type": "text", "selector": ".right-panel", "includes": "inferred"},
                {
                    "type": "text",
                    "selector": ".right-panel",
                    "includes": "deterministic-collection-rule",
                },
                {
                    "type": "text",
                    "selector": ".right-panel",
                    "includes": "Rule-based linkage for design-code catalogue records.",
                },
                {"type": "console_clean"},
            ],
        }
    )
    source_links = "".join(
        '<li><a href="'
        + escape(concepts[route]["path"], quote=True)
        + '">'
        + escape(concepts[route]["title"])
        + '</a> · <a href="'
        + escape(concepts[route]["resource"], quote=True)
        + '">Original source</a></li>'
        for route in [*spec["source_routes"], spec["target_route"]]
    )
    limitations = "".join("<li>" + escape(t) + "</li>" for t in spec["limitations"])
    negatives = "".join("<li>" + escape(t) + "</li>" for t in spec["negative_controls"])
    page = f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Design-code evidence walkthrough</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'/%3E"><style>body{{margin:0;background:#f4f7fb;color:#172b4d;font:1.05rem/1.6 system-ui,sans-serif}}main{{max-width:70rem;margin:auto;padding:1.2rem}}a{{color:#154a80}}h1{{font-size:clamp(1.6rem,4vw,2.5rem);line-height:1.25}}figure{{margin:1.5rem 0}}img{{display:block;width:100%;height:auto}}.notice{{padding:1rem;border-left:5px solid #924900;background:#fff4dc}}code{{overflow-wrap:anywhere}}li{{margin:.55rem 0}}</style></head><body><main><a href="index.html">Planning bundle</a><h1>{escape(spec["question"])}</h1><p>{escape(spec["answer"])}</p><p class="notice">Frozen source: 25 July 2026. Review overdue since 25 October 2026. Format migrated on 24 November 2026; source records were not refreshed.</p><p><a data-reader-link="primary" href="{escape(reader_url, quote=True)}">Inspect Design code in the Reader</a></p><figure><picture><source media="(max-width:600px)" srcset="walkthrough-mobile.svg"><img src="walkthrough-desktop.svg" alt="Three design-code records link to the same NPPF record through inferred collection rules."></picture><figcaption>Three actual domain edges, with their original qualification. <a href="walkthrough-desktop.svg">Open the full diagram</a>.</figcaption></figure><h2>Follow the evidence</h2><ol><li>Open Design code in the Reader and inspect its source and metadata.</li><li>Open the graph and follow the inferred policy link to the NPPF record.</li><li>Read the original source and check current policy, local circumstances and rights before making any decision.</li></ol><ul>{source_links}</ul><h2>Limits and rights</h2><ul>{limitations}</ul><h2>Unsupported conclusions</h2><ul>{negatives}</ul><h2>Use this bundle with an AI client</h2><p>Give the client <a href="llms.txt">the discovery instructions</a> or <a href="ai-context.json">the complete deterministic context</a>. The context contains all 230 concepts, their exact YAML front matter and Markdown bodies, source hashes and all 40 qualified domain links. Retrieve it without model inference; cite source paths and preserve qualifications when answering. No model answer is certified by this technical check.</p><p><a href="okf-bundle.yamlld">YAML-LD graph</a> · <a href="profile/planning-metadata/v1/README.md">Versioned domain profile</a> · <a href="walkthrough-evidence.json">Machine evidence</a> · <a href="https://github.com/chris-page-gov/okf-explorer/blob/main/docs/okf-standards.md">Current and historical standards</a></p></main></body></html>'''
    page = page.replace("profile/planning-metadata/v1/README.md", "profile/planning-metadata/v1/")
    files = {
        "walkthrough.html": page.encode(),
        "walkthrough-desktop.svg": diagram(spec, concepts, selected, mobile=False),
        "walkthrough-mobile.svg": diagram(spec, concepts, selected, mobile=True),
        "walkthrough-evidence.json": encode(evidence),
        "ai-context.json": encode(context),
        "reader-journeys.json": encode(
            {
                "schema": "okf-explorer-journeys.v1",
                "bundle_descriptor": "okf-explorer.json",
                "expected_identity": identity,
                "journeys": journeys,
            }
        ),
        "llms.txt": (
            "# UK planning metadata bundle\n\nCore: 0.3. Profile: "
            + descriptor["profile"]
            + "\nDescriptor: "
            + BASE
            + "okf-explorer.json\nComplete context: "
            + BASE
            + "ai-context.json\nYAML-LD graph: "
            + BASE
            + "okf-bundle.yamlld\nWalkthrough: "
            + BASE
            + "walkthrough.html\n\n230 draft concepts; 0 Core assertions; 40 inferred domain relationships. Source: 25 July 2026. Review overdue: 25 October 2026. No policy compliance, source endorsement, executable service or access permission is established. Cite exact source paths and keep all qualifications.\n"
        ).encode(),
        ".well-known/okf.json": encode(
            {
                "schema": "okf-planning-discovery.v1",
                "okf_version": "0.3",
                "descriptor": BASE + "okf-explorer.json",
                "ai_context": BASE + "ai-context.json",
                "walkthrough": BASE + "walkthrough.html",
                "semantic_profile": descriptor["profile"],
                "execution_available": False,
            }
        ),
    }
    files["profile/planning-metadata/v1/relationship.schema.json"] = (
        ROOT / "profiles/planning-metadata/v1/relationship.schema.json"
    ).read_bytes()
    profile = (ROOT / "profiles/planning-metadata/v1/README.md").read_text()
    files["profile/planning-metadata/v1/index.html"] = (
        """<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Planning metadata profile v1</title><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'/%3E"><style>body{max-width:65rem;margin:auto;padding:1rem;font:1rem/1.6 system-ui,sans-serif;color:#172b4d}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}a{color:#154a80}</style></head><body><main><h1>Planning metadata profile v1</h1><pre>"""
        + escape(profile)
        + """</pre><p><a href="relationship.schema.json">Relationship schema</a> · <a href="../../../walkthrough.html">Question walkthrough</a> · <a href="https://github.com/chris-page-gov/okf-explorer/blob/main/docs/okf-standards.md">Standards register</a></p></main></body></html>"""
    ).encode()
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = build()
    # Retire only the exact former companion copy; profile prose is ancillary
    # HTML so it cannot be mistaken for an additional typed Markdown concept.
    old = BUNDLE / "profile/planning-metadata/v1/README.md"
    if old.exists():
        if args.check:
            raise SystemExit("Retired generated profile Markdown remains")
        if old.read_bytes() != (ROOT / "profiles/planning-metadata/v1/README.md").read_bytes():
            raise SystemExit("Unrecognised old profile copy")
        old.unlink()
    for name, data in files.items():
        path = BUNDLE / name
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit("Stale companion: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(
        f"Planning companions {'checked' if args.check else 'built'}: {len(files)} files; 230 concepts, 40 domain links, one question"
    )


if __name__ == "__main__":
    main()
