"""Bounded, cached metadata retrieval; never invent missing abstracts."""

import asyncio
import os
import re
from urllib.parse import quote, urlparse

import httpx

from hypothesis_lab.config import load_environment
from hypothesis_lab.models import Evidence, Publication

load_environment()

_cache: dict[str, list[Publication]] = {}


def reconstruct(index):
    if not index:
        return None
    words = sorted(
        (position, word) for word, positions in index.items() for position in positions
    )
    return " ".join(word for _, word in words)


async def search(query: str) -> list[Publication]:
    query = query.strip()
    if not query:
        return []
    if query in _cache:
        return _cache[query]
    params = {"search": query, "per-page": 10}
    if os.getenv("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    async with httpx.AsyncClient(timeout=20) as client:
        for attempt in range(3):
            response = await client.get("https://api.openalex.org/works", params=params)
            if (
                response.status_code == 429 or response.status_code >= 500
            ) and attempt < 2:
                await asyncio.sleep(2**attempt)
                continue
            response.raise_for_status()
            seen, publications = set(), []
            for item in response.json().get("results", []):
                key = (item.get("doi") or item["id"]).lower()
                if key in seen:
                    continue
                seen.add(key)
                publications.append(
                    Publication(
                        id=item["id"],
                        title=item.get("title") or "Untitled publication",
                        authors=[
                            a["author"]["display_name"]
                            for a in item.get("authorships", [])[:3]
                        ],
                        year=item.get("publication_year"),
                        doi=item.get("doi"),
                        abstract=reconstruct(item.get("abstract_inverted_index")),
                        url=item.get("doi") or item["id"],
                    )
                )
            _cache[query] = publications
            return publications
    return []


def extract(publication: Publication) -> Evidence | None:
    """Preserve a sentence verbatim, skipping only an explicit abstract heading."""
    if not publication.abstract:
        return None
    abstract = publication.abstract.strip()
    # Strip a standalone metadata heading, not the word in a substantive sentence.
    heading = re.match(r"^abstract(?:[.:]\s*|\s*\n\s*|$)", abstract, re.IGNORECASE)
    if heading:
        abstract = abstract[heading.end() :]
    if not abstract:
        return None
    excerpt = re.split(r"(?<=[.!?])\s+", abstract)[0]
    return Evidence(
        publication_id=publication.id,
        claim=excerpt,
        excerpt=excerpt,
        source_location=(
            "Abstract, first substantive sentence"
            if heading
            else "Abstract, first sentence"
        ),
    )


def safe_research_url(value: str) -> str:
    """Validate links without fetching arbitrary researcher-supplied hosts."""
    value = value.strip()
    if value.startswith("10."):
        value = "https://doi.org/" + value
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Use a DOI or a public HTTPS research link")
    import ipaddress

    host = parsed.hostname.lower()
    if host == "localhost" or "." not in host:
        raise ValueError("Use a public research link")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("IP-address links are not supported")
    return value


async def resolve_link(value: str) -> Publication:
    """Resolve DOI/OpenAlex metadata; preserve other links for manual review."""
    url = safe_research_url(value)
    parsed = urlparse(url)
    if parsed.hostname in {"doi.org", "dx.doi.org"}:
        identifier = "https://doi.org/" + parsed.path.lstrip("/")
        if not re.match(r"^https://doi.org/10\.\d{4,9}/\S+$", identifier):
            raise ValueError("Enter a valid DOI")
    elif parsed.hostname == "openalex.org" and re.fullmatch(r"/W\d+", parsed.path):
        identifier = parsed.path.lstrip("/")
    else:
        return Publication(
            id=url,
            title=parsed.hostname + parsed.path,
            url=url,
            provider="Researcher link · metadata unverified",
        )
    params = {}
    if os.getenv("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                "https://api.openalex.org/works/" + quote(identifier, safe=""),
                params=params,
            )
            response.raise_for_status()
            item = response.json()
    except httpx.HTTPError:
        raise ValueError(
            "OpenAlex could not resolve this source; check the identifier and connection"
        ) from None
    return Publication(
        id=item["id"],
        title=item.get("title") or "Untitled publication",
        authors=[a["author"]["display_name"] for a in item.get("authorships", [])[:3]],
        year=item.get("publication_year"),
        doi=item.get("doi"),
        abstract=reconstruct(item.get("abstract_inverted_index")),
        url=item.get("doi") or item["id"],
    )
