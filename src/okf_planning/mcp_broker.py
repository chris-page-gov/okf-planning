"""Local MCP selection broker for OKF Planning data."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PlanningMCPBroker:
    """Non-executing local MCP broker that prepares selection plans for planning queries."""

    def __init__(self, bundle_dir: str):
        self.bundle_dir = bundle_dir

    def prepare_selection_plan(self, dataset_id: str, query: str | None = None) -> dict[str, Any]:
        """Prepare non-executing candidate plan for live execution by a downstream service."""
        return {
            "status": "candidate_plan_prepared",
            "dataset_id": dataset_id,
            "query": query or "",
            "requires_live_authorization": True,
            "live_endpoint": f"https://www.planning.data.gov.uk/dataset/{dataset_id}.json",
            "candidate_parameters": {
                "dataset": dataset_id,
                "limit": 100,
                "format": "json",
            },
            "instructions": "Pass candidate plan to live planning server for execution after user confirmation.",
        }
