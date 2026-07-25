# OKF Planning Metadata Model (OKF 0.2)

The OKF Planning metadata model maps raw planning data and policy entities into RDF DCAT 3, SKOS, PROV-O, and RDF Data Cube terms.

## Terms & Mappings

| Field | RDF Predicate | Description |
| --- | --- | --- |
| `id` | `dct:identifier` | Unique record ID (e.g. `conservation-area`, `nppf-framework-policy`) |
| `title` | `dct:title` | Human-readable title |
| `description` | `dct:description` | Detailed text summary |
| `landingPage` | `dcat:landingPage` | Live source or documentation page |
| `sourcePublisher` | `okf:sourcePublisher` | Original data publisher URI |
| `bundlePublisher` | `okf:bundlePublisher` | OKF bundle maintainer URI |
| `semanticAuthority` | `okf:semanticAuthority` | Semantic mapping authority URI |
| `wasAttributedTo` | `prov:wasAttributedTo` | Provenance attribution |
| `wasDerivedFrom` | `prov:wasDerivedFrom` | Source dataset derivation link |
| `wasGeneratedBy` | `prov:wasGeneratedBy` | Release metadata URI |
