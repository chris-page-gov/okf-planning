# OKF Planning Bundle v0.2 Demo Guide

This guide walks through human and automated AI agent interaction with the OKF Bundle for UK Planning & Housing Data.

## 1. Human Discovery Page & Embedded Viewer

Open `bundle/index.html` in your web browser. You will see:
- Real-time search across 230 datasets, policies, and statutory instruments.
- Facet filtering by typology (`geography`, `category`, `organisation`, `document`, `legal-instrument`, `policy`, `timetable`).
- Direct action button: **Open in OKF Explorer**, which preloads `okf-explorer.json` into OKF Explorer v0.4+.
- Schema syntax tabs for inspecting canonical `okf-bundle.yamlld`, `okf-bundle.jsonld`, and `checksums.json`.

## 2. Machine & AI Agent Access

AI agents (such as Antigravity, Claude, ChatGPT, or custom MCP clients) can access:
- **Descriptor**: `https://chris-page-gov.github.io/okg-planning/okf-explorer.json`
- **YAML-LD**: `https://chris-page-gov.github.io/okg-planning/okf-bundle.yamlld`
- **Data Manifest**: `https://chris-page-gov.github.io/okg-planning/data/manifest.json`
- **MCP Selection Bindings**: `https://chris-page-gov.github.io/okg-planning/data/planning/mcp-bindings.json`
