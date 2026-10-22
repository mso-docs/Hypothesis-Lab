"""One authoritative script and practice scenario for the getting-started video.

The source is a real OpenAlex metadata snapshot. Counts are synthetic and never
attributed to the source paper. Video chapters, transcript, and app help share it.
"""

from copy import deepcopy
from hypothesis_lab.retrieval.openalex import extract
from hypothesis_lab.models import Publication

TITLE = "Radish germination · practice"
HYPOTHESIS = "At least 60% of radish seeds germinate within seven days under controlled conditions."
PUBLICATION = {
    "id": "https://openalex.org/W2044136592",
    "title": "Influence of Pressure on Germination of Garden Cress, Leaf Mustard, and Radish Seeds at Various Temperatures",
    "authors": ["Akio Shimizu", "Jun Kumakura"],
    "year": 2011,
    "doi": "https://doi.org/10.4236/ajps.2011.23050",
    "abstract": "The effects of hydrostatic pressure (0.1 - 400 MPa) and temperature (4°C, 25°C, and 35°C) on the germination of three types of seeds (garden cress, leaf mustard, and radish) were studied. The normal germination rate of the three types of seeds was decreased at high hydrostatic pressure, and germination time tended to be delayed. Pressure and temperature had two types of effects on seed germination. Germination of garden cress and leaf mustard seeds was more resistant to pressure at lower temperature. Conversely, germination of radish seeds was most pressure-sensitive at low temperature, and germination drastically decreased with treatment at 50 MPa and 4°C. Generally, pressure and temperature effects on protein structure and enzyme activity have been classified into two types, “hillside”-like (pressurization decreases the stable temperature range) and “tongue”-like (stabilizing effect of moderate pressure against heat denaturation). Therefore, the type of temperature-pressure effects on germination of garden cress and leaf mustard seeds is classified as “hillside”-like and that of radish seeds is classified as “tongue”-like, similarly to the generally observed effects on protein denaturation.",
    "url": "https://doi.org/10.4236/ajps.2011.23050",
    "provider": "OpenAlex",
}

CHAPTERS = [
    {
        "start": 0,
        "end": 10,
        "title": "From question to report",
        "page": "question",
        "caption": "Start a research investigation without knowing a prior or posterior. Define the event, collect research, choose starting assumptions, and let the app calculate the updated result.",
    },
    {
        "start": 10,
        "end": 24,
        "title": "Create an investigation",
        "page": "question",
        "caption": "In the explorer, choose New investigation. Name it Radish germination. A new workspace starts without papers or observations.",
    },
    {
        "start": 24,
        "end": 40,
        "title": "Define a testable hypothesis",
        "page": "question",
        "caption": "Write: At least 60% of radish seeds germinate within seven days under controlled conditions. In guided analysis setup, define the event as a visible radicle by day seven. No observations yet? Choose Not yet and continue reviewing papers.",
    },
    {
        "start": 40,
        "end": 56,
        "title": "Attach a real research paper",
        "page": "sources",
        "caption": "Open literature, then Add a link. Paste the example DOI, inspect its metadata, and follow the original source. Its conditions differ from our teaching scenario.",
    },
    {
        "start": 56,
        "end": 72,
        "title": "Review the source excerpt",
        "page": "evidence",
        "caption": "Open evidence.json. Read the verbatim excerpt and the original source. Mark its relationship Inconclusive for this scenario; classification does not update the model.",
    },
    {
        "start": 72,
        "end": 92,
        "title": "Choose assumptions and add data",
        "page": "analysis",
        "caption": "In analysis.py, define the event, choose I have event counts, and select Little previous knowledge. Enter 34 events in 50 observations and mark them synthetic. The app calculates a 67.3% updated estimate; you do not enter a posterior.",
    },
    {
        "start": 92,
        "end": 106,
        "title": "Record methods and limitations",
        "page": "notes",
        "caption": "In research-notes.md, record the event definition, sampling design, independence assumptions, and limitations. The interval crosses 60%; the mean alone does not confirm the hypothesis.",
    },
    {
        "start": 106,
        "end": 122,
        "title": "Save and export your report",
        "page": "report",
        "caption": "Save with the toolbar or Ctrl/Cmd S. Open report.md and export Markdown or JSON. Keep sources, observations, priors, annotations, and notes together for reproducibility.",
    },
]
DURATION = CHAPTERS[-1]["end"]


def practice_workspace() -> dict:
    paper = Publication.model_validate(deepcopy(PUBLICATION))
    evidence = extract(paper)
    if evidence:
        evidence.relationship = "inconclusive"
        evidence.requires_review = True
    return {
        "title": TITLE,
        "hypothesis": HYPOTHESIS,
        "prior": {"alpha": 1, "beta": 1},
        "setup": {"data_mode": "available", "prior_mode": "little"},
        "events": 34,
        "trials": 50,
        "publications": [paper.model_dump()],
        "evidence": [evidence.model_dump()] if evidence else [],
        "synthetic": True,
        "is_demo": False,
        "is_tutorial": True,
        "success_definition": "Visible radicle within seven days after sowing",
        "sampling_description": "50 synthetic teaching observations; independent Bernoulli trials assumed. Not data from the linked paper.",
        "notes": "# Radish germination · practice\n\n## Question\n"
        + HYPOTHESIS
        + "\n\n## Event definition\nVisible radicle by day seven.\n\n## Teaching observations\n34 events in 50 observations. All counts are synthetic and are not extracted from the paper.\n\n## Source context\nThe linked paper studies pressure and temperature treatments. It provides context, not direct validation of this scenario. The suggested Inconclusive label needs your review.\n\n## Model assumptions\nIndependent Bernoulli trials, a consistent event definition, and constant probability.\n\n## Interpretation\nThe uniform Beta(1,1) starting assumption becomes Beta(35,17). The 95% interval crosses 60%; the posterior mean alone does not confirm the scientific hypothesis.\n\n## Next steps\nCollect real, independently checked observations under a documented sampling design. This export is an investigation report, not a publication-ready manuscript.\n",
    }


def vtt_timestamp(seconds: int) -> str:
    return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}.000"


def captions_vtt() -> str:
    return (
        "WEBVTT\n\n"
        + "\n\n".join(
            f"{i + 1}\n{vtt_timestamp(c['start'])} --> {vtt_timestamp(c['end'])}\n{c['caption']}"
            for i, c in enumerate(CHAPTERS)
        )
        + "\n"
    )


def chapters_vtt() -> str:
    return (
        "WEBVTT\n\n"
        + "\n\n".join(
            f"{i + 1}\n{vtt_timestamp(c['start'])} --> {vtt_timestamp(c['end'])}\n{c['title']}"
            for i, c in enumerate(CHAPTERS)
        )
        + "\n"
    )
