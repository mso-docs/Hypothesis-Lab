# Public static preview and full local application

The submission site is a **read-only static preview**, not a hosted scientific backend. It reuses the application frontend with allowlisted bundled demo findings. Visitors can explore files, sources and citations, themes, Help, methodology, and the captioned walkthrough. **Run locally** links to the repository, source ZIP, documentation, and launch instructions.

Editing, new investigations, calculations, live OpenAlex search, SQLite persistence, report exports, and Ollama interpretation belong to the local Marimo app. The preview disables those controls and labels its synthetic observations. It requires no Python browser runtime, API credentials, database, or inference server.

## Build and review

```bash
uv sync --locked
uv run python scripts/build_static_demo.py --repository https://github.com/OWNER/REPOSITORY
python -m http.server 8000 --directory dist/pages
```

The builder writes only an explicit demo snapshot, calculated demo curves, frontend modules/styles, media assets, a preview adapter, and static install documentation. It does not enumerate or export saved investigations. Paths are relative so a GitHub project subpath works. Build outputs are ignored by Git.

Review navigation, themes, source links, disabled actions, video playback/captions/chapter seeking, responsive layout, and Run locally links in a browser before publication. Automated runtime checks do not establish visual browser compatibility.

## GitHub Pages

The `.github/workflows/pages.yml` workflow runs on every push to `main`, checks the static preview, and builds and deploys only `dist/pages` using GitHub's Pages artifact/deployment actions. To enable it:

1. Push the reviewed repository, keeping `.env`, local databases, and personal research out of Git.
2. Set **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Push changes to `main` to deploy automatically. To rebuild without a new commit, use **Actions → Publish static preview → Run workflow**.
4. Check the deployment URL and browser-test the published preview.

GitHub Pages hosts static HTML/CSS/JavaScript; it does not run this application's Python backend. [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

## Vercel

The same `dist/pages` directory can be deployed as a static Vercel project with no runtime backend. Build it before upload, or configure the Python/uv build environment explicitly. Do not point Vercel at `marimo run app.py` as a function entry point.

A future full hosted version requires a deliberate backend deployment and durable storage strategy. Vercel now documents WebSocket support in public beta, with pinned instances, reconnect behavior and maximum connection durations. That makes old blanket claims that Vercel cannot support WebSockets outdated; it does not establish compatibility with this app's Marimo session lifecycle. See [Vercel WebSocket guidance](https://vercel.com/kb/guide/do-vercel-serverless-functions-support-websocket-connections) and [Python runtime](https://vercel.com/docs/functions/runtimes/python).

A public server's localhost refers to that server, not the visitor's computer. The local Ollama integration is available when users run the repository. It is deliberately unavailable in the public preview.

## Credentials and publication

Never include `.env`, API keys, local SQLite databases, private notes, caches, or arbitrary workspace files in a published artifact. Only the builder's `dist/pages` output belongs in the static deployment. The full application keeps `OPENALEX_API_KEY` in the local Python process.

Once this workflow is pushed to `main` and Pages is configured, future pushes publish automatically. Pull requests and pushes to other branches do not deploy the preview.
