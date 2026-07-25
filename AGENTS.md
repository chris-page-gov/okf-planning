# Technical Repository Guide for AI Agents

Welcome to `okg-planning`. This repository houses the Open Knowledge Format (OKF) Bundle v0.2 for UK Planning & Housing Data.

## Repository Layout

- `bundle/`: Published static OKF bundle assets for GitHub Pages.
  - `okf-bundle.yamlld`: Canonical YAML-LD semantic descriptor.
  - `okf-bundle.jsonld`: Compacted/expanded JSON-LD descriptor.
  - `okf-explorer.json`: OKF Explorer v0.4+ runtime descriptor.
  - `context/okf-planning.jsonld`: Pinned local JSON-LD context.
  - `data/`: Sharded data plane (manifest, overview, records, search, standards, governance, reconciliation, coverage, analysis, planning extensions).
  - `checksums.json`: SHA-256 integrity map.
  - `index.html`, `app.js`, `styles.css`: Human landing page & GUI.
- `src/okf_planning/`: Core Python package for normalization, model definitions, bundle building, MCP selection broker, and evaluation suite.
- `scripts/`: Data acquisition and CLI build entry points.
- `tests/`: Automated unit tests.
- `docs/`: Technical specifications.

## Guidance for AI Coding Agents

1. **Deterministic Builds**: Always run `python3 scripts/build_bundle.py` after modifying `src/okf_planning/` to update `bundle/` artifacts and `checksums.json`.
2. **OKF 0.2 Standard Rules**: Maintain DCAT 3, SKOS, PROV-O terms, non-endorsement statements, and valid JSON-LD contexts.
3. **No Live Execution in Metadata Layer**: The bundle is frozen metadata only. Live execution must go through downstream live APIs.
