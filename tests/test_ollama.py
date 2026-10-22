"""Contract checks without requiring installed models or external networking."""

import asyncio
import json

import httpx
import pytest

from hypothesis_lab.ollama import Ollama, context_for, endpoint, fingerprint
from hypothesis_lab.ui.widget import analyze, starter, report_for


def test_discovery_interpretation_and_snapshot_provenance():
    workspace = starter()
    before = analyze(workspace)
    calls = []

    def handle(request):
        calls.append(request)
        if request.url.path == "/api/tags":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "research:latest", "size": 100, "digest": "abc"},
                        {"name": "remote:cloud", "size": 100},
                        {"name": "alias", "size": 100, "remote_host": "ollama.com"},
                    ]
                },
            )
        payload = json.loads(request.content)
        assert payload["stream"] is False
        assert payload["model"] == "research:latest"
        assert "OpenAlex" not in payload.get("api_key", "")
        return httpx.Response(
            200, json={"message": {"content": "## Findings\nReview [S1]."}}
        )

    client = Ollama(httpx.MockTransport(handle))
    assert asyncio.run(client.models()) == [
        {"name": "research:latest", "digest": "abc"}
    ]
    draft = asyncio.run(client.interpret("research:latest", workspace, before))
    assert draft["digest"] == "abc" and draft["requires_review"]
    assert draft["input_hash"] == fingerprint(context_for(workspace, before))
    workspace["interpretation"] = draft
    assert analyze(workspace) == before
    assert not report_for(workspace)["interpretation"]["stale"]
    workspace["notes"] += " Changed interpretation of the design."
    assert report_for(workspace)["interpretation"]["stale"]
    assert all(r.url.host == "127.0.0.1" for r in calls)


def test_cloud_model_cannot_be_requested():
    client = Ollama(
        httpx.MockTransport(lambda r: httpx.Response(200, json={"models": []}))
    )
    with pytest.raises(ValueError, match="installed local model"):
        asyncio.run(client.interpret("remote:cloud", starter(), analyze(starter())))


@pytest.mark.parametrize(
    "url",
    [
        "https://ollama.com",
        "http://example.com",
        "http://localhost/path",
        "http://user:pass@localhost",
    ],
)
def test_remote_endpoints_are_rejected(monkeypatch, url):
    monkeypatch.setenv("HYPOTHESIS_OLLAMA_URL", url)
    with pytest.raises(ValueError, match="loopback"):
        endpoint()


def test_connection_failure_is_actionable_and_does_not_expose_request():
    def fail(request):
        raise httpx.ConnectError("private request", request=request)

    with pytest.raises(ValueError, match="ollama serve") as error:
        asyncio.run(Ollama(httpx.MockTransport(fail)).models())
    assert "private request" not in str(error.value)


def test_literature_only_context_does_not_claim_calculated_findings():
    workspace = starter()
    workspace["setup"]["data_mode"] = "literature_only"
    context = context_for(workspace, analyze(workspace))
    assert context["numerical_result"]["ready"] is False
    assert context["numerical_result"]["mean"] is None
    assert context["numerical_result"]["successes"] == 0
    assert "interpretation" not in context
    assert context["sources"][0]["citation"] == "S1"


def test_timeout_and_empty_generation_are_actionable():
    def timeout(request):
        raise httpx.ReadTimeout("sensitive", request=request)

    with pytest.raises(ValueError, match="timed out"):
        asyncio.run(Ollama(httpx.MockTransport(timeout)).models())

    def empty(request):
        return httpx.Response(
            200,
            json={"models": [{"name": "local", "size": 100}]}
            if request.url.path == "/api/tags"
            else {"message": {"content": ""}},
        )

    with pytest.raises(ValueError, match="no interpretation"):
        asyncio.run(
            Ollama(httpx.MockTransport(empty)).interpret(
                "local", starter(), analyze(starter())
            )
        )
