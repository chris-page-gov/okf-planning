"""Non-executing discovery helper for planning resources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PlanningMCPBroker:
    """Resolve declared resources without manufacturing live API endpoints."""

    def __init__(self, bundle_dir: str):
        self.bundle_dir = Path(bundle_dir).resolve()

    def _load_resources(self) -> list[dict[str, Any]]:
        manifest_path = self.bundle_dir / "data/manifest.json"
        with open(manifest_path, encoding="utf-8") as source:
            manifest = json.load(source)
        resources: list[dict[str, Any]] = []
        for relative in manifest.get("chunks", {}).get("resources", []):
            path = (self.bundle_dir / relative).resolve()
            if self.bundle_dir not in path.parents:
                raise ValueError(f"Resource shard escapes bundle: {relative}")
            with open(path, encoding="utf-8") as source:
                payload = json.load(source)
            if not isinstance(payload, list):
                raise ValueError(f"Resource shard is not an array: {relative}")
            resources.extend(payload)
        return resources

    def prepare_selection_plan(
        self, dataset_id: str, query: str | None = None
    ) -> dict[str, Any]:
        """Return declared discovery links and an explicit non-execution status."""
        resources = [
            resource
            for resource in self._load_resources()
            if resource.get("dataset") == dataset_id
        ]
        executable = [
            resource
            for resource in resources
            if resource.get("resource_type") in {"api-endpoint", "access-service"}
        ]
        return {
            "candidate_parameters": {
                "dataset": dataset_id,
                "query": query or "",
            },
            "dataset_id": dataset_id,
            "declared_resources": resources,
            "executable_resources": executable,
            "instructions": (
                "Select a source-declared executable resource and obtain any "
                "required authorization in a downstream MCP implementation."
            ),
            "query": query or "",
            "requires_live_authorization": True,
            "status": (
                "candidate_plan_prepared"
                if executable
                else "metadata_only_no_executable_binding"
            ),
        }
