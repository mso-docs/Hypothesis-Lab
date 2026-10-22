"""Typed bridge between the research IDE and the deterministic Python services.

The browser owns presentation and transient navigation. Python owns validation,
retrieval, calculations, and durable records. Credentials never enter widget state.
"""

import asyncio
from copy import deepcopy
from pathlib import Path
import re
import os
import math
import json
from typing import Literal

import anywidget
import traitlets
import numpy as np
from scipy.stats import beta
from pydantic import BaseModel, Field

from hypothesis_lab import services
from hypothesis_lab.ollama import Ollama, context_for, fingerprint
from hypothesis_lab.setup import normalize_setup, missing_setup, assumption_summary
from hypothesis_lab.demo import OBSERVATIONS
from hypothesis_lab.inference import estimate, compare, sequence
from hypothesis_lab.models import Observation, Publication
from hypothesis_lab.retrieval.openalex import search, resolve_link, extract
from hypothesis_lab.reporting import snapshot, markdown
from hypothesis_lab.tutorial import practice_workspace
from hypothesis_lab.ui.walkthrough import walkthrough_bundle

ASSETS = Path(__file__).parent / "frontend"
RELATIONSHIPS = {"supporting", "contradicting", "inconclusive", "unclassified"}


def frontend_source() -> str:
    """Bundle three dependency-free ES modules for AnyWidget's single ESM entry."""
    chunks = []
    for name in ("icons.js", "charts.js", "workspace.js"):
        source = (ASSETS / name).read_text()
        source = re.sub(r"^import .*?;\s*$", "", source, flags=re.MULTILINE)
        source = re.sub(
            r"^export (?=(?:function|const|let|class)\b)",
            "",
            source,
            flags=re.MULTILINE,
        )
        chunks.append(source)
    return "\n".join(chunks)


class Request(BaseModel):
    id: str = Field(max_length=100)
    type: Literal[
        "new",
        "demo",
        "tutorial",
        "load",
        "save",
        "search",
        "link",
        "export",
        "update",
        "ollama_models",
        "interpret",
    ]
    workspace: dict | None = None
    title: str = Field(default="", max_length=160)
    query: str = Field(default="", max_length=500)
    link: str = Field(default="", max_length=2000)
    model: str = Field(default="", max_length=200)


def clean_workspace(raw: dict) -> dict:
    """Validate editable content and reconstruct evidence from original abstracts."""
    value = normalize_setup(raw)
    value["title"] = str(value.get("title", "Untitled investigation"))[:160]
    value["hypothesis"] = str(value.get("hypothesis", ""))[:10000]
    value["notes"] = str(value.get("notes", ""))[:100000]
    prior = value.get("prior", {})
    a, b = float(prior.get("alpha", 1)), float(prior.get("beta", 1))
    if not all(math.isfinite(v) and 0 < v <= 1000001 for v in (a, b)):
        raise ValueError("Prior parameters must be positive finite numbers")
    value["prior"] = {"alpha": a, "beta": b}
    for key in ("trials", "events"):
        number = value.get(key, 0)
        if (
            isinstance(number, bool)
            or not isinstance(number, (int, float))
            or not math.isfinite(number)
            or number < 0
            or number != int(number)
            or number > 100000000
        ):
            raise ValueError("Observation counts must be nonnegative whole numbers")
        value[key] = int(number)
    if value["events"] > value["trials"]:
        raise ValueError("Events cannot exceed the number of eligible observations")
    for key, fallback in (("p0", 0.1), ("p1", 0.2)):
        probability = float(value.get(key, fallback))
        if not math.isfinite(probability) or not 0 < probability < 1:
            raise ValueError(
                "Comparison probabilities must be strictly between zero and one"
            )
        value[key] = probability
    for key in ("success_definition", "sampling_description"):
        value[key] = str(value.get(key, ""))[:5000]
    raw_batches = value.get("observation_batches", [])
    if not isinstance(raw_batches, list) or len(raw_batches) > 100:
        raise ValueError("At most 100 observation batches are supported")
    value["observation_batches"] = [
        Observation.model_validate(o).model_dump() for o in raw_batches
    ]
    raw_papers = value.get("publications", [])
    if not isinstance(raw_papers, list) or len(raw_papers) > 50:
        raise ValueError("At most 50 attached publications are supported")
    papers = [Publication.model_validate(p) for p in raw_papers]
    seen, unique = set(), []
    for paper in papers:
        key = (paper.doi or paper.id).lower()
        if key not in seen:
            seen.add(key)
            unique.append(paper)
    papers = unique
    value["publications"] = [p.model_dump() for p in papers]
    annotations = {
        e.get("publication_id"): e
        for e in value.get("evidence", [])
        if isinstance(e, dict)
    }
    evidence = []
    for paper in papers:
        record = extract(paper)
        if record:
            annotation = annotations.get(paper.id, {})
            relationship = annotation.get("relationship", "unclassified")
            record.relationship = (
                relationship if relationship in RELATIONSHIPS else "unclassified"
            )
            record.requires_review = bool(annotation.get("requires_review", True))
            evidence.append(record.model_dump())
    value["evidence"] = evidence
    value["synthetic"] = bool(value.get("synthetic", False))
    return value


def starter() -> dict:
    value = services.demo_workspace()
    value["observation_batches"] = [o.model_dump() for o in OBSERVATIONS]
    value["success_definition"] = "Day exceeding a fixed extreme-heat threshold"
    value["sampling_description"] = (
        "Four independent synthetic teaching batches; not extracted from the papers"
    )
    return value


def observations_for(workspace: dict) -> list[Observation]:
    workspace = normalize_setup(workspace)
    if workspace["setup"]["data_mode"] == "literature_only":
        return []
    k, n = workspace["events"], workspace["trials"]
    if n == 0:
        if k:
            raise ValueError("Events cannot exceed the number of observations")
        return []
    batches = [
        Observation.model_validate(o) for o in workspace.get("observation_batches", [])
    ]
    if (
        batches
        and sum(o.trials for o in batches) == n
        and sum(o.successes for o in batches) == k
    ):
        if len({o.experiment_id for o in batches}) != len(batches):
            raise ValueError(
                "Observation batches must have unique experiment identifiers"
            )
        return batches
    return [
        Observation(
            experiment_id="user-entered-observations",
            successes=k,
            trials=n,
            synthetic=workspace["synthetic"],
            independently_verified=False,
            success_definition=workspace.get("success_definition")
            or "Researcher-defined event",
            sampling_description=workspace.get("sampling_description")
            or "Researcher-entered counts; independence must be checked",
        )
    ]


def analyze(workspace: dict) -> dict:
    workspace = normalize_setup(workspace)
    pending = missing_setup(workspace)
    a, b = workspace["prior"]["alpha"], workspace["prior"]["beta"]
    observations = observations_for(workspace)
    result = estimate(a, b, observations)
    k, n = sum(o.successes for o in observations), sum(o.trials for o in observations)
    # Include quantile samples so narrow and boundary posteriors are not lost
    # between a uniform grid's points at large sample sizes.
    quantiles = np.linspace(0.001, 0.999, 151)
    x = np.unique(
        np.clip(
            np.concatenate(
                [
                    np.linspace(0.001, 0.999, 251),
                    beta.ppf(quantiles, result.alpha, result.beta),
                    beta.ppf(quantiles, 1 + k, 1 + n - k),
                    [result.mean],
                ]
            ),
            1e-12,
            1 - 1e-12,
        )
    )
    updates = sequence(a, b, observations)
    return {
        **result.to_dict(),
        "prior": {"alpha": a, "beta": b},
        "successes": k,
        "trials": n,
        "ready": not pending,
        "missing_setup": pending,
        "assumption_summary": assumption_summary(workspace),
        "export_ready": len(workspace["hypothesis"].strip()) >= 10
        or bool(workspace.get("publications")),
        "curves": {
            "x": x.tolist(),
            "prior": beta.pdf(x, a, b).tolist(),
            "posterior": beta.pdf(x, result.alpha, result.beta).tolist(),
            "likelihood": beta.pdf(x, 1 + k, 1 + n - k).tolist(),
        },
        "sequence": [
            {
                "batch": i,
                "label": "Prior" if i == 0 else f"Batch {i}",
                "n": sum(o.trials for o in observations[:i]),
                "mean": r.mean,
                "lower": r.interval[0],
                "upper": r.interval[1],
            }
            for i, r in enumerate(updates)
        ],
        "sensitivity": [
            {
                "label": label,
                "prior_alpha": pa,
                "prior_beta": pb,
                **estimate(pa, pb, observations).to_dict(),
            }
            for label, pa, pb in [
                ("Uniform", 1, 1),
                ("Weakly informed", 2, 8),
                ("Concentrated", 10, 40),
            ]
        ],
        "log_bayes_factor": compare(
            float(workspace.get("p0", 0.1)),
            float(workspace.get("p1", 0.2)),
            observations,
        ),
    }


def interpretation_record(workspace, analysis):
    record = workspace.get("interpretation")
    if not isinstance(record, dict):
        return None
    return {
        **record,
        "stale": record.get("input_hash")
        != fingerprint(context_for(workspace, analysis)),
        "requires_review": True,
    }


def report_for(workspace: dict) -> dict:
    workspace = clean_workspace(workspace)
    analysis = analyze(workspace)
    if not analysis["export_ready"]:
        raise ValueError("Add a hypothesis or sources before exporting")
    if not analysis["ready"]:
        from datetime import datetime, timezone

        return {
            "schema_version": 2,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "title": workspace["title"],
            "hypothesis": workspace["hypothesis"],
            "model": "Not run",
            "model_status": "pending",
            "posterior": None,
            "prior": workspace["prior"],
            "setup": workspace["setup"],
            "assumption_summary": analysis["assumption_summary"],
            "missing_setup": analysis["missing_setup"],
            "observations": [],
            "publications": workspace["publications"],
            "evidence": workspace["evidence"],
            "notes": workspace["notes"],
            "interpretation": interpretation_record(workspace, analysis),
            "limitations": "Source-review report only. No numerical inference has been performed. Qualitative annotations are not quantitative observations.",
        }
    observations = observations_for(workspace)
    result = estimate(
        workspace["prior"]["alpha"], workspace["prior"]["beta"], observations
    )
    report = snapshot(
        workspace["hypothesis"],
        workspace["prior"]["alpha"],
        workspace["prior"]["beta"],
        observations,
        result,
        [Publication.model_validate(p) for p in workspace["publications"]],
        workspace["evidence"],
    )
    report.update(
        title=workspace["title"],
        notes=workspace["notes"],
        setup=workspace["setup"],
        assumption_summary=analysis["assumption_summary"],
        model_status="computed",
        interpretation=interpretation_record(workspace, analysis),
        success_definition=workspace.get("success_definition"),
        sampling_description=workspace.get("sampling_description"),
    )
    report["limitations"] = (
        (
            "Synthetic demonstration observations. "
            if workspace["synthetic"]
            else "Researcher-entered observations have not been independently verified. "
        )
        + "Qualitative evidence does not update the posterior. Independent Bernoulli trials and a common event definition are assumed. This model estimates event frequency; it does not establish trend or causation."
    )
    return report


class ResearchWorkspace(anywidget.AnyWidget):
    _esm = frontend_source()
    _css = ASSETS / "workspace.css"
    data = traitlets.Dict().tag(sync=True)
    request = traitlets.Dict().tag(sync=True)
    fullscreen = traitlets.Bool(False).tag(sync=True)
    guide = traitlets.Dict().tag(sync=True)

    def __init__(self, workspace: dict | None = None, *, fullscreen: bool = False):
        super().__init__()
        self.fullscreen = fullscreen
        self.guide = walkthrough_bundle()
        self._generation = 0
        self._tasks = set()
        self._ollama_models = []
        self._publish(
            workspace or starter(),
            message="Guided demo ready. Start with the research question.",
        )
        self.observe(self._on_request, names="request")

    def _publish(
        self,
        workspace,
        *,
        message="",
        error="",
        results=None,
        request_id="",
        download=None,
    ):
        analysis = None
        try:
            workspace = normalize_setup(workspace)
            analysis = analyze(workspace)
        except (ValueError, TypeError):
            error = (
                error
                or "Check the model inputs: events must not exceed observations, and prior parameters must be positive."
            )
        self.data = {
            "workspace": workspace,
            "analysis": analysis,
            "ollama_models": self._ollama_models,
            "interpretation_stale": bool(
                workspace.get("interpretation")
                and analysis
                and workspace["interpretation"].get("input_hash")
                != fingerprint(context_for(workspace, analysis))
            ),
            "investigations": services.list_workspaces(),
            "openalex_configured": bool(os.getenv("OPENALEX_API_KEY")),
            "message": message,
            "error": error,
            "request_id": request_id,
            "search_results": results
            if results is not None
            else self.data.get("search_results", []),
            "download": download,
        }

    def _on_request(self, change):
        try:
            request = Request.model_validate(change["new"])
        except ValueError:
            self._publish(
                self.data["workspace"],
                error="The request could not be read. Reload the workspace and try again.",
            )
            return
        self._generation += 1
        generation = self._generation
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.dispatch(request, generation))
        else:
            task = loop.create_task(self.dispatch(request, generation))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def dispatch(self, request: Request, generation: int | None = None):
        workspace = deepcopy(self.data["workspace"])
        try:
            if request.workspace is not None:
                workspace = clean_workspace(request.workspace)
            message, results, download = "", None, None
            if request.type == "new":
                title = request.title.strip()
                if not title:
                    raise ValueError("Give your investigation a name")
                if title in services.list_workspaces():
                    raise ValueError(
                        "That name is already in use. Choose another name or open the existing investigation."
                    )
                workspace = services.new_workspace(title)
                services.save_workspace(title, workspace)
                message = (
                    "Investigation created. Define your research question to begin."
                )
                results = []
            elif request.type == "demo":
                workspace, results = starter(), []
                message = "Original guided demo restored."
            elif request.type == "tutorial":
                workspace, results = practice_workspace(), []
                existing = set(services.list_workspaces())
                base, suffix = workspace["title"], 2
                while workspace["title"] in existing:
                    workspace["title"] = f"{base} {suffix}"
                    suffix += 1
                message = "Seed-germination practice loaded. All observations are synthetic; save to keep your work."
            elif request.type == "load":
                workspace = services.load_workspace(request.title)
                if workspace is None:
                    raise ValueError("That investigation could not be found")
                workspace = clean_workspace(workspace)
                results = []
                message = "Investigation opened."
            elif request.type == "save":
                if workspace.get("is_demo"):
                    workspace["title"] = (
                        request.title.strip() or "Extreme heat · my investigation"
                    )
                    workspace["is_demo"] = False
                services.save_workspace(workspace["title"], workspace)
                message = "Saved locally. The original guided demo is always available."
            elif request.type == "search":
                if not request.query.strip():
                    raise ValueError("Enter a topic, title, or author to search")
                results = [p.model_dump() for p in await search(request.query)]
                message = f"Found {len(results)} publications. Select papers to add to this investigation."
            elif request.type == "link":
                publication = await resolve_link(request.link)
                workspace["publications"].append(publication.model_dump())
                workspace = clean_workspace(workspace)
                message = "Source added to the investigation."
            elif request.type == "ollama_models":
                models = await Ollama().models()
                if generation is not None and generation != self._generation:
                    return
                self._ollama_models = models
                message = f"Found {len(models)} installed local models."
            elif request.type == "interpret":
                workspace["interpretation"] = await Ollama().interpret(
                    request.model, workspace, analyze(workspace)
                )
                message = (
                    "Local-model interpretation ready for review. Save to keep it."
                )
            elif request.type == "export":
                report = report_for(workspace)
                download = {
                    "id": request.id,
                    "json": json.dumps(report, indent=2),
                    "markdown": markdown(report),
                }
                message = "Reproducibility package prepared."
            elif request.type == "update":
                message = "Changes ready · save to keep this investigation"
            else:
                raise ValueError("Unknown workspace action")
            if generation is not None and generation != self._generation:
                return
            self._publish(
                workspace,
                message=message,
                results=results,
                request_id=request.id,
                download=download,
            )
        except ValueError as error:
            if generation is not None and generation != self._generation:
                return
            self._publish(
                self.data["workspace"], error=str(error), request_id=request.id
            )
        except Exception:
            if generation is not None and generation != self._generation:
                return
            # HTTP error strings can contain API keys in URLs. Do not forward them.
            self._publish(
                self.data["workspace"],
                error="This action could not finish. Your existing sources are preserved. Check connectivity and the OpenAlex configuration, then retry.",
                request_id=request.id,
            )
