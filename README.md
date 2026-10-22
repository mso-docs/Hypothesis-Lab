# Hypothesis Lab

A local scientific research IDE built with Python and Marimo. An Obsidian-inspired workspace connects a research question, real linked publications, reviewable evidence, explicit Bayesian models, and reproducible reports.

## Run

```bash
uv sync
uv run marimo run app.py
```

Open the printed local URL. If an older instance is running, stop and restart it to load the redesign, or use `uv run marimo run app.py --port 2720`.

For notebook development: `uv run marimo edit app.py`. App mode uses the full viewport; notebook mode keeps the workspace inline beside the code.

## The workspace

- **Explorer:** actual investigation files; selecting a file opens a document tab.
- **Command palette:** `Ctrl/Cmd K` to jump to files or actions.
- **Context inspector:** source provenance alongside literature and a read-only analysis summary. Set up the model in the central guided flow. Both panes can be collapsed.
- **Save:** `Ctrl/Cmd S`, or the toolbar action. Named investigations are stored locally in SQLite.
- **Appearance:** the sun/moon toolbar control toggles dark and light themes and remembers the choice in this browser.

The first launch opens a guided extreme-heat investigation. Follow the five-step guide, inspect its real papers and original DOI links, compare the regional counterpoint, review verbatim excerpts, and experiment with priors. Its 20 events in 100 observations are **synthetic teaching data**, not measurements extracted from the papers.

**Save a copy** preserves your edits as a separate investigation. **New investigation** starts with an empty question, no papers, and no observations. The original guided demo remains available in the explorer. Reopen your saved investigations from the project selector.

## Video walkthrough and help

The question-mark tool opens **Help & docs**. The video, starting-assumptions guide, and methodology are nested there and share one Help tab. Choose **Watch getting started** below **New investigation** to jump directly to the video. The bundled 2:02 illustrated video has chapter seeking, captions, a full transcript, and an offline **Load practice example** action. It follows a separate radish-seed hypothesis from setup to source review, modeling, notes, and export. The example uses a real linked paper and explicitly synthetic observations.

See [the written walkthrough](docs/getting-started.md) for the complete steps and video rebuild instructions. The original climate demo and existing saved investigations remain separate.

## OpenAlex and research links

Put the key in a local `.env` file:

```dotenv
OPENALEX_API_KEY=your-key
```

The app reads `.env` automatically at startup. An existing process environment value takes precedence. The key stays in Python; widget state, frontend code, exports, and error messages do not include it. Restart after changing the key.

In **literature**, search by topic, title, or author. Add selected results to the current investigation; searches do not replace existing sources. **Add a link** accepts DOI identifiers, DOI URLs, OpenAlex URLs, or other public HTTPS research links. DOI/OpenAlex links resolve publication metadata. Other HTTPS links are saved as unverified references without fetching arbitrary hosts or inventing metadata.

No API key or network request is needed to open the curated starter. The three bundled publication snapshots were verified against OpenAlex on October 22, 2026. Missing abstracts remain missing.

## Scientific boundaries

Qualitative annotations never alter numerical inference. Excerpts preserve the first substantive abstract sentence verbatim, with source attribution and a review flag. This is conservative deterministic extraction, not semantic LLM analysis. Marking an excerpt reviewed records a researcher's action; it does not verify a study or its conclusions.

The Beta–Binomial model assumes independent Bernoulli trials, a consistent event definition, and a constant probability. The starter uses Beta(2,8) and four synthetic batches, yielding Beta(22,88), posterior mean 0.20, and a 95% credible interval of approximately 13.1%–27.9%. The model estimates event probability; it does not establish temporal trends or causation. Normalized likelihood is labeled separately from the posterior.

In **analysis**, follow three questions: define the event, say whether you have observations, and choose what you already know. **Little previous knowledge** uses a documented Beta(1,1) starting assumption; **Previous study** accepts separate historical counts with a source and independence confirmation; **Custom** exposes advanced alpha/beta parameters. The app calculates the posterior automatically. With **Not yet**, numerical analysis stays pending while source review, notes, saving, and source-review exports remain available. Once ready, inspect sequential updates and prior sensitivity, or compare two explicitly specified fixed event probabilities. New researcher-entered counts are not independently verified. Overlapping datasets and spatial/temporal dependence require review before pooling.

## Architecture

```text
app.py                         Thin Marimo entry point
src/hypothesis_lab/
  config.py                    Local environment loading
  models.py                    Pydantic scientific contracts
  demo.py                      Real citations + synthetic teaching scenario
  services.py                  Investigation creation and local workflows
  persistence.py               SQLite repository boundary
  retrieval/openalex.py        Search, DOI resolution, conservative extraction
  inference/                   Deterministic Bayesian mathematics
  reporting.py                 Reproducibility snapshots and Markdown
  ui/widget.py                 Validated request/state bridge to Python
  ui/frontend/
    workspace.js               Document views, navigation, commands, editing
    workspace.css              Scoped theme/layout/interaction styles
    icons.js                   Consistent dependency-free SVG icons
    charts.js                  SVG plots of Python-computed density samples
```

The frontend does not compute posterior probabilities or store API credentials. Python owns validation, inference, retrieval, and persistence. SVG charts consume SciPy-computed samples, including adaptive quantile points for narrow posteriors. The small frontend modules are assembled for Marimo's supported AnyWidget interface without a separate frontend framework or build server. Keep external JavaScript dependencies out of these modules unless the bundling strategy is deliberately extended.

## Checks

```bash
uv run pytest
uv run marimo check --strict app.py
# Optional frontend runtime checks; requires Node.js 22+
uv run python scripts/check_ui.py
```

The frontend checks exercise all eight document views, appearance, pane toggles, dialogs, escaping, editing, and the message bridge using a minimal test host. They do not replace visual browser QA.

## Public submission link

Publication waits for design approval. [Deployment notes](docs/deployment.md) describe a sanitized interactive GitHub Pages / static Vercel demo using browser Python, and the server-side changes needed for public live search. The local Marimo server is not a Vercel serverless function. No deployment has been performed.

## Next scientific extensions

Verified CSV observation import, richer evidence extraction through optional providers, additional statistical models, explicit dependence diagnostics, and external snapshot import. Keep source interpretation separate from the inference engine.

Apache-2.0 · Mac Labs AI
