/** Runtime smoke checks for the dependency-free frontend. No browser automation. */
import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";
const [bundlePath, statePath] = process.argv.slice(2);
if (!bundlePath || !statePath)
  throw new Error(
    "Usage: node scripts/check-ui.mjs <bundled.mjs> <widget-state.json>",
  );
const {
  default: { render },
} = await import(`file://${bundlePath}`);
const fixture = JSON.parse(await readFile(statePath, "utf8"));
const handlers = {};
const storage = new Map();
globalThis.localStorage = {
  getItem: (k) => storage.get(k),
  setItem: (k, v) => storage.set(k, v),
};
globalThis.document = {
  activeElement: null,
  addEventListener() {},
  createElement() {
    return { click() {} };
  },
};
globalThis.window = {
  addEventListener() {},
  matchMedia: () => ({ matches: true }),
};
const fakeVideo = {
  currentTime: 0,
  paused: true,
  readyState: 1,
  play() {
    this.paused = false;
    return Promise.resolve();
  },
  addEventListener() {},
};
const el = {
  innerHTML: "",
  isConnected: true,
  contains: () => false,
  querySelector: (selector) =>
    selector === "#hl-walkthrough-video" &&
    el.innerHTML.includes('id="hl-walkthrough-video"')
      ? fakeVideo
      : null,
  querySelectorAll: () => [],
  addEventListener: (name, fn) => (handlers[name] = fn),
};
let data = fixture,
  receiver,
  request;
const model = {
  get: (key) =>
    key === "fullscreen" ? false : key === "guide" ? fixture.guide : data,
  on: (_, fn) => (receiver = fn),
  off() {},
  set: (_, value) => (request = value),
  save_changes() {},
};
const dispose = render({ model, el });
function click(action) {
  handlers.click({
    target: { closest: () => ({ dataset: { action } }) },
    preventDefault() {},
  });
}
for (const [page, expected] of Object.entries({
  help: "All guides and reference documentation live here",
  question: "Scientific hypothesis",
  sources: "Search OpenAlex",
  evidence: "verbatim abstract excerpts",
  analysis: "Prior sensitivity",
  notes: "research-notes.md",
  graph: "Literature map",
  report: "REPRODUCIBILITY RECORD",
  methodology: "Separate interpretation from inference",
})) {
  click(`page:${page}`);
  assert(el.innerHTML.includes(expected), `${page} renders expected content`);
  assert(
    !el.innerHTML.includes("undefined"),
    `${page} has no undefined display values`,
  );
}
click("help:overview");
assert(el.innerHTML.includes("Help home"));
assert(el.innerHTML.includes("Help &amp; docs"));
click("help:setup");
assert(el.innerHTML.includes("You do not need to know the posterior"));
click("help:methodology");
assert(el.innerHTML.includes("Separate interpretation from inference"));
assert(!el.innerHTML.includes('data-action="page:methodology" role="tab"'));
click("help:walkthrough");
assert(el.innerHTML.includes("Load practice example"));
assert(el.innerHTML.includes("Full video transcript"));
if (fixture.guide.video_src) {
  assert(el.innerHTML.includes('<video id="hl-walkthrough-video" controls'));
  click("chapter:72");
  assert.equal(fakeVideo.currentTime, 72);
  assert.equal(fakeVideo.paused, false);
}
click("theme");
assert(el.innerHTML.includes('data-theme="light"'));
if (fixture.guide.video_src) assert.equal(fakeVideo.currentTime, 72);
click("page:question");
click("theme");
assert(el.innerHTML.includes('data-theme="dark"'));
click("inspector");
assert(el.innerHTML.includes("hide-inspector"));
click("explorer");
assert(el.innerHTML.includes("hide-explorer"));
click("command");
assert(el.innerHTML.includes('role="dialog"'));
click("close-dialog");
click("dialog:new");
assert(el.innerHTML.includes("Investigation name"));
assert(
  el.innerHTML.includes("First time here? Watch the 2-minute walkthrough"),
);
click("close-dialog");
click("dialog:link");
assert(el.innerHTML.includes("DOI or research URL"));
click("close-dialog");
click("save");
assert(el.innerHTML.includes("Save working copy"));
click("close-dialog");
click("page:sources");
data = {
  ...fixture,
  workspace: {
    ...fixture.workspace,
    publications: [
      {
        id: "evil",
        title: "<img src=x onerror=alert(1)>",
        authors: ["<script>alert(1)</script>"],
        url: "javascript:alert(1)",
        provider: "Researcher",
        year: 2026,
        abstract: null,
      },
    ],
  },
};
receiver();
assert(!el.innerHTML.includes("<img src=x"));
assert(!el.innerHTML.includes('href="javascript:'));
click("page:analysis");
assert(el.innerHTML.includes("What event are you measuring?"));
assert(el.innerHTML.includes("Do you have observations to analyze?"));
assert(el.innerHTML.includes("What do you already know?"));
click("page:question");
handlers.input({
  target: {
    dataset: { field: "hypothesis" },
    value: "A modified research question with explicit assumptions",
    type: "text",
  },
});
await new Promise((resolve) => setTimeout(resolve, 700));
assert(request.type === "update");
assert(request.workspace.hypothesis.startsWith("A modified"));
// A correction typed while an older invalid update is pending must be sent
// after its error arrives, and must not be overwritten by the old snapshot.
const firstRequest = request;
handlers.input({
  target: {
    dataset: { field: "hypothesis" },
    value: "A newer corrected research question that must be preserved",
    type: "text",
  },
});
data = {
  ...fixture,
  workspace: firstRequest.workspace,
  request_id: firstRequest.id,
  error: "Prior request was invalid",
};
receiver();
assert(el.innerHTML.includes("A newer corrected research question"));
await new Promise((resolve) => setTimeout(resolve, 120));
assert.notEqual(request.id, firstRequest.id);
assert(request.workspace.hypothesis.startsWith("A newer corrected"));
data = {
  ...fixture,
  workspace: request.workspace,
  request_id: request.id,
  error: "",
};
receiver();
assert(el.innerHTML.includes("Unsaved changes"));
click("page:sources");
click("inspect:0");
assert(!el.innerHTML.includes(" hide-inspector"));

click("page:analysis");
assert(el.innerHTML.includes("Interpret findings with Ollama"));
click("ollama-models");
assert.equal(request.type, "ollama_models");
data = {
  ...data,
  error: "",
  ollama_models: [{ name: "research:latest", digest: "abc" }],
};
receiver();
assert(el.innerHTML.includes("research:latest"));
click("interpret");
assert.equal(request.type, "interpret");
assert.equal(request.model, "research:latest");
data = {
  ...data,
  workspace: {
    ...data.workspace,
    interpretation: {
      model: "research:latest",
      created_at: "today",
      text: "<script>unsafe()</script>",
      context: {},
      input_hash: "abc",
    },
  },
  interpretation_stale: true,
};
receiver();
assert(!el.innerHTML.includes("<script>unsafe()"));
assert(el.innerHTML.includes("regenerate before relying"));
// Closing tabs preserves drafts, picks a neighbor, and supports an empty workbench.
click("page:question");
click("page:notes");
click("close-tab:question");
assert(!el.innerHTML.includes('data-action="close-tab:question"'));
assert(el.innerHTML.includes("research-notes.md"));
click("page:question");
assert(el.innerHTML.includes("A newer corrected research question"));
for (const route of [
  "question",
  "sources",
  "analysis",
  "help",
  "notes",
  "evidence",
  "graph",
  "report",
])
  click(`close-tab:${route}`);
assert(el.innerHTML.includes("No open documents"));
click("page:question");
assert(el.innerHTML.includes('data-action="close-tab:question"'));
assert(el.innerHTML.includes("A newer corrected research question"));
dispose();
console.log(
  "Frontend runtime checks passed: 8 workspace/help views, nested docs, guided setup, Ollama discovery/interpretation, video help, theme, pane toggles, dialogs, safe text/links, editing & request bridge.",
);
