# OKF Planning demo guide

## Human discovery page

Serve [`bundle/`](../bundle/) over HTTP or open the
[published page](https://chris-page-gov.github.io/okf-planning/). The page:

- loads every dataset shard declared by `data/manifest.json`;
- shows manifest-derived record, entity, relationship and publisher counts;
- supports combined text and typology filtering;
- assigns all source-derived strings with `textContent`;
- can display the normative root Markdown, Explorer descriptor, semantic
  YAML-LD extension and checksum catalogue;
- has no runtime dependency on external font services.

The page is a view over a frozen snapshot. Search is local static search, not a
live query against Planning Data England.

## OKF Explorer

Use the [direct Explorer link](https://chris-page-gov.github.io/okf-explorer/?bundle=https%3A%2F%2Fchris-page-gov.github.io%2Fokf-planning%2Fokf-explorer.json).

Expected behavior:

1. Overview loads without hydrating every record.
2. Search results open `dataset/<id>`, not a lifecycle value such as `alpha`.
3. Opening Reader or Resources hydrates top-level array shards.
4. Resources show source landing/documentation pages only.
5. Graph relationships are visibly labelled as inferred rule-derived links.
6. Trust and lifecycle views show the draft, unverified snapshot state and
   absolute staleness boundary.

## Machine entry points

- Normative OKF root:
  `https://chris-page-gov.github.io/okf-planning/index.md`
- Explorer descriptor:
  `https://chris-page-gov.github.io/okf-planning/okf-explorer.json`
- Data manifest:
  `https://chris-page-gov.github.io/okf-planning/data/manifest.json`
- Discovery-only MCP metadata:
  `https://chris-page-gov.github.io/okf-planning/data/planning/mcp-bindings.json`

The MCP metadata is not an MCP server. A downstream implementation must supply
transport, input schemas, authorization and a source-declared executable
resource before anything can run.

## Offline validation

```sh
python3 scripts/build_bundle.py
python3 scripts/check_okf.py
pytest
```

The normal build reads `source/dataset.json`; it does not silently fall back to
live acquisition. Use `scripts/acquire_planning_data.py` only for an intentional
snapshot refresh.
