import pytest

from hypothesis_lab import persistence
from hypothesis_lab.config import load_environment
from hypothesis_lab.retrieval.openalex import safe_research_url
from hypothesis_lab.services import (
    demo_workspace,
    list_workspaces,
    load_workspace,
    new_workspace,
    save_workspace,
)


def test_environment_preserves_process_values(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "process-value")
    monkeypatch.delenv("LAB_TEST_SETTING", raising=False)
    path = tmp_path / ".env"
    path.write_text('OPENALEX_API_KEY=file-value\nLAB_TEST_SETTING="hello"\n')
    load_environment(path)
    import os

    assert os.environ["OPENALEX_API_KEY"] == "process-value"
    assert os.environ["LAB_TEST_SETTING"] == "hello"


def test_starter_uses_linked_sources_and_blank_has_no_observations():
    demo = demo_workspace()
    assert len(demo["publications"]) == 3
    assert all(p["doi"].startswith("https://doi.org/10.") for p in demo["publications"])
    assert demo["synthetic"]
    blank = new_workspace("My research")
    assert blank["publications"] == [] and blank["trials"] == 0
    assert not blank["synthetic"]


def test_named_investigations_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "DB_PATH", tmp_path / "workspace.sqlite3")
    save_workspace("First", new_workspace("First"))
    save_workspace("Second", demo_workspace())
    assert set(list_workspaces()) == {"First", "Second"}
    assert load_workspace("First")["trials"] == 0
    assert load_workspace("Second")["title"] == "Second"
    assert load_workspace("missing") is None


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://localhost/x",
        "https://127.0.0.1",
        "javascript:alert(1)",
        "https://a:b@example.com",
    ],
)
def test_reject_invalid_research_links(url):
    with pytest.raises(ValueError):
        safe_research_url(url)


def test_bare_doi_link():
    assert safe_research_url("10.1038/s41558-021-01092-9").startswith(
        "https://doi.org/"
    )


def test_resolve_doi_and_preserve_unverified_links(monkeypatch):
    import asyncio

    import httpx

    from hypothesis_lab.retrieval import openalex

    calls = []
    client = httpx.AsyncClient

    async def handle(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "id": "https://openalex.org/W123",
                "title": "Verified title",
                "doi": "https://doi.org/10.1234/test",
                "publication_year": 2024,
            },
        )

    monkeypatch.setattr(
        openalex.httpx,
        "AsyncClient",
        lambda **kwargs: client(transport=httpx.MockTransport(handle), **kwargs),
    )
    paper = asyncio.run(openalex.resolve_link("10.1234/test"))
    assert paper.title == "Verified title" and paper.abstract is None
    assert calls[0].url.host == "api.openalex.org"
    link = asyncio.run(openalex.resolve_link("https://research.example/paper"))
    assert "unverified" in link.provider and len(calls) == 1


def test_link_resolution_errors_do_not_expose_api_key(monkeypatch):
    import asyncio

    import httpx

    from hypothesis_lab.retrieval import openalex

    client = httpx.AsyncClient
    monkeypatch.setenv("OPENALEX_API_KEY", "secret-test-value")

    async def handle(request):
        return httpx.Response(401)

    monkeypatch.setattr(
        openalex.httpx,
        "AsyncClient",
        lambda **kwargs: client(transport=httpx.MockTransport(handle), **kwargs),
    )
    with pytest.raises(ValueError) as error:
        asyncio.run(openalex.resolve_link("10.1234/test"))
    assert "secret-test-value" not in str(error.value)
