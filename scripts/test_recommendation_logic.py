"""Simple smoke test for recommendation bucket rules."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.graph import GaokaoAgentGraph


async def main() -> None:
    """Run the recommendation graph with a sample request and assert buckets."""
    state = {
        "user_id": "u001",
        "province": "Guangdong",
        "subject_type": "physics",
        "score": 625,
        "rank": 12000,
        "preferred_provinces": ["Guangdong", "Beijing", "Shanghai"],
        "preferred_majors": ["Computer Science and Technology", "Software Engineering"],
        "score_analysis": {},
        "retrieved_schools": [],
        "recommended_choices": {"rush": [], "stable": [], "safe": []},
        "study_plan": {},
        "final_answer": "",
    }

    result = await GaokaoAgentGraph().generate_recommendation(state)
    choices = result["recommended_choices"]

    assert choices["rush"], "rush bucket should not be empty"
    assert choices["stable"], "stable bucket should not be empty"
    assert choices["safe"], "safe bucket should not be empty"
    assert all(len(choices[key]) <= 5 for key in ("rush", "stable", "safe"))
    assert all("reason" in item and item["reason"] for group in choices.values() for item in group)
    assert any(item["match"]["province_match"] for group in choices.values() for item in group)
    assert any(item["tags"] for group in choices.values() for item in group)

    print("recommendation logic smoke test passed")
    print(f"rush={len(choices['rush'])}, stable={len(choices['stable'])}, safe={len(choices['safe'])}")


if __name__ == "__main__":
    asyncio.run(main())
