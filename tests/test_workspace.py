"""Behavioral contracts for the Python bridge used by the research IDE."""

import asyncio
import json
from copy import deepcopy

import pytest

from hypothesis_lab import persistence, services
from hypothesis_lab.models import Publication
from hypothesis_lab.ui import widget
from hypothesis_lab.ui.widget import (
    Request,
    ResearchWorkspace,
    analyze,
    clean_workspace,
    observations_for,
    report_for,
    starter,
)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "DB_PATH", tmp_path / "investigations.sqlite3")


def dispatch(component, action, **kwargs):
    asyncio.run(component.dispatch(Request(id=action, type=action, **kwargs)))


def test_starter_real_sources_and_verbatim_excerpts():
    value = starter()
    assert len(value["publications"]) == 3
    assert all(
        p["doi"].startswith("https://doi.org/10.") for p in value["publications"]
    )
    assert value["synthetic"] and value["is_demo"]
    for evidence in value["evidence"]:
        paper = next(
            p for p in value["publications"] if p["id"] == evidence["publication_id"]
        )
        assert evidence["excerpt"] in paper["abstract"]
        assert evidence["excerpt"] != "Abstract."
        assert (
            evidence["requires_review"] and evidence["relationship"] == "unclassified"
        )
    assert analyze(value)["mean"] == pytest.approx(0.2)
    assert len(observations_for(value)) == 4
    value["publications"].clear()
    assert len(starter()["publications"]) == 3


def test_blank_workspace_is_not_ready_for_export():
    value = services.new_workspace("Field study")
    assert analyze(value)["ready"] is False
    assert observations_for(value) == []
    with pytest.raises(ValueError, match="hypothesis"):
        report_for(value)


def test_named_create_save_load_and_pristine_demo():
    app = ResearchWorkspace()
    dispatch(app, "save", title="My demo fork")
    assert app.data["workspace"]["title"] == "My demo fork"
    assert app.data["workspace"]["is_demo"] is False
    dispatch(app, "new", title="Field study")
    assert app.data["workspace"]["publications"] == []
    assert set(services.list_workspaces()) == {"My demo fork", "Field study"}
    edited = deepcopy(app.data["workspace"])
    edited["notes"] = "Researcher notes survive reopening."
    dispatch(app, "save", workspace=edited)
    dispatch(app, "load", title="My demo fork")
    assert len(app.data["workspace"]["publications"]) == 3
    dispatch(app, "load", title="Field study")
    assert app.data["workspace"]["notes"] == edited["notes"]
    dispatch(app, "demo")
    assert app.data["workspace"]["is_demo"]
    assert app.data["workspace"]["title"] == starter()["title"]
    assert app.data["workspace"]["notes"] == starter()["notes"]


def test_annotation_cannot_change_posterior_or_forge_excerpt():
    original = starter()
    edited = deepcopy(original)
    edited["evidence"][0].update(
        relationship="supporting", requires_review=False, excerpt="Forged text"
    )
    cleaned = clean_workspace(edited)
    assert cleaned["evidence"][0]["excerpt"] == original["evidence"][0]["excerpt"]
    assert cleaned["evidence"][0]["relationship"] == "supporting"
    assert analyze(cleaned)["mean"] == analyze(original)["mean"]
    assert analyze(cleaned)["interval"] == analyze(original)["interval"]


def test_researcher_twenty_of_hundred_is_one_user_batch():
    value = services.new_workspace("Survey")
    value.update(
        hypothesis="A measured event occurs in this population.", trials=100, events=20
    )
    value["setup"]["data_mode"] = "available"
    value["success_definition"] = "A measured event occurred"
    observations = observations_for(clean_workspace(value))
    assert len(observations) == 1
    assert observations[0].experiment_id == "user-entered-observations"
    assert not observations[0].synthetic
    assert not observations[0].independently_verified
    assert analyze(value)["ready"]


@pytest.mark.parametrize(
    "counts",
    [
        {"events": 101, "trials": 100},
        {"events": -1, "trials": 100},
        {"events": 1.5, "trials": 100},
    ],
)
def test_invalid_counts_cannot_save_or_export(counts):
    app = ResearchWorkspace()
    invalid = starter()
    invalid.update(counts)
    dispatch(app, "save", workspace=invalid, title="Invalid study")
    assert app.data["error"]
    assert services.list_workspaces() == []
    dispatch(app, "export", workspace=invalid)
    assert app.data["error"]
    assert app.data["download"] is None


def test_api_key_never_serialized(monkeypatch):
    marker = "test-secret-never-send-to-browser"
    monkeypatch.setenv("OPENALEX_API_KEY", marker)
    app = ResearchWorkspace()
    assert app.data["openalex_configured"] is True
    assert marker not in json.dumps(app.data)


def test_failed_search_preserves_results_sources_and_redacts_exception(monkeypatch):
    async def fail(query):
        raise RuntimeError("https://api.openalex.org/?api_key=private-marker")

    monkeypatch.setattr(widget, "search", fail)
    app = ResearchWorkspace()
    existing = [Publication(id="old-result", title="Earlier result").model_dump()]
    app._publish(app.data["workspace"], results=existing)
    sources = deepcopy(app.data["workspace"]["publications"])
    dispatch(app, "search", query="new query")
    assert app.data["error"]
    assert app.data["search_results"] == existing
    assert app.data["workspace"]["publications"] == sources
    assert "private-marker" not in json.dumps(app.data)


def test_stale_search_failure_cannot_overwrite_newer_workspace(monkeypatch):
    async def scenario():
        started, finish = asyncio.Event(), asyncio.Event()

        async def delayed_failure(query):
            started.set()
            await finish.wait()
            raise RuntimeError("old request failed")

        monkeypatch.setattr(widget, "search", delayed_failure)
        app = ResearchWorkspace()
        app._generation = 1
        old = asyncio.create_task(
            app.dispatch(Request(id="old", type="search", query="heat"), 1)
        )
        await started.wait()
        app._generation = 2
        await app.dispatch(Request(id="new", type="new", title="New investigation"), 2)
        finish.set()
        await old
        assert app.data["workspace"]["title"] == "New investigation"
        assert app.data["request_id"] == "new"
        assert app.data["error"] == ""

    asyncio.run(scenario())


def test_app_runs_with_research_workspace_widget():
    from app import app

    outputs, definitions = app.run()
    assert outputs
    assert isinstance(definitions["workspace"].widget, ResearchWorkspace)
    assert definitions["workspace"].widget.data["analysis"]["ready"]
