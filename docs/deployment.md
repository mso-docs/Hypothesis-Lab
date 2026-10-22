# Public demo deployment

Deployment waits for approval of the redesigned interface. Nothing in this document creates a hosted site, account, or public link.

## Recommended route

Keep the full application local for research, credentials, and SQLite storage. Prepare a separate, sanitized Marimo WebAssembly demo for a GitHub Pages submission link. The public demo should open the same curated investigation, allow changing inference parameters and starting an empty investigation, and offer JSON/Markdown downloads. Label its observations synthetic and identify its real literature sources independently.

Marimo supports interactive browser execution through Pyodide and static hosting on GitHub Pages. This preserves the Python scientific engine instead of duplicating Bayesian calculations in JavaScript. See [Marimo WebAssembly](https://docs.marimo.io/guides/wasm/).

| Route | Suitable behavior | Required adaptation |
| --- | --- | --- |
| Local Marimo | Full research workflow, live OpenAlex, local saves | Load the local environment before server-side retrieval |
| GitHub Pages / static Vercel | Interactive, curated demo with browser Python | Bundle package/assets, remove secrets, adapt saving and retrieval |
| Vercel companion frontend + HTTP API | Live public search with a private server-side key | Separate bounded HTTP endpoints, quota controls, deliberate storage policy |
| Persistent Python server | Full hosted Marimo application | A host supporting the app's session lifecycle and WebSocket transport |

## Static export preparation

The installed Marimo version at this review was **0.25.2**. Its actual `marimo export html-wasm --help` supports `--mode run`, `--no-show-code`, `--no-execute`, directory exports, and `--offline`. These flags do not establish that this application already works in a browser.

After creating a browser-compatible entry point, the intended build is:

```bash
uv run marimo export html-wasm demo_app.py \
  --mode run --no-show-code --no-execute -o dist/demo
python -m http.server 8000 --directory dist/demo
```

`demo_app.py` is a proposed entry point, not an existing file. Do not publish an export of the full local application without the checks below. `--no-execute` avoids capturing local outputs during this build; source code remains public even with `--no-show-code`.

A directory export is preferable here: package code, styles, and the curated source snapshot need explicit inclusion and verification. Current Marimo documents local-module bundling, configured Python paths for modules outside the notebook directory, and local wheels; single-file exports do not include all these resources. Ensure the `src/hypothesis_lab` package resolves during export. Keep non-code assets in the expected exported asset location, rather than relying on local filesystem paths. See [Marimo export documentation](https://docs.marimo.io/guides/exporting/webassembly_html/).

Compatibility work before publishing:

- Confirm the exact NumPy, SciPy, Pydantic, AnyWidget, and HTTPX dependencies install under the export's Pyodide runtime. Compiled dependencies need compatible wheels; desktop installation alone proves nothing about browser support.
- Replace server filesystem assumptions with bundled assets. Browser SQLite, if available, does not automatically persist to the user's local project directory. Use explicit downloads initially, or a tested browser-storage adapter with clear persistence behavior.
- Use the curated literature snapshot for the public first-run demo. Browser network access is subject to CORS and cannot conceal application credentials. A live search button requires a separate protected backend or an explicitly designed user-owned-key workflow.
- Verify startup, all workspace views, calculations, new-investigation behavior, light/dark appearance, exports, refresh behavior, and a GitHub project subpath in a real browser. Loading indicators must explain the initial Python/runtime download.

Do not label the export validated until these browser checks pass.

## Vercel boundaries

A static WASM directory can be hosted on Vercel as well as Pages. A Vercel Function is a request handler, not a drop-in replacement for a persistent Marimo session server. The existing `marimo run app.py` process should not simply be placed inside a function. Review current [Vercel runtime documentation](https://vercel.com/docs/functions/runtimes/python) and [platform limits](https://vercel.com/docs/limits) before implementing the companion API.

A companion API can reuse the Python retrieval/inference package for bounded HTTP requests while the frontend handles navigation. It must keep the OpenAlex key server-side, validate input, restrict result size, rate-limit public use, and avoid exposing raw provider request URLs or errors containing credentials. Local SQLite files are not a durable multiuser database for a serverless service. Keep the submission demo anonymous and ephemeral unless a separate persistence design is implemented.

## Credential and research-data boundary

`OPENALEX_API_KEY` belongs only in the local process environment or a hosting platform's server-side secret settings. Never put it in HTML, browser Python, JavaScript, public build variables, notebook outputs, exported snapshots, or committed `.env` files. A build-time environment variable becomes public if code embeds it into generated files.

Publish only an allowlisted demo snapshot containing citation metadata, source URLs, reviewed excerpts, synthetic observations, and explanatory notes. Do not upload the local SQLite database, personal notes, `.env`, caches, logs, or arbitrary workspace directories. Review the export directory and repository changes before publishing. No API key is needed to view the curated demo.

## Approval checkpoint

Once the design is approved, build and browser-test the sanitized artifact locally. Present its limitations and chosen host, then publish the reviewed artifact using the user's authorized repository/account. The submitted link should identify whether users are running the browser demo or the full local research application.

## Custom frontend packaging

The redesigned workspace uses an AnyWidget bridge in `ui/widget.py`. Its ESM source is assembled from `ui/frontend/icons.js`, `charts.js`, and `workspace.js`; its stylesheet is `ui/frontend/workspace.css`. These files are runtime package assets, not optional development files. Wheel builds and browser exports must include all four files, plus curated demo data and any other paths read by Python.

The current ESM bundler intentionally strips the known single-line local imports and named exports before concatenation, retaining the final default `render` export. Adding multiline imports, external JavaScript dependencies, duplicate top-level identifiers, or a second default export requires replacing or extending that bundler. Validate the assembled module with `node --check`, then test its rendering and widget synchronization in a browser. A JavaScript syntax check alone does not verify AnyWidget transport.

A public WASM build must also install compatible `anywidget` and `traitlets` packages and verify bidirectional widget state, async retrieval failure behavior, and stylesheet loading. The local Python bridge currently invokes SQLite-backed services and reads frontend files at import time; those paths require an explicit browser storage/assets adaptation. Keep the server-only OpenAlex adapter out of browser credential flows. The custom frontend does not by itself make the full local app a static deployable app.

## Getting-started media

Include `ui/frontend/media/` (MP4, poster JPG, captions VTT, chapters VTT) and `tutorial.py` in the public demo package. The local AnyWidget serves these bundled assets as data URLs, without using the OpenAlex key or reading user investigations. Preserve native video controls, chapter seeking, the full transcript, and the practice-workspace action when adapting the public build. Verify media playback and caption loading against the deployed Content Security Policy in a real browser.
