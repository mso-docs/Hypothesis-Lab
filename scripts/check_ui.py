"""Prepare public-only fixture state and check the frontend without a browser.

Requires Node.js 22+. This checks runtime rendering and message wiring, not pixels
or the browser's WebSocket transport; browser QA remains a separate check.
"""

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from hypothesis_lab.ui.widget import ResearchWorkspace, frontend_source

with TemporaryDirectory(prefix="hypothesis-ui-") as directory:
    temporary = Path(directory)
    bundle = temporary / "workspace.mjs"
    fixture = temporary / "state.json"
    bundle.write_text(frontend_source())
    component = ResearchWorkspace()
    fixture.write_text(json.dumps({**component.data, "guide": component.guide}))
    subprocess.run(["node", "--check", str(bundle)], check=True)
    subprocess.run(
        [
            "node",
            str(Path(__file__).with_name("check-ui.mjs")),
            str(bundle),
            str(fixture),
        ],
        check=True,
    )
