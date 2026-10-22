"""Public preview contains curated data only and needs no Python server."""

import importlib.util
import json
from pathlib import Path


def test_static_build_is_allowlisted_and_subpath_safe(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "PRIVATE-SENTINEL-DO-NOT-EXPORT")
    path = Path(__file__).resolve().parents[1] / "scripts/build_static_demo.py"
    spec = importlib.util.spec_from_file_location("static_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.build(tmp_path, "https://github.com/example/hypothesis-lab")
    state = json.loads((tmp_path / "demo.json").read_text())
    assert state["workspace"]["is_demo"] and state["workspace"]["synthetic"]
    assert state["investigations"] == [] and not state["openalex_configured"]
    assert "Run locally" in (tmp_path / "index.html").read_text()
    for name in (
        "demo.json",
        "guide.json",
        "index.html",
        "run-locally.html",
        "workspace.mjs",
        "preview.mjs",
    ):
        assert "PRIVATE-SENTINEL-DO-NOT-EXPORT" not in (tmp_path / name).read_text()
    guide = json.loads((tmp_path / "guide.json").read_text())
    assert guide["hypothesis"] and guide["source"]["doi"]
    for key in ("video_src", "poster_src", "captions_src", "chapters_src"):
        assert guide[key].startswith("./media/")
        assert (tmp_path / guide[key]).is_file()
    assert "marimo run app.py" in (tmp_path / "run-locally.html").read_text()
