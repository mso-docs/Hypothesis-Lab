"""Application workflows independent of the notebook and presentation layer."""

from copy import deepcopy

from hypothesis_lab import demo, persistence
from hypothesis_lab.retrieval.openalex import extract


def demo_workspace() -> dict:
    """Offline starter: real linked literature and explicitly synthetic counts."""
    return {
        "title": "Extreme heat · guided demo",
        "hypothesis": demo.HYPOTHESIS,
        "notes": demo.NOTES,
        "prior": {"alpha": 2, "beta": 8},
        "trials": 100,
        "events": 20,
        "publications": [paper.model_dump() for paper in demo.PUBLICATIONS],
        "evidence": [e.model_dump() for p in demo.PUBLICATIONS if (e := extract(p))],
        "synthetic": True,
        "is_demo": True,
        "setup": {
            "data_mode": "available",
            "prior_mode": "custom",
            "prior_rationale": "Illustrative Beta(2,8) teaching assumption, not extracted from the papers.",
        },
    }


def new_workspace(title: str = "Untitled investigation") -> dict:
    """Start with an uninformative prior and no entered observations or papers."""
    title = title.strip() or "Untitled investigation"
    return {
        "title": title,
        "hypothesis": "",
        "notes": "# Research notes\n\n## Question\n\n## Methods\n\n## Findings\n",
        "prior": {"alpha": 1, "beta": 1},
        "trials": 0,
        "events": 0,
        "publications": [],
        "evidence": [],
        "synthetic": False,
        "is_demo": False,
        "setup": {"data_mode": "literature_only", "prior_mode": "little"},
    }


def list_workspaces() -> list[str]:
    return persistence.list_investigations()


def save_workspace(title: str, payload: dict) -> None:
    title = title.strip()
    if not title:
        raise ValueError("Give this investigation a name before saving")
    snapshot = deepcopy(payload)
    snapshot["title"] = title
    persistence.save(title, snapshot)


def load_workspace(title: str) -> dict | None:
    return persistence.load(title)
