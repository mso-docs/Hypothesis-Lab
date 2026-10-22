"""Researcher-facing assumptions, independent of UI and Bayesian arithmetic."""

from copy import deepcopy
import math


def normalize_setup(workspace: dict) -> dict:
    """Migrate old investigations and derive a prior from the declared source.

    A legacy nonuniform prior is preserved as custom. Historical observations
    are a separate, explicitly documented dataset, never the current counts.
    """
    value = deepcopy(workspace)
    raw = value.get("setup") or {}
    if not isinstance(raw, dict):
        raise ValueError("Analysis setup must be an object")
    prior = value.get("prior") or {"alpha": 1, "beta": 1}
    mode = raw.get(
        "prior_mode", "little" if prior == {"alpha": 1, "beta": 1} else "custom"
    )
    data_mode = raw.get(
        "data_mode", "available" if value.get("trials", 0) else "literature_only"
    )
    if mode not in {"little", "previous", "custom"} or data_mode not in {
        "available",
        "literature_only",
    }:
        raise ValueError("Choose a supported starting assumption and observation mode")
    setup = {
        "data_mode": data_mode,
        "prior_mode": mode,
        "previous_successes": raw.get("previous_successes", 0),
        "previous_trials": raw.get("previous_trials", 0),
        "prior_reference": str(raw.get("prior_reference", ""))[:5000],
        "prior_rationale": str(raw.get("prior_rationale", ""))[:5000],
        "previous_independent": raw.get("previous_independent") is True,
    }
    for key in ("previous_successes", "previous_trials"):
        n = setup[key]
        if (
            isinstance(n, bool)
            or not isinstance(n, (int, float))
            or not math.isfinite(n)
            or n != int(n)
            or not 0 <= n <= 1000000
        ):
            if mode == "previous":
                raise ValueError(
                    "Previous-study counts must be nonnegative whole numbers, up to one million"
                )
            setup[key] = 0
            continue
        setup[key] = int(n)
    if setup["previous_successes"] > setup["previous_trials"]:
        if mode == "previous":
            raise ValueError(
                "Previous-study events cannot exceed its observation count"
            )
        setup["previous_successes"] = setup["previous_trials"] = 0
    if mode == "little":
        prior = {"alpha": 1, "beta": 1}
    elif mode == "previous":
        prior = {
            "alpha": 1 + setup["previous_successes"],
            "beta": 1 + setup["previous_trials"] - setup["previous_successes"],
        }
    value["prior"], value["setup"] = prior, setup
    return value


def missing_setup(workspace: dict) -> list[str]:
    value = normalize_setup(workspace)
    setup = value["setup"]
    missing = []
    if len(value.get("hypothesis", "").strip()) < 10:
        missing.append("Write a research hypothesis")
    if not value.get("success_definition", "").strip():
        missing.append("Define what counts as an event")
    if setup["data_mode"] == "literature_only":
        missing.append("Add quantitative observations when they are available")
    elif not value.get("trials", 0):
        missing.append("Enter a positive observation count")
    if setup["prior_mode"] == "previous":
        if not setup["previous_trials"]:
            missing.append("Enter the previous study's observations")
        if not setup["prior_reference"].strip():
            missing.append("Record the previous study's source")
        if not setup["previous_independent"]:
            missing.append(
                "Confirm the previous observations are independent and comparable"
            )
    return missing


def assumption_summary(workspace: dict) -> str:
    value = normalize_setup(workspace)
    setup = value["setup"]
    if setup["prior_mode"] == "little":
        return "Little previous knowledge: Beta(1,1), equal density across event probabilities. This is a starting assumption, not an assumption-free choice."
    if setup["prior_mode"] == "previous":
        return f"Previous study: Beta(1,1) updated with {setup['previous_successes']} events in {setup['previous_trials']} historical observations. Source: {setup['prior_reference'] or 'not yet recorded'}. Independence and comparability require researcher confirmation."
    return "Custom starting assumption: " + (
        setup["prior_rationale"] or "Parameters preserved; rationale not yet recorded."
    )
