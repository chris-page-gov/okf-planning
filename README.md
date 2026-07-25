# Open Knowledge Format (OKF) Bundle for UK Planning & Housing Data in England

`okg-planning` is a metadata-only discovery layer for public planning and housing data in England, exposed through the Ministry of Housing, Communities & Local Government (**MHCLG**) [Planning and housing data in England Beta API](https://www.planning.data.gov.uk/docs) and augmented with national planning policies, statutory instruments, and spatial environmental designations.

Built on **Open Knowledge Format (OKF) Standard 0.2**, this bundle extends 0.1 by introducing canonical **YAML-LD** (`okf-bundle.yamlld`), DCAT 3 / SKOS / PROV-O semantic graphs, and a GitHub Pages federation model.

---

## Canonical Entry Points (v0.2.0)

| Resource | Link |
| --- | --- |
| **Human Discovery UI** | [index.html](file:///Users/crpage/repos/okg-planning/bundle/index.html) |
| **Open in OKF Explorer** | [OKF Explorer Direct Link](https://chris-page-gov.github.io/okf-explorer/?bundle=https%3A%2F%2Fchris-page-gov.github.io%2Fokg-planning%2Fokf-explorer.json) |
| **OKF Explorer Runtime Descriptor** | [okf-explorer.json](file:///Users/crpage/repos/okg-planning/bundle/okf-explorer.json) |
| **Canonical YAML-LD Bundle (0.2)** | [okf-bundle.yamlld](file:///Users/crpage/repos/okg-planning/bundle/okf-bundle.yamlld) |
| **Expanded JSON-LD Bundle** | [okf-bundle.jsonld](file:///Users/crpage/repos/okg-planning/bundle/okf-bundle.jsonld) |
| **Pinned Local Context** | [okf-planning.jsonld](file:///Users/crpage/repos/okg-planning/bundle/context/okf-planning.jsonld) |
| **Data & Shard Manifest** | [manifest.json](file:///Users/crpage/repos/okg-planning/bundle/data/manifest.json) |
| **Overview Index** | [overview.json](file:///Users/crpage/repos/okg-planning/bundle/data/overview.json) |
| **Search Manifest** | [manifest.json](file:///Users/crpage/repos/okg-planning/bundle/data/search/manifest.json) |
| **Standards Evaluation** | [evaluation.json](file:///Users/crpage/repos/okg-planning/bundle/data/standards/evaluation.json) |
| **Coverage Ledger** | [ledger.json](file:///Users/crpage/repos/okg-planning/bundle/data/coverage/ledger.json) |
| **Cross-Source Reconciliation** | [report.json](file:///Users/crpage/repos/okg-planning/bundle/data/reconciliation/report.json) |
| **Governed Release Metadata** | [release.json](file:///Users/crpage/repos/okg-planning/bundle/data/governance/release.json) |
| **MCP Binding Index** | [mcp-bindings.json](file:///Users/crpage/repos/okg-planning/bundle/data/planning/mcp-bindings.json) |
| **Spatial Index** | [spatial-index.json](file:///Users/crpage/repos/okg-planning/bundle/data/planning/spatial-index.json) |
| **SHA-256 Checksums** | [checksums.json](file:///Users/crpage/repos/okg-planning/bundle/checksums.json) |

---

## Data Scope & Policy Augmentations

The bundle spans **230 metadata records** and over **5.3 million entities** across England:

1. **MHCLG Planning Data API (220 Datasets)**:
   - 104 Spatial Geographies (Conservation Areas, Listed Building Outlines, Tree Preservation Orders, Article 4 Directions, Green Belt, Brownfield Land).
   - 54 Planning Categories & 15 Public Organisations.
   - 11 Document Collections & 5 Statutory Local Plan Timetables.
2. **National Planning Policy Framework (NPPF)**:
   - Housing Delivery Test, Sustainable Development (Para 11), Green Belt Protection, Heritage Assets, Design & Beauty, Biodiversity Net Gain (BNG).
3. **Planning Practice Guidance (PPG)**:
   - Operational guidance across Use Classes (Class E, C3, C4, B2, B8), Permitted Development Rights (PDR), Section 106 agreements, Community Infrastructure Levy (CIL), Viability, EIA, and SHLAA.
4. **Statutory Legislation**:
   - Town and Country Planning Act 1990, Levelling-up and Regeneration Act 2023 (LURA), Town and Country Planning (Use Classes) Order 1987/2020, GPDO 2015.
5. **Cross-Agency Environmental & Heritage Augmentations**:
   - Historic England (National Heritage List for England - NHLE).
   - Environment Agency (Flood Risk Zones 2 & 3).
   - Natural England (SSSIs, Ancient Woodland, BNG Register).
   - Ordnance Survey (OS Open Data / UPRN / USRN).
   - HM Land Registry (INSPIRE Polygons).
   - Planning Inspectorate (PINS Section 78 Appeals & NSIPs).

---

## Build & Validation CLI

Build the static bundle, compute SHA-256 checksums, and execute unit tests:

```bash
# Acquire live snapshot from planning.data.gov.uk
python3 scripts/acquire_planning_data.py

# Build OKF Planning Bundle v0.2
python3 scripts/build_bundle.py

# Run test suite
pytest
```

---

## License

This metadata bundle is published under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) and the [MIT License](LICENSE).
