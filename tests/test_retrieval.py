from hypothesis_lab.models import Publication
from hypothesis_lab.retrieval.openalex import extract, reconstruct


def test_reconstruction_and_no_fabrication():
    assert (
        reconstruct({"heat": [1], "Extreme": [0], "events.": [2]})
        == "Extreme heat events."
    )
    assert reconstruct(None) is None
    assert extract(Publication(id="x", title="Test")) is None


def test_extraction_retains_provenance_and_no_inferred_relationship():
    p = Publication(
        id="x", title="Test", abstract="Reported sentence. Another sentence."
    )
    e = extract(p)
    assert e.excerpt == "Reported sentence."
    assert e.publication_id == "x"
    assert e.requires_review and e.relationship == "unclassified"


def test_search_deduplicates_doi_and_retries(monkeypatch):
    import asyncio

    import httpx

    from hypothesis_lab.retrieval import openalex

    calls = []
    real_client = httpx.AsyncClient

    async def handle(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429)
        item = {
            "id": "https://openalex.org/W1",
            "doi": "https://doi.org/example",
            "title": "Source",
            "abstract_inverted_index": {"Exact": [0], "text.": [1]},
        }
        return httpx.Response(
            200, json={"results": [item, dict(item, id="https://openalex.org/W2")]}
        )

    monkeypatch.setattr(
        openalex.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs),
    )

    async def no_wait(seconds):
        pass

    monkeypatch.setattr(openalex.asyncio, "sleep", no_wait)
    openalex._cache.clear()
    results = asyncio.run(openalex.search("heat"))
    assert len(results) == 1 and results[0].abstract == "Exact text."
    assert len(calls) == 2
    assert asyncio.run(openalex.search("heat")) == results
    assert len(calls) == 2


def test_extraction_skips_only_standalone_abstract_heading():
    for prefix in ["Abstract. ", "ABSTRACT\n", "Abstract: "]:
        abstract = (
            prefix + "On 19 May 2016 the temperature reached a record. More context."
        )
        evidence = extract(Publication(id="source", title="Source", abstract=abstract))
        assert evidence.excerpt == "On 19 May 2016 the temperature reached a record."
        assert evidence.excerpt in abstract
        assert evidence.source_location == "Abstract, first substantive sentence"
        assert evidence.relationship == "unclassified" and evidence.requires_review
    assert (
        extract(Publication(id="heading", title="Heading", abstract="Abstract."))
        is None
    )
    actual = extract(
        Publication(id="x", title="X", abstract="Abstract concepts are useful. Next.")
    )
    assert actual.excerpt == "Abstract concepts are useful."
    assert actual.source_location == "Abstract, first sentence"
