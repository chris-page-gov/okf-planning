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

Expected behaviour:

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
transport, input schemas, authorisation and a source-declared executable
resource before anything can run.

## Offline validation

```sh
uv run --locked python scripts/build_bundle.py
uv run --locked python scripts/check_okf.py
uv run --locked --extra test pytest
```

The normal build reads `source/dataset.json`; it does not silently fall back to
live acquisition. Use `scripts/acquire_planning_data.py` only for an intentional
snapshot refresh.


## Complex question walkthrough

Open [the design-code question](../bundle/walkthrough.html), read its source and
review dates, then follow the primary Reader link. Inspect Design code, expand
Overview to see its original source URL and draft lifecycle, and use the graph
to follow the inferred policy link to the NPPF record. Reload and check that
the selected record and source remain available. Repeat on a narrow screen
using the Details panel.

The diagram uses three real `derived-from-policy` links. Its mobile layout
repeats the same NPPF target for legibility; it does not create three policies.
Every link retains inferred confidence and collection-rule derivation. The
walkthrough rejects a compliance decision, current-policy claim or executable
service inference. Source pages were not refreshed in November. AI clients use
`ai-context.json` for all 230 source concepts and all 40 links; the question’s
three displayed edges are an illustrative traversal, not the entire graph.
Technical client access does not certify a model’s answer.
