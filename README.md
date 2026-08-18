# OKF Planning

`okf-planning` is an independent, metadata-only discovery bundle for public
planning and housing information in England. Its frozen source plane combines
the [Planning Data England catalogue](https://www.planning.data.gov.uk/) with
ten explicitly curated policy, legislation, guidance, heritage and environment
records.

The generated [`bundle/`](bundle/) is conformant with
[Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/SPEC.md):
the normative bundle is a hierarchy of Markdown concepts with YAML
frontmatter. JSON, YAML-LD, DCAT 3, PROV-O, SKOS, static search, federation,
integrity and OKF Explorer files are additive project extensions. They are not
part of the OKF core specification and do not replace the Markdown layer.

The bundle is a draft, unverified independent publication. It does not imply
endorsement by MHCLG or any source publisher.

## Entry points

| Purpose | Repository file | Public URL |
| --- | --- | --- |
| Normative OKF root | [`bundle/index.md`](bundle/index.md) | [`index.md`](https://chris-page-gov.github.io/okf-planning/index.md) |
| Human discovery page | [`bundle/index.html`](bundle/index.html) | [OKF Planning](https://chris-page-gov.github.io/okf-planning/) |
| Open in OKF Explorer | — | [Explorer link](https://chris-page-gov.github.io/okf-explorer/?bundle=https%3A%2F%2Fchris-page-gov.github.io%2Fokf-planning%2Fokf-explorer.json) |
| Explorer descriptor | [`bundle/okf-explorer.json`](bundle/okf-explorer.json) | [`okf-explorer.json`](https://chris-page-gov.github.io/okf-planning/okf-explorer.json) |
| Explorer data manifest | [`bundle/data/manifest.json`](bundle/data/manifest.json) | [`data/manifest.json`](https://chris-page-gov.github.io/okf-planning/data/manifest.json) |
| Semantic YAML-LD projection | [`bundle/okf-bundle.yamlld`](bundle/okf-bundle.yamlld) | [`okf-bundle.yamlld`](https://chris-page-gov.github.io/okf-planning/okf-bundle.yamlld) |
| JSON-LD projection | [`bundle/okf-bundle.jsonld`](bundle/okf-bundle.jsonld) | [`okf-bundle.jsonld`](https://chris-page-gov.github.io/okf-planning/okf-bundle.jsonld) |
| Integrity catalogue | [`bundle/checksums.json`](bundle/checksums.json) | [`checksums.json`](https://chris-page-gov.github.io/okf-planning/checksums.json) |

## Snapshot and trust

The checked-in Planning Data source files are a governed snapshot, not a live
API mirror. The release records their SHA-256 digests and the project-declared
snapshot timestamp in
[`bundle/data/governance/release.json`](bundle/data/governance/release.json).
Each generated concept has:

- `generated.by` and `generated.at`;
- a source-specific `sources` entry;
- `status: draft`;
- a project-declared quarterly `stale_after` review boundary, which describes
  this independent snapshot rather than the freshness of an upstream service;
- no `verified` field, so its derived OKF trust tier is **unverified**.

Source landing pages may change after the snapshot. The bundle carries them for
discovery and does not manufacture per-record JSON, CSV or GeoJSON endpoints.

The current snapshot contains 230 records, 240 declared source pages, 8 source
publishers and 40 rule-derived relationships. Entity counts are carried from
the frozen catalogue or curated entries, have not been independently validated,
and must not be read as a bundle completeness score.

## Explorer projection

The Explorer manifest uses top-level array shards for datasets, resources,
publishers and relationships. Search result `open` values are canonical record
routes. All shards, the Markdown core and semantic projections are covered by
[`checksums.json`](bundle/checksums.json).

The MCP file is discovery metadata only. It declares no server, transport,
authorisation mechanism or executable endpoint. `PlanningMCPBroker` resolves
only resources actually declared in the bundle.

See [the metadata model](docs/metadata-model.md) and
[the demo guide](docs/demo-guide.md) for the core/extension boundary and UI
contract.

## Build and validation

Normal builds are offline and require the checked-in source snapshot:

```sh
python3 scripts/build_bundle.py
python3 scripts/check_okf.py
pytest
```

To deliberately refresh both source files from Planning Data England:

```sh
python3 scripts/acquire_planning_data.py
python3 scripts/build_bundle.py
python3 scripts/check_okf.py
```

Acquisition fetches and validates both payloads before replacing either
checked-in file. A network failure leaves the existing snapshot untouched.

CI rebuilds the bundle once, runs the conformance and integrity checks, and
fails when generated files are not synchronised. The checked candidate is
uploaded without a second bundle build.

## Build and publication lifecycle

[`okf.publication.json`](okf.publication.json) is the machine-readable
publication contract. It maps the frozen and curated source family to the
generated semantic, Explorer, integrity and Pages planes. The separate
[`okf.semantic.json`](okf.semantic.json) records graph meaning and its limits.

The contract's command strings are untrusted data: review them against
`AGENTS.md` and the repository code before execution. Run its local checks with:

```sh
python3 scripts/check_publication_contract.py
python3 scripts/check_documentation_lockstep.py
```

The [build and publication method](docs/publication-method.md) explains the
authored and generated boundaries, the single-build Pages candidate and the
current assurance gap. An exact-commit real-browser receipt is not yet
integrated, so the public entry points above must not be treated as verified
deployment evidence for a particular commit.

## Rights

Source-specific licence and attribution statements are carried on records.
Repository code is licensed under the [MIT License](LICENSE). No single bundle
licence overrides the rights declared by source publishers.
