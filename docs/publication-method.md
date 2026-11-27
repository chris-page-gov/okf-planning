# Build and publication method

This independent planning metadata pilot remains draft and unverified. Source
acquisition is separate from the offline build. The source snapshot remains
25 July 2026, and the review boundary of 25 October 2026 remains overdue.
Migrating the format on 24 November does not refresh sources or grant approval.

The [semantic contract](../okf.semantic.json) governs meaning. The separate
[publication contract](../okf.publication.json) governs build, assurance and
promotion. Review declared commands against `AGENTS.md` and repository code
before execution; contracts do not execute commands.

## Source and generated boundaries

The two frozen JSON files under `source/` and curated records in
`src/okf_planning/sources.py` are compiler inputs. The core generator owns
`bundle/concepts/`, `bundle/context/`, `bundle/data/` and its declared root
outputs. Markdown remains normative for concept text and provenance.
`bundle/index.html`, `app.js` and `styles.css` are authored UI assets.
The reviewed `source/snapshot-lock.json` binds both frozen input digests and the
declared source and generation identity. A changed payload fails before output
cleanup; an authorised future refresh requires a new reviewed snapshot identity
and lock, rather than retaining July dates for new material.

The companion generator reads frozen concepts and qualified links, the authored
question under `walkthroughs/`, and the versioned profile under `profiles/`.
It writes one question walkthrough, responsive SVGs, complete AI context,
source evidence, discovery files, native journeys and profile copies. It must
not alter the original concept or relationship bytes.

The core checksum file covers the core generator’s output set. The packaging-only
`publication.json` binds the exact Git commit and SHA-256 of every served file,
including authored UI, companions and `.nojekyll`. Retain its digest separately.
Packaging copies reviewed bytes without another semantic build.
Packaging rejects a dirty source tree. An explicit `--allow-dirty` is reserved
for local diagnostics and marks the manifest ineligible for release.

## Acceptance and promotion

1. Sync locked Python 3.12.11 and run the offline core and companion builds.
   Check Core conformance, roles, relationship profile, integrity, full source
   identity, documentation and changelog lockstep.
2. Check the downloaded candidate's original manifest digest, source revision,
   OKF version and declared file bytes before installing the Reader or browser.
   Verify the pinned Explorer revision and deterministic runtime tree. Run all
   four native record, graph and derivation cases and the actual question link on desktop
   and mobile, including original source cards and reloads.
3. Require zero browser errors, no AA accessibility violations, no horizontal
   overflow, readable diagrams and complete HTTP byte comparison. Preserve
   failed receipts and diagnose them before claiming acceptance.
4. The protected `build` check aggregates core and browser jobs and fails if
   either fails. Upload and deploy the same exact candidate; neither deployment
   nor a failed live check authorises a semantic rebuild.
5. Download the exact main Actions ZIP, verify membership and hashes, then run
   public question journeys and complete served-byte checks. The public verifier
   has a 55-second deadline and reports failures immediately.
6. For a formal release, annotate a version tag at that accepted revision.
   Attach the unchanged candidate ZIP, public acceptance report and checksums
   to a draft. Download and compare every asset before publication, then repeat
   public access and digest checks afterwards. Record actual immutability and
   verify the platform’s signed attestation when available.

Annotated Git tags and signed release attestations are separate evidence.
Historical Core 0.2 tags remain unchanged. Technical acceptance establishes
neither current policy, proposal compliance, human review, source endorsement
nor whole-estate completion.
