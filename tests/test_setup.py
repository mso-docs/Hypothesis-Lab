"""Scientific invariants for the approachable setup workflow."""

import pytest
from hypothesis_lab import services
from hypothesis_lab.setup import normalize_setup, missing_setup
from hypothesis_lab.ui.widget import analyze, clean_workspace, report_for
from hypothesis_lab.reporting import markdown


def measured_workspace():
    value = services.new_workspace("Test investigation")
    value.update(
        hypothesis="The event occurs in this sampled population.",
        success_definition="A predefined measurable event",
        events=3,
        trials=10,
    )
    value["setup"]["data_mode"] = "available"
    return value


def test_no_previous_knowledge_derives_uniform_prior_and_calculates_posterior():
    value = measured_workspace()
    value["prior"] = {"alpha": 999, "beta": 1}
    clean = clean_workspace(value)
    assert clean["prior"] == {"alpha": 1, "beta": 1}
    result = analyze(clean)
    assert result["ready"]
    assert (result["alpha"], result["beta"]) == (4, 8)
    assert "not an assumption-free choice" in result["assumption_summary"]


def test_literature_only_excludes_even_previously_entered_counts():
    value = measured_workspace()
    value["setup"]["data_mode"] = "literature_only"
    result = analyze(value)
    assert not result["ready"] and result["trials"] == 0
    report = report_for(value)
    assert report["posterior"] is None and report["observations"] == []
    assert report["model_status"] == "pending"
    assert "No posterior has been calculated" in markdown(report)


def test_previous_study_requires_independence_reference_and_separate_counts():
    value = measured_workspace()
    value["setup"].update(
        prior_mode="previous", previous_trials=20, previous_successes=14
    )
    assert not analyze(value)["ready"]
    value["setup"].update(
        previous_independent=True,
        prior_reference="Independent study DOI and sampling notes",
    )
    clean = clean_workspace(value)
    assert clean["prior"] == {"alpha": 15, "beta": 7}
    result = analyze(clean)
    assert result["ready"]
    assert (result["alpha"], result["beta"]) == (18, 14)
    assert result["trials"] == 10
    assert report_for(clean)["setup"]["previous_trials"] == 20


def test_custom_parameters_and_legacy_saved_assumptions_survive():
    value = measured_workspace()
    value.pop("setup")
    value["prior"] = {"alpha": 2, "beta": 8}
    restored = clean_workspace(value)
    assert restored["setup"]["prior_mode"] == "custom"
    assert restored["prior"] == {"alpha": 2, "beta": 8}
    assert analyze(restored)["alpha"] == 5
    assert value.get("setup") is None


def test_missing_event_definition_keeps_numeric_inference_pending():
    value = measured_workspace()
    value["success_definition"] = ""
    assert not analyze(value)["ready"]
    assert "Define what counts as an event" in missing_setup(value)


@pytest.mark.parametrize(
    "bad",
    [
        {"previous_trials": 5, "previous_successes": 6},
        {"previous_trials": 2.5},
        {"previous_successes": -1},
    ],
)
def test_invalid_historical_counts_are_rejected(bad):
    value = measured_workspace()
    value["setup"].update(prior_mode="previous", **bad)
    with pytest.raises(ValueError):
        normalize_setup(value)


def test_switching_away_from_previous_study_discards_invalid_unused_counts():
    value = measured_workspace()
    value["setup"].update(previous_successes=6, previous_trials=5)
    clean = clean_workspace(value)
    assert clean["prior"] == {"alpha": 1, "beta": 1}
    assert analyze(clean)["ready"]
