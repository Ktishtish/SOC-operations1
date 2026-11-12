"""Load phishing IR training scenarios from disk."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "data" / "scenarios"


@lru_cache(maxsize=1)
def load_all_scenarios() -> dict[str, dict[str, Any]]:
    scenarios: dict[str, dict[str, Any]] = {}
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
            scenarios[data["id"]] = data
    return scenarios


def list_scenario_summaries() -> list[dict[str, Any]]:
    summaries = []
    for scenario in load_all_scenarios().values():
        summaries.append(
            {
                "id": scenario["id"],
                "title": scenario["title"],
                "difficulty": scenario["difficulty"],
                "description": scenario["description"],
                "mitre_tactics": scenario["mitre_tactics"],
                "estimated_minutes": scenario["estimated_minutes"],
                "learning_objectives": scenario["learning_objectives"],
            }
        )
    order = {"beginner": 0, "intermediate": 1, "advanced": 2}
    summaries.sort(key=lambda s: order.get(s["difficulty"], 9))
    return summaries


def get_scenario(scenario_id: str) -> dict[str, Any]:
    scenarios = load_all_scenarios()
    if scenario_id not in scenarios:
        raise KeyError(f"Unknown scenario: {scenario_id}")
    return scenarios[scenario_id]
