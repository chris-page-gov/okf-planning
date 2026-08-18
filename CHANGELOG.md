# Changelog

All notable changes to `okf-planning` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

### Added

- Added `okf.publication.json` and `okf.semantic.json` to separate publication
  lifecycle controls from the draft planning graph's meaning.
- Added local publication-contract, documentation-lockstep and Pages-candidate
  checks, with regression tests and a plain-English method guide.

### Changed

- Removed the redundant second bundle build from the Pages workflow. The
  workflow now uploads the one generated, validated and diff-checked candidate.
- Isolated pull request cancellation by ref, kept protected-main publication
  serial and non-cancelling, pinned action revisions and added job timeouts.
- Made the cross-hash-seed determinism subprocess use the repository's explicit
  source path instead of depending on an editable installation side effect.

### Publication boundary

- Exact-commit real-browser verification remains migration work. Existing
  public links are not verified deployment evidence until that gate passes for
  the deployed commit.

## [0.2.0] — 2026-07-25

### Added

- Published 230 planning metadata concepts as a normative OKF v0.2 Markdown
  hierarchy with structured `sources`, `generated`, lifecycle metadata and an
  explicit unverified trust state.
- Retained YAML-LD, JSON-LD, DCAT 3, PROV-O, SKOS, federation, static search and
  Explorer representations as documented extensions.
- Added source-specific policy, legislation, guidance, heritage and environment
  records alongside the frozen 220-record Planning Data England catalogue.
- Added canonical top-level array shards for datasets, resources, publishers
  and rule-derived relationships.
- Added conformance, integrity, offline-safety, cross-contract and
  cross-hash-seed determinism tests.

### Changed

- Corrected search results so `open` contains the canonical dataset route.
- Removed constructed JSON, CSV and GeoJSON endpoints; resources now contain
  only declared source landing and documentation pages.
- Assigned curated records to their actual source publishers.
- Replaced claimed certifications, entity reconciliation and hard-coded quality
  scores with measured, qualified or explicitly not-evaluated evidence.
- Made source acquisition atomic and normal builds pinned-snapshot-only.
- Updated the discovery page to hydrate every manifest shard, derive its counts
  from data and render source strings without HTML interpolation.
