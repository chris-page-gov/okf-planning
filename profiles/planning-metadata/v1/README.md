# Planning metadata profile v1

Profile identity: `https://chris-page-gov.github.io/okf-planning/profile/planning-metadata/v1/`.
Implementation date: 24 November 2026. Core standard: OKF 0.3, announced on
18 November 2026. Resolve the pinned specification and historical versions through
[Explorer's standards register](https://github.com/chris-page-gov/okf-explorer/blob/main/docs/okf-standards.md)
and [machine register](https://github.com/chris-page-gov/okf-explorer/blob/main/registry/okf-standards.json).

This profile describes this producer's existing frozen planning catalogue. It
adds DCAT, SKOS, PROV-O, rule-derived links and a sharded Explorer representation
to the normative Markdown. It does not claim Bundle Wiki v1 or v2 assertion
conformance or external certification. The retained Bundle Wiki v1 context is a
structural term mapping, rather than evidence of adoption of that profile.

The source model contains 230 stable record identities, 240 declared source pages,
eight publishers and 40 links. Record Markdown remains authoritative for its
provenance and text. The checked-in source envelopes and curated source register
are the deterministic compiler inputs. No upstream acquisition is part of this
format migration.

Each relationship retains `source`, `target`, `kind`, `confidence`,
`evidence_type` and any `note`. `confidence: inferred` and
`evidence_type: deterministic-collection-rule` describe a catalogue rule. A link
label such as `governed-by` does not establish that a specific legal provision
applies to a site, proposal or person. The migration adds no official mandate,
permission, identity reconciliation or human verification event.

Typed Markdown records are Core concepts. Navigation indexes and logs are not
concepts. The semantic projection assigns explicit Core roles to resource,
organisation, vocabulary, bundle and other extension declarations. Qualified
source identities, direction and original predicate meanings remain intact.
Resolve the reviewed local JSON-LD context without fetching arbitrary contexts.

The source snapshot is project-declared as 25 July 2026. Historical record
generation remains `okf-planning/0.2.0` at `2026-07-25T11:25:00Z`.
The review boundary remains `2026-10-25` and is overdue at this implementation
date. Current projection version and format-migration dates are separate from
those source events. `status: draft` and the absence of `verified` remain visible.

Source-specific rights and attribution travel with records. Repository code is
MIT-licensed; this profile grants no additional rights over publisher material.
Metadata field-presence scores do not establish accuracy, completeness, current
source availability or fitness for a planning decision. The MCP component selects
declared metadata; it declares no executable service or authorisation boundary.

Acceptance requires complete source/core/graph integrity, preservation of the
frozen record and relationship identities, a distinct source-linked question and
negative controls, real Explorer and AI source access, and exact deployed-byte
verification. Historical Core 0.2 material retains its own version and evidence.
