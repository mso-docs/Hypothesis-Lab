/** Execute the shipped Pages entry point against a minimal non-browser host. */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
const directory = process.argv[2];
if (!directory)
  throw Error("Usage: node scripts/check-static.mjs <build-directory>");
const handlers = {};
const root = {
  innerHTML: "Loading demo preview…",
  textContent: "",
  isConnected: true,
  contains: () => false,
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener: (name, fn) => (handlers[name] = fn),
  setAttribute() {},
};
globalThis.document = {
  getElementById: () => root,
  activeElement: null,
  addEventListener() {},
};
globalThis.window = {
  addEventListener() {},
  matchMedia: () => ({ matches: true }),
};
globalThis.localStorage = { getItem: () => null, setItem() {} };
globalThis.MutationObserver = class {
  observe() {}
};
globalThis.fetch = async (url) => ({
  ok: true,
  json: async () => JSON.parse(await readFile(url, "utf8")),
});
const entry = pathToFileURL(resolve(directory, "preview.mjs"));
const { ready } = await import(entry.href);
await ready;
assert(
  root.innerHTML.includes("Scientific hypothesis"),
  "The shipped entry point must render the workspace",
);
assert.equal(root.textContent, "");
handlers.click({
  target: { closest: () => ({ dataset: { action: "help:overview" } }) },
  preventDefault() {},
});
assert(
  root.innerHTML.includes("All guides and reference documentation live here"),
);
const click = (action) =>
  handlers.click({
    target: { closest: () => ({ dataset: { action } }) },
    preventDefault() {},
  });
click("close-tab:help");
assert(!root.innerHTML.includes('data-action="close-tab:help"'));
for (const route of ["question", "sources", "analysis"])
  click(`close-tab:${route}`);
assert(root.innerHTML.includes("No open documents"));
click("help:overview");
assert(root.innerHTML.includes('data-action="close-tab:help"'));
console.log(
  "Static entry-point startup, Help navigation, and tab closing passed.",
);
