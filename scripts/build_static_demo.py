"""Build an allowlisted, read-only Pages preview; never export local workspaces."""

import argparse
import html
import json
from pathlib import Path
import re
import shutil

from hypothesis_lab.ui.widget import analyze, frontend_source, starter
from hypothesis_lab.tutorial import CHAPTERS, DURATION, HYPOTHESIS, PUBLICATION


def build(output: Path, repository: str):
    if not re.fullmatch(
        r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
    ):
        raise ValueError(
            "Use the public GitHub repository URL, without credentials or query parameters"
        )
    output.mkdir(parents=True, exist_ok=True)
    assets = Path(__file__).resolve().parents[1] / "src/hypothesis_lab/ui/frontend"
    shutil.copytree(assets / "media", output / "media", dirs_exist_ok=True)
    shutil.copyfile(assets / "workspace.css", output / "workspace.css")
    (output / "workspace.mjs").write_text(frontend_source())
    workspace = starter()
    state = {
        "workspace": workspace,
        "analysis": analyze(workspace),
        "investigations": [],
        "openalex_configured": False,
        "message": "",
        "error": "",
        "search_results": [],
        "ollama_models": [],
        "download": None,
    }
    (output / "demo.json").write_text(json.dumps(state))
    guide = {
        "title": "From research question to reproducible report",
        "duration": DURATION,
        "format": "Captioned illustrated walkthrough",
        "chapters": CHAPTERS,
        "hypothesis": HYPOTHESIS,
        "source": PUBLICATION,
        "video_src": "./media/getting-started.mp4",
        "poster_src": "./media/getting-started.jpg",
        "captions_src": "./media/getting-started.vtt",
        "chapters_src": "./media/getting-started-chapters.vtt",
    }
    # Resolve exact package filenames instead of assuming caption names.
    names = [p.name for p in (assets / "media").iterdir()]
    guide["poster_src"] = "./media/" + next(n for n in names if n.endswith(".jpg"))
    guide["captions_src"] = "./media/" + next(
        n for n in names if n.endswith(".vtt") and "chapter" not in n
    )
    guide["chapters_src"] = "./media/" + next(
        n for n in names if n.endswith(".vtt") and "chapter" in n
    )
    (output / "guide.json").write_text(json.dumps(guide))
    (output / ".nojekyll").touch()
    (output / "preview.mjs").write_text("""async function boot() {
const {default: {render}} = await import("./workspace.mjs");
const [data, guide] = await Promise.all(["demo.json", "guide.json"].map(p => fetch(new URL(p, import.meta.url)).then(r => {if (!r.ok) throw Error("Preview assets unavailable"); return r.json()})));
const state = {data, guide, fullscreen: false};
const listeners = new Map();
const model = {get: k => state[k], set: (k,v) => {
  if(k === "request") {state.data = {...data, request_id:v.id, error:"This is a read-only preview. Choose Run locally for the full research workspace."}; queueMicrotask(() => listeners.get("change:data")?.());}
  else state[k] = v;
}, save_changes(){}, on:(k,f)=>listeners.set(k,f), off:k=>listeners.delete(k)};
const root = document.getElementById("workspace");
function freeze() {
  root.querySelectorAll("form[data-form] input, form[data-form] button").forEach(e => {e.disabled=true; e.title="Run locally to use this feature";});
  root.querySelectorAll("input[data-field],textarea[data-field],input[data-setup],input[data-synthetic],input[data-previous-independent],select[data-annotation],input[data-reviewed],[data-ollama-model]").forEach(e => e.disabled=true);
  root.querySelectorAll("button[data-action]").forEach(e => {
    const a=e.dataset.action;
    if (/^(save$|demo$|tutorial$|interpret$|ollama-models$|attach:|export:|load:|dialog:new$|dialog:projects$)/.test(a)) {e.disabled=true; e.title="Available in the local app — use Run locally";}
  });
}
// Observe newly navigated documents; state remains the curated snapshot.
new MutationObserver(freeze).observe(root,{childList:true,subtree:true});
render({model,el:root}); freeze();
}
export const ready = boot().catch(error => {
  console.error("Preview startup failed", error);
  const root = document.getElementById("workspace");
  root.textContent = "The demo could not load. Refresh the page or use Run locally above. If this persists, the site may need to be redeployed.";
  root.setAttribute("role", "alert");
});
""")
    (output / "index.html").write_text(
        """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hypothesis Lab · Demo preview</title><link rel="stylesheet" href="./workspace.css"><style>body{margin:0;background:#18181b;color:#e5e3ed;font:14px system-ui}.preview-bar{padding:12px 20px;display:flex;gap:18px;align-items:center;border-bottom:1px solid #393440;flex-wrap:wrap}.preview-bar span{flex:1;color:#aaa5b9}.preview-bar a{color:#c1a2ff}#workspace>.hl-app{height:calc(100dvh - 63px);min-height:600px}.hl-status{display:none}</style><header class="preview-bar"><strong>Hypothesis Lab / Preview</strong><span>Read-only demo · real literature · synthetic observations. Explore files, Help, and the walkthrough.</span><a href="./run-locally.html">Run locally →</a></header><div id="workspace"><p>Loading demo preview…</p></div><script type="module" src="./preview.mjs"></script></html>"""
    )
    repo = html.escape(repository)
    (
        output / "run-locally.html"
    ).write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Run Hypothesis Lab locally</title><style>body{{background:#18181b;color:#e5e3ed;font:16px/1.7 system-ui;max-width:850px;margin:60px auto;padding:24px}}a{{color:#b99aff}}pre{{background:#222127;padding:22px;border:1px solid #393440;border-radius:8px;overflow:auto}}h1{{font-size:38px}}small{{color:#aaa5b9}}</style><a href="./index.html">← Explore the preview</a><h1>Your research. Your workspace.</h1><p>The preview shows the interface and bundled investigation. Run the full Marimo application to create investigations, search papers, enter observations, calculate results, save locally, export reports, and interpret findings with your own Ollama models.</p><p><a href="{repo}">View repository</a> · <a href="{repo}/archive/HEAD.zip">Download source ZIP</a> · <a href="{repo}/blob/HEAD/docs/getting-started.md">Full getting-started guide</a></p><h2>1. Install and launch</h2><p>Install Git and <a href="https://docs.astral.sh/uv/getting-started/installation/">uv</a>, then run:</p><pre>git clone {repo}.git
cd {repository.rsplit("/", 1)[-1]}
uv sync --locked
uv run marimo run app.py</pre><p>Open the local URL printed by Marimo. The bundled demo works without an API key. To enable live paper search, copy <code>.env.example</code> to <code>.env</code> and add your own OpenAlex key.</p><h2>2. Optional: interpret findings with Ollama</h2><p>Install <a href="https://ollama.com/download">Ollama</a> and download a local model you choose with <code>ollama pull MODEL</code>. Start Ollama, open Analysis in the local application, refresh local models, select yours, and choose Analyze findings.</p><p>AI interpretations are reviewable drafts. The deterministic scientific model calculates the posterior separately.</p><h2>Preview capabilities</h2><p>Navigation, themes, source links, methodology, and the walkthrough work here. Editing, calculations, live search, saving, exports, practice-workspace creation, and Ollama require the local application. Nothing entered in the preview is saved.</p><small>This static site contains only the curated demo, not local databases, private notes, or API credentials.</small></html>''')
    print(f"Static preview built in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/pages"))
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    build(args.output, args.repository.rstrip("/"))
