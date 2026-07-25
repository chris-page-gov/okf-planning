# Changelog

All notable changes to the `okg-planning` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-25

### Added
- Created initial OKF Bundle for UK Planning & Housing Data in England ported to OKF Standard 0.2.
- Ported OKF extensions to 0.2, including canonical YAML-LD (`okf-bundle.yamlld`) and expanded JSON-LD (`okf-bundle.jsonld`).
- Ingested 220 datasets across 11 typologies from `planning.data.gov.uk` (spanning 5.3M+ entities).
- Integrated policy and statutory instrument augmentations for NPPF, Planning Practice Guidance (PPG), Town and Country Planning Act 1990, Levelling-up and Regeneration Act 2023 (LURA), Use Classes Order, and General Permitted Development Order (GPDO).
- Added cross-agency spatial environmental & heritage linkages for Historic England (NHLE), Environment Agency (Flood Risk Zones), Natural England (SSSIs/BNG), Ordnance Survey, Land Registry, and Planning Inspectorate (PINS).
- Built interactive human discovery web application in `bundle/index.html` with dark glassmorphism styling, dataset search, facet filtering, schema viewer, and direct link to OKF Explorer.
- Implemented Python package `okf_planning`, CLI build engine `build_bundle.py`, local MCP selection broker, and completeness evaluation suite.
