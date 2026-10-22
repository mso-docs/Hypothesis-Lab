/** Presentation and transient navigation only. All scientific results come from Python. */
import { icon } from "./icons.js";
import { densityChart, sequenceChart, evidenceGraph } from "./charts.js";

const documents = {
  help: {
    file: "Help & docs",
    title: "Help & docs",
    icon: "help",
    section: "Learn",
  },
  question: {
    file: "hypothesis.md",
    title: "Research question",
    icon: "file",
    section: "Define",
  },
  sources: {
    file: "literature",
    title: "Literature",
    icon: "book",
    section: "Discover",
  },
  evidence: {
    file: "evidence.json",
    title: "Evidence review",
    icon: "gitBranch",
    section: "Review",
  },
  analysis: {
    file: "analysis.py",
    title: "Bayesian analysis",
    icon: "activity",
    section: "Model",
  },
  notes: {
    file: "research-notes.md",
    title: "Research notes",
    icon: "note",
    section: "Document",
  },
  graph: {
    file: "source-map",
    title: "Source map",
    icon: "graph",
    section: "Explore",
  },
  report: {
    file: "report.md",
    title: "Investigation report",
    icon: "download",
    section: "Export",
  },
};
const h = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const pct = (value) => `${(Number(value) * 100).toFixed(1)}%`;
const safeHref = (value) =>
  /^https:\/\//i.test(String(value ?? "")) ? h(value) : "";
const button = (action, label, glyph, primary = false, extra = "") =>
  `<button class="hl-button${primary ? " hl-primary" : ""}" data-action="${action}" ${extra}>${glyph ? icon(glyph) : ""}${h(label)}</button>`;
const tool = (action, label, glyph, active = false) =>
  `<button class="hl-icon-button${active ? " hl-active" : ""}" data-action="${action}" aria-label="${h(label)}" title="${h(label)}">${icon(glyph)}</button>`;
const field = (
  label,
  path,
  value,
  {
    type = "text",
    hint = "",
    step = "any",
    min = "",
    rows = 0,
    disabled = false,
  } = {},
) =>
  `<div class="hl-field"><label for="hl-${path}">${h(label)}</label>${rows ? `<textarea id="hl-${path}" data-field="${path}" rows="${rows}" ${disabled ? "disabled" : ""}>${h(value)}</textarea>` : `<input id="hl-${path}" data-field="${path}" type="${type}" value="${h(value)}" ${type === "number" ? `step="${step}" min="${min}"` : ""} ${disabled ? "disabled" : ""}>`}${hint ? `<small>${h(hint)}</small>` : ""}</div>`;
const empty = (
  glyph,
  title,
  description,
  action = "sources",
  label = "Find literature",
) =>
  `<div class="hl-empty">${icon(glyph, 30)}<h3>${h(title)}</h3><p>${h(description)}</p>${button(`page:${action}`, label, "arrowRight")}</div>`;
const note = (content, glyph = "info") =>
  `<div class="hl-banner">${icon(glyph)}<div>${content}</div></div>`;
function markdownPreview(value) {
  return h(value)
    .split("\n")
    .map((row) => {
      if (/^### /.test(row)) return `<h3>${row.slice(4)}</h3>`;
      if (/^## /.test(row)) return `<h2>${row.slice(3)}</h2>`;
      if (/^# /.test(row)) return `<h2>${row.slice(2)}</h2>`;
      if (/^- /.test(row)) return `<p>• ${row.slice(2)}</p>`;
      return `<p>${row.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>") || "&nbsp;"}</p>`;
    })
    .join("");
}

export function render({ model, el }) {
  let server = model.get("data");
  const guide = model.get("guide") || { chapters: [] };
  let current = structuredClone(server.workspace);
  let page = "question";
  let openTabs = ["question", "sources", "analysis"];
  let selectedSource = 0;
  let selectedModel = "";
  let helpTopic = "overview",
    helpExpanded = false;
  let dirty = false,
    busy = false,
    pending = "",
    localError = "",
    invalidModel = false;
  let revision = 0,
    sentRevision = 0,
    hideInspector = false,
    hideExplorer = false,
    returnFocus = null;
  let dialog = "",
    filter = "",
    sourceFilter = "",
    showInspector = false,
    showExplorer = false,
    notePreview = false;
  let toast = "",
    toastTimer,
    updateTimer,
    lastDownload = "",
    downloadFormat = "json";
  const expandedDetails = new Set();
  let theme = "dark";
  try {
    theme = localStorage.getItem("hypothesis-lab-theme") || "dark";
  } catch {}
  const abort = new AbortController();
  const signal = abort.signal;

  function navigate(next) {
    if (next === "methodology") {
      helpTopic = "methodology";
      next = "help";
    } else if (next === "help") helpTopic = "overview";
    if (next === "help") helpExpanded = true;
    if (!documents[next]) return;
    page = next;
    if (!openTabs.includes(next)) openTabs.push(next);
    showExplorer = false;
    dialog = "";
    draw(false);
  }
  function notify(message) {
    toast = message;
    clearTimeout(toastTimer);
    draw();
    toastTimer = setTimeout(() => {
      toast = "";
      draw();
    }, 4000);
  }
  function send(type, extra = {}) {
    clearTimeout(updateTimer);
    if (busy) return;
    const id =
      globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;
    pending = type;
    sentRevision = revision;
    busy = true;
    localError = "";
    model.set("request", {
      id,
      type,
      workspace: structuredClone(current),
      ...extra,
    });
    model.save_changes();
    draw();
  }
  function edit(path, value) {
    const parts = path.split(".");
    if (parts.length === 2) {
      current[parts[0]] ||= {};
      current[parts[0]][parts[1]] = value;
    } else current[path] = value;
    if (path.startsWith("prior.")) current.setup.prior_mode = "custom";
    if (path === "trials" || path === "events")
      current.observation_batches = [];
    dirty = true;
    revision += 1;
    localError = "";
    const state = el.querySelector("[data-dirty-status]");
    if (state) state.textContent = "Unsaved changes";
    clearTimeout(updateTimer);
    updateTimer = setTimeout(() => send("update"), 650);
  }
  function activeAnalysis() {
    return invalidModel ? null : server.analysis;
  }
  function summaryStats() {
    const a = activeAnalysis(),
      ready = a?.ready;
    const items = [
      [
        "Updated estimate",
        ready ? pct(a.mean) : "—",
        "Posterior · calculated by the app",
      ],
      [
        "95% credible interval",
        ready ? `${pct(a.interval[0])} – ${pct(a.interval[1])}` : "—",
        "Equal-tailed interval",
      ],
      [
        "Observations",
        current.setup.data_mode === "literature_only"
          ? "Not yet"
          : String(current.trials || 0),
        current.setup.data_mode === "literature_only"
          ? "Numerical analysis pending"
          : `${current.events || 0} events · ${current.synthetic ? "synthetic" : "researcher-entered"}`,
      ],
      [
        "Linked sources",
        String(current.publications.length),
        "Literature context",
      ],
    ];
    return `<div class="hl-stats">${items.map(([label, value, sub]) => `<div class="hl-stat"><label>${label}</label><strong>${value}</strong><small>${sub}</small></div>`).join("")}</div>`;
  }
  function workflow() {
    return `<div class="hl-workflow" aria-label="Investigation workflow">${[
      ["question", "Define"],
      ["sources", "Find papers"],
      ["evidence", "Review"],
      ["analysis", "Model"],
      ["report", "Export"],
    ]
      .map(
        ([route, label], i) =>
          `<button class="hl-step${route === page ? " hl-active" : ""}" data-action="page:${route}"><span>${i + 1}</span>${label}</button>`,
      )
      .join("")}</div>`;
  }
  function pageHeader() {
    const doc =
      page === "help"
        ? {
            ...documents.help,
            title: {
              overview: "Help & docs",
              walkthrough: "Getting started",
              setup: "Starting assumptions",
              methodology: "Model methodology",
            }[helpTopic],
          }
        : documents[page];
    return `<div class="hl-document-head"><div><div class="hl-source-meta">${h(doc.section.toUpperCase())} <span> / </span> ${page === "help" ? '<span class="hl-tag">Documentation</span>' : current.is_demo ? '<span class="hl-badge">Guided demo</span>' : '<span class="hl-tag">Investigation</span>'}</div><h1>${h(doc.title)}</h1><p>${h({ question: "A testable question. A traceable path from sources to uncertainty.", sources: "Find papers, attach sources, and inspect the original research.", evidence: "Review what the source actually says before interpreting it.", analysis: "Explicit observations and assumptions. Deterministic calculations.", notes: "A working record of definitions, decisions, and open questions.", graph: "Explore the sources connected to this research question.", report: "A portable record of your sources, assumptions, and calculations.", methodology: "Understand the model before interpreting its results.", help: "Watch the workflow, follow the chapters, then try the practice investigation." }[page])}</p></div>${page === "sources" ? button("dialog:link", "Add a link", "link") : page === "report" ? button("export:markdown", "Export report", "download", true, activeAnalysis()?.export_ready ? "" : "disabled") : ""}</div>`;
  }
  function questionDocument() {
    const a = activeAnalysis();
    return `${current.is_demo ? `<div class="hl-onboarding"><div class="hl-panel-head"><h3>${icon("flask")} Start with a real research workflow</h3><span class="hl-badge">5 steps</span></div><p>Explore three linked papers, review their findings, and test a Bayesian model. The observations are synthetic teaching data.</p>${workflow()}<div class="hl-toolbar">${button("page:sources", "Explore the papers", "arrowRight", true)}${button("dialog:new", "Start your own", "plus")}</div></div>` : workflow()}
      <section class="hl-panel"><div class="hl-panel-head"><h2>${icon("file")} Scientific hypothesis</h2><small>Editable · plain language</small></div>${field("What are you investigating?", "hypothesis", current.hypothesis, { rows: 3, disabled: busy && pending !== "update", hint: "Describe a testable proposition. The app calculates updated uncertainty once suitable observations are available." })}<div class="hl-source-meta">${icon("gitBranch", 13)} ${current.publications.length} sources connected <span>·</span> ${current.evidence.filter((e) => !e.requires_review).length} excerpts reviewed</div></section>
      <section class="hl-setup-intro"><div><h3>Set up your analysis</h3><p>No posterior to supply. Define your event, tell us whether you have observations, and choose your starting assumptions.</p></div>${button("page:analysis", "Open guided setup", "arrowRight", true)}</section>
      ${summaryStats()}
      ${a?.ready ? `<section class="hl-panel"><div class="hl-panel-head"><h2>Prior → posterior</h2>${button("page:analysis", "Open analysis", "arrowRight")}</div>${densityChart(a, { compact: true })}<div class="hl-source-meta">Beta(${a.alpha}, ${a.beta}) <span>·</span> ${current.synthetic ? "Synthetic demonstration" : "Researcher-entered counts"} <span>·</span> Qualitative annotations do not update this model</div></section>` : empty("activity", "Your investigation starts here", "Start with the guided setup, or collect papers and notes until quantitative observations are available.", "analysis", "Set up the model")}
      <div class="hl-next-actions"><button class="hl-next-action" data-action="page:sources">${icon("book", 20)}<span><strong>Inspect the literature</strong><small>${current.publications.length} linked sources</small></span>${icon("arrowRight")}</button><button class="hl-next-action" data-action="page:notes">${icon("note", 20)}<span><strong>Keep a research log</strong><small>Methods, definitions, next steps</small></span>${icon("arrowRight")}</button></div>`;
  }
  function sourceRow(p, index, { result = false } = {}) {
    const url = safeHref(p.url || p.doi);
    const attached = current.publications.some(
      (existing) => (existing.doi || existing.id) === (p.doi || p.id),
    );
    return `<article class="hl-source-row${!result && selectedSource === index ? " hl-source-selected" : ""}" data-source="${result ? "search:" : ""}${index}"><div class="hl-source-meta"><span class="hl-source-number">${String(index + 1).padStart(2, "0")}</span><span>${h(p.year || "n.d.")}</span><span>${h(p.provider)}</span>${!p.abstract ? '<span class="hl-tag">No abstract</span>' : ""}</div><h3>${url ? `<a href="${url}" target="_blank" rel="noopener noreferrer">${h(p.title)}</a>` : h(p.title)}</h3><div class="hl-source-meta">${h((p.authors || []).join(", ") || "Authors unavailable")}</div>${p.abstract ? `<details class="hl-source-abstract" data-detail="${result ? "result" : "source"}-${h(p.id)}"><summary>Read abstract</summary><p>${h(p.abstract)}</p></details>` : `<p class="hl-note">${p.provider?.startsWith("Researcher link") ? "Research link preserved. No publication metadata or claims inferred." : "The provider has no abstract for this paper. No excerpt has been extracted."}</p>`}<div class="hl-source-actions">${url ? `<a class="hl-link" href="${url}" target="_blank" rel="noopener noreferrer">${icon("external", 13)} Open original source</a>` : ""}${result ? button(`attach:${index}`, attached ? "Added" : "Add to investigation", attached ? "check" : "plus", false, attached || busy ? "disabled" : "") : button(`inspect:${index}`, "Inspect source", "panelRight")}</div></article>`;
  }
  function sourcesDocument() {
    const papers = current.publications.filter((p) =>
      `${p.title} ${p.authors.join(" ")}`
        .toLowerCase()
        .includes(sourceFilter.toLowerCase()),
    );
    return `<form data-form="search" class="hl-search-form"><div class="hl-search-box">${icon("search")}<input name="query" id="hl-literature-query" type="search" placeholder="Search by topic, paper title, or author…" value="${h(current.search_query || "")}" aria-label="Search OpenAlex" ${busy && pending !== "update" ? "disabled" : ""}><kbd>↵</kbd></div>${button("submit", "Search OpenAlex", "search", true, busy ? "disabled" : 'type="submit"')}</form>
      ${server.search_results?.length ? `<section class="hl-panel"><div class="hl-panel-head"><h2>Search results <span class="hl-badge">${server.search_results.length}</span></h2>${button("clear-search", "Dismiss results", "close")}</div>${server.search_results.map((p, i) => sourceRow(p, i, { result: true })).join("")}</section>` : ""}
      <div class="hl-panel-head" style="margin-top:24px"><h2>Investigation sources <span class="hl-badge">${current.publications.length}</span></h2><label class="hl-inline-filter">${icon("filter", 13)}<input id="hl-source-filter" data-local="sourceFilter" type="search" value="${h(sourceFilter)}" placeholder="Filter sources" aria-label="Filter attached sources"></label></div>
      ${current.is_demo ? note("<strong>Real papers, separate teaching data.</strong> These source snapshots came from OpenAlex. The synthetic event counts in the model were not extracted from these papers.") : ""}
      ${papers.length ? papers.map((p) => sourceRow(p, current.publications.indexOf(p))).join("") : empty("book", "Build your source library", "Search OpenAlex or add a DOI, paper URL, or research link. Your sources stay attached to this investigation.", "question", "Return to the question")}`;
  }
  function evidenceDocument() {
    return `${note("These are <strong>verbatim abstract excerpts</strong>, not AI interpretations. Review the source, choose a relationship, and mark it reviewed. Annotations never become numerical likelihoods.")}
      <div class="hl-review-summary"><span>${current.evidence.filter((e) => !e.requires_review).length} of ${current.evidence.length} excerpts reviewed</span><div class="hl-progress"><span style="width:${current.evidence.length ? (current.evidence.filter((e) => !e.requires_review).length / current.evidence.length) * 100 : 0}%"></span></div></div>
      ${
        current.evidence.length
          ? current.evidence
              .map((e, i) => {
                const p = current.publications.find(
                  (p) => p.id === e.publication_id,
                );
                return `<article class="hl-evidence-row"><div class="hl-source-meta"><span class="hl-badge">E${String(i + 1).padStart(2, "0")}</span><span>${h(e.source_location)}</span><span class="hl-tag">${e.requires_review ? "Needs review" : "Researcher reviewed"}</span></div><h3>${p ? h(p.title) : h(e.publication_id)}</h3><blockquote>${h(e.excerpt)}</blockquote><div class="hl-review-controls"><label>Relationship to hypothesis<select data-annotation="${i}" aria-label="Relationship for excerpt ${i + 1}" ${busy && pending !== "update" ? "disabled" : ""}>${["unclassified", "supporting", "contradicting", "inconclusive"].map((v) => `<option value="${v}" ${v === e.relationship ? "selected" : ""}>${v[0].toUpperCase() + v.slice(1)}</option>`).join("")}</select></label><label class="hl-check-label"><input type="checkbox" data-reviewed="${i}" ${!e.requires_review ? "checked" : ""} ${busy && pending !== "update" ? "disabled" : ""}> I reviewed this excerpt</label>${p && safeHref(p.url) ? `<a class="hl-link" href="${safeHref(p.url)}" target="_blank" rel="noopener noreferrer">${icon("external", 13)} Source</a>` : ""}</div><small class="hl-note">${h(e.extraction_method)}</small></article>`;
              })
              .join("")
          : empty(
              "gitBranch",
              "No abstract-backed excerpts yet",
              "Attach a paper with an available abstract. Sources without abstracts remain in your library, but produce no invented findings.",
            )
      }`;
  }
  function localModelPanel() {
    const models = server.ollama_models || [];
    if (!models.some((m) => m.name === selectedModel))
      selectedModel = models[0]?.name || "";
    const record = current.interpretation;
    return `<section class="hl-panel hl-local-model"><div class="hl-panel-head"><h2>Interpret findings with Ollama</h2><span class="hl-tag">Optional · local model</span></div><p class="hl-note">Choose an installed model to review your question, notes, attached abstracts, and calculated findings. Abstracts are capped at 1,800 characters each and notes at 12,000. Drafts need researcher review; statistical results stay unchanged.</p><div class="hl-toolbar">${button("ollama-models", "Refresh local models", "activity", false, busy ? "disabled" : "")}<div class="hl-field"><label for="hl-ollama-model">Installed model</label><select id="hl-ollama-model" data-ollama-model ${busy ? "disabled" : ""}>${models.length ? models.map((m) => `<option value="${h(m.name)}" ${m.name === selectedModel ? "selected" : ""}>${h(m.name)}</option>`).join("") : '<option value="">Refresh to discover models</option>'}</select></div>${button("interpret", busy && pending === "interpret" ? "Generating interpretation…" : "Analyze findings", "activity", true, !busy && selectedModel ? "" : "disabled")}</div><details data-detail="ollama-help"><summary>Set up Ollama</summary><p class="hl-note">Run the app and Ollama on the same computer. Start Ollama with <code>ollama serve</code>, install your preferred model with <code>ollama pull MODEL</code>, then refresh. Only installed local models are listed. For local-only operation, disable Ollama cloud features. No automatic cloud fallback. A hosted demo cannot use this local connection.</p></details>${record ? `<div class="hl-divider"></div><div class="hl-panel-head"><h3>Interpretation draft</h3><span class="hl-tag">Researcher review required</span></div><p class="hl-note">${h(record.model)} · ${h(record.created_at)}${server.interpretation_stale || dirty ? " · Investigation changed — regenerate before relying on this draft" : ""}</p><div class="hl-markdown">${markdownPreview(record.text)}</div><details data-detail="ollama-context"><summary>Inspect the material sent to the model</summary><pre class="hl-code">${h(JSON.stringify(record.context, null, 2))}</pre></details>` : ""}</section>`;
  }
  function analysisDocument() {
    const a = activeAnalysis();
    if (!a?.ready)
      return (
        guidedSetup() +
        localModelPanel() +
        `${note(current.setup.data_mode === "literature_only" ? "<strong>Literature review only.</strong> Collect sources, review claims, and keep notes. Numerical inference stays pending until you have suitable observations." : "<strong>Complete your setup.</strong> The app will calculate the updated estimate; you do not need to provide a posterior.")}<ul class="hl-setup-pending">${(a?.missing_setup || []).map((item) => `<li>${h(item)}</li>`).join("")}</ul><div class="hl-toolbar">${button("page:sources", "Find literature", "book")}${button("page:report", "Export source review", "download")}</div>`
      );
    return `${guidedSetup()}${localModelPanel()}${note("<strong>Updated estimate (posterior): calculated automatically.</strong> Your starting assumptions and current observations are combined below. Try alternative starting assumptions to check sensitivity.")}${summaryStats()}<section class="hl-panel"><div class="hl-panel-head"><h2>Probability distributions</h2><span class="hl-tag">Beta–Binomial</span></div>${densityChart(a)}<div class="hl-note">95% interval: ${pct(a.interval[0])}–${pct(a.interval[1])}. The likelihood is normalized for display.</div></section><section class="hl-panel"><div class="hl-panel-head"><h2>Sequential evidence</h2><small>Mean and 95% credible interval</small></div>${sequenceChart(a)}</section><section class="hl-panel"><div class="hl-panel-head"><h2>Prior sensitivity</h2><small>Same observations · different assumptions</small></div><table class="hl-table"><thead><tr><th>Prior</th><th>Posterior</th><th>Mean</th><th>95% interval</th></tr></thead><tbody>${a.sensitivity.map((s) => `<tr><td>${h(s.label)}</td><td class="hl-mono">Beta(${s.alpha}, ${s.beta})</td><td>${pct(s.mean)}</td><td>${pct(s.interval[0])}–${pct(s.interval[1])}</td></tr>`).join("")}</tbody></table></section><details class="hl-panel" data-detail="comparison"><summary>Compare two fixed event probabilities</summary><div style="margin-top:16px" class="hl-form-row">${field("H₀ · baseline p", "p0", current.p0 ?? 0.1, { type: "number", min: ".001", step: ".001", disabled: busy && pending !== "update" })}${field("H₁ · alternative p", "p1", current.p1 ?? 0.2, { type: "number", min: ".001", step: ".001", disabled: busy && pending !== "update" })}</div><div class="hl-code">log BF₁₀ = ${a.log_bayes_factor.toFixed(4)}</div><p class="hl-note">Positive values favor H₁; negative values favor H₀. This compares specified event probabilities, not the natural-language scientific claim.</p></details>${note("<strong>Model boundary:</strong> independent Bernoulli trials, a common event definition, and constant probability. Check dataset overlap and dependence before pooling observations.")}`;
  }
  function notesDocument() {
    return `<div class="hl-panel-head"><span class="hl-source-meta">Markdown · ${current.notes.length.toLocaleString()} characters</span>${button("note-preview", notePreview ? "Edit notes" : "Preview", "note")}</div>${notePreview ? `<div class="hl-markdown">${markdownPreview(current.notes)}</div>` : `<label class="hl-sr-only" for="hl-notes">Research notes</label><textarea id="hl-notes" class="hl-editor hl-notes-editor" data-field="notes" spellcheck="true" ${busy && pending !== "update" ? "disabled" : ""}>${h(current.notes)}</textarea>`}`;
  }
  function reportDocument() {
    const a = activeAnalysis(),
      ready = a?.ready;
    const canExport = a?.export_ready;
    return `${note("The export includes the original question, source metadata, verbatim excerpts, review annotations, priors, observations, notes, assumptions, and posterior calculations.")}<section class="hl-report-sheet"><div class="hl-source-meta">HYPOTHESIS LAB / REPRODUCIBILITY RECORD</div><h2>${h(current.title)}</h2><p>${h(current.hypothesis || "No hypothesis defined yet.")}</p><div class="hl-divider"></div><h3>Model summary</h3><div class="hl-code">Prior       Beta(${h(current.prior.alpha)}, ${h(current.prior.beta)})\nObservations ${current.setup.data_mode === "literature_only" ? "Not available" : `${current.events} / ${current.trials}`}\nPosterior   ${ready ? `Beta(${a.alpha}, ${a.beta})` : "Not computed"}\nMean        ${ready ? pct(a.mean) : "—"}\n95% CI      ${ready ? `${pct(a.interval[0])} – ${pct(a.interval[1])}` : "—"}</div><h3>Sources & review</h3><p>${current.publications.length} linked sources · ${current.evidence.length} excerpts · ${current.evidence.filter((e) => !e.requires_review).length} reviewed</p><h3>Limitations</h3><p>${current.synthetic ? "The observation data are synthetic teaching data." : "The researcher-entered observations have not been independently verified."} Literature classifications do not update the posterior. This model does not establish a trend or causation.</p><div class="hl-divider"></div><div class="hl-toolbar">${button("export:markdown", "Download Markdown", "download", true, canExport && !busy ? "" : "disabled")}${button("export:json", "Download JSON", "file", false, canExport && !busy ? "" : "disabled")}</div>${!ready ? '<p class="hl-note">Add a research question or sources to export. Numerical analysis is labeled pending until setup is complete.</p>' : ""}</section>`;
  }
  function methodologyDocument() {
    return `<div class="hl-markdown"><h2>Separate interpretation from inference</h2><p>Literature is scientific context. Numerical observations are entered explicitly and evaluated by deterministic Python code. A supporting label is never converted to a likelihood ratio.</p><h3>Beta–Binomial estimation</h3><div class="hl-code">p ∼ Beta(α, β)\nk | p ∼ Binomial(n, p)\np | k ∼ Beta(α + k, β + n − k)\nE[p | k] = (α + k) / (α + β + n)</div><p>The 95% credible interval uses equal-tailed quantiles of the posterior Beta distribution, computed with SciPy. The likelihood curve is normalized only for display.</p><h3>Assumptions to check</h3><ul><li>Independent Bernoulli trials, without repeated or overlapping observations.</li><li>A consistent event definition and sampling frame.</li><li>A constant event probability within the modeled sample.</li></ul><h3>What this demonstration does</h3><p>It estimates an event probability. It does not estimate temporal trends, validate a causal hypothesis, or resolve spatial dependence. The bundled literature includes regional differences that this simple model cannot express.</p><h3>Source provenance</h3><p>Demo publication metadata was retrieved from OpenAlex on October 22, 2026. The original DOI links are preserved. Missing abstracts remain missing. Extracted excerpts are the first substantive abstract sentence, retained verbatim and requiring researcher review.</p><h3>Reproducibility</h3><p>JSON exports preserve parameters, observations, source records, annotations, and results. Notes and methodology decisions travel with the report. Local saved investigations use SQLite. The API key stays in the local Python process.</p>${button("page:analysis", "Return to analysis", "arrowLeft")}</div>`;
  }
  function walkthroughDocument() {
    const stamp = (seconds) =>
      `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
    return `<section class="hl-help-intro"><div><span class="hl-badge">2-minute video guide</span><h2>${h(guide.title || "From research question to reproducible report")}</h2><p>Use a seed-germination question to learn the full investigation workflow. No API key is needed to watch or load the bundled practice example.</p></div>${button("tutorial", "Load practice example", "flask", true, busy ? "disabled" : "")}</section>
      ${guide.video_src ? `<div class="hl-video-frame"><video id="hl-walkthrough-video" controls playsinline preload="metadata" poster="${guide.poster_src}" aria-label="Getting started with Hypothesis Lab: captioned illustrated walkthrough"><source src="${guide.video_src}" type="video/mp4"><track kind="captions" src="${guide.captions_src}" srclang="en" label="English"><track kind="chapters" src="${guide.chapters_src}" srclang="en" label="Walkthrough chapters">Your browser does not support embedded video. Use the transcript below.</video></div><div class="hl-video-meta"><span>${h(guide.format)} · ${stamp(guide.duration)}</span><a class="hl-link" href="${guide.video_src}" download="hypothesis-lab-getting-started.mp4">${icon("download", 13)} Download video</a></div>` : note("The bundled walkthrough video could not be loaded. The complete transcript and practice example are available below.")}
      <section class="hl-panel hl-video-chapters"><div class="hl-panel-head"><h2>Follow the chapters</h2><small>Select a chapter to jump in the video</small></div><div class="hl-chapter-grid">${guide.chapters.map((chapter, i) => `<button class="hl-chapter" data-action="chapter:${chapter.start}" ${guide.video_src ? "" : "disabled"}><span class="hl-chapter-number">${String(i + 1).padStart(2, "0")}</span><span>${h(chapter.title)}</span><time>${stamp(chapter.start)}</time></button>`).join("")}</div></section>
      <section class="hl-panel"><div class="hl-panel-head"><h2>Try the same example</h2><span class="hl-tag">Synthetic teaching data</span></div><p class="hl-note">${h(guide.hypothesis)}</p><div class="hl-form-row"><div class="hl-code">Starting assumption: Uniform\nEvents: 34 / 50\nUpdated result: Beta(35, 17)</div><div class="hl-note"><strong>Expected result</strong><p>Mean 67.3% · 95% credible interval 54.1%–79.2%. The interval crosses 60%; the mean alone does not confirm the hypothesis.</p></div></div><p class="hl-note">The linked paper provides context under different experimental conditions. The example counts are not taken from it. Its suggested Inconclusive annotation still needs your review.</p><div class="hl-toolbar">${button("tutorial", "Load practice example", "flask", true, busy ? "disabled" : "")}${guide.source?.url ? `<a class="hl-button" href="${safeHref(guide.source.url)}" target="_blank" rel="noopener noreferrer">${icon("external")} Open example paper</a>` : ""}</div></section>
      <details class="hl-panel" data-detail="walkthrough-transcript"><summary>Full video transcript</summary><div class="hl-transcript">${guide.chapters.map((chapter) => `<section><h3><span>${stamp(chapter.start)}</span> ${h(chapter.title)}</h3><p>${h(chapter.caption)}</p>${button(`page:${chapter.page}`, "Open this workspace file", "arrowRight")}</section>`).join("")}</div></details>
      <section class="hl-panel"><div class="hl-panel-head"><h2>Common questions</h2></div><div class="hl-note"><p><strong>Do I need an OpenAlex key?</strong> No key is needed for the video or practice scenario. Live retrieval uses the server's configured key; restart the app after editing .env.</p><p><strong>Will loading practice replace my work?</strong> Unsaved edits trigger a save/discard prompt. Existing saved investigations are preserved, and practice uses a new name if its original name is already saved.</p><p><strong>Is the export a finished paper?</strong> It is a reproducible investigation report. A publication-ready manuscript still needs scientific review, a complete methods section, and the appropriate research and reporting standards.</p></div>${button("page:methodology", "Read the statistical methodology", "help")}</section>`;
  }

  function helpDocument() {
    const topics = {
      overview: "Help home",
      walkthrough: "Video walkthrough",
      setup: "Starting assumptions",
      methodology: "Model methodology",
    };
    const nav = `<nav class="hl-help-nav" aria-label="Help documentation">${Object.entries(
      topics,
    )
      .map(
        ([key, title]) =>
          `<button class="hl-button${helpTopic === key ? " hl-help-active" : ""}" data-action="help:${key}" ${helpTopic === key ? 'aria-current="page"' : ""}>${h(title)}</button>`,
      )
      .join("")}</nav>`;
    if (helpTopic === "walkthrough") return nav + walkthroughDocument();
    if (helpTopic === "methodology") return nav + methodologyDocument();
    if (helpTopic === "setup")
      return (
        nav +
        `<div class="hl-markdown"><h2>You do not need to know the posterior</h2><p>The posterior is the updated uncertainty the app calculates from your starting assumptions and current observations.</p><h3>1. Define the event</h3><p>Specify exactly what counts as a success, the eligible observations, and the sampling conditions.</p><h3>2. No quantitative data yet?</h3><p>Choose <strong>Not yet</strong>. Find papers, review excerpts, keep research notes, and export a source-review report. The app will not turn qualitative claims into invented numbers.</p><h3>3. Choose your starting assumption (prior)</h3><p><strong>Little previous knowledge:</strong> Beta(1,1) gives equal density to event probabilities between 0 and 1. It is a transparent starting assumption, not an assumption-free choice. Inspect sensitivity after adding observations.</p><p><strong>Previous study:</strong> enter historical counts and their source only when the event definition, conditions, and sampling are comparable. Confirm they do not overlap with current observations. Beta(1,1) is updated with the historical dataset before analyzing the current one; full pooling is a substantive assumption.</p><p><strong>Custom:</strong> advanced users can enter positive alpha and beta values and document their reasoning. Existing investigations preserve their saved parameters.</p><h3>Read the updated result</h3><p>The posterior mean summarizes the event probability. The credible interval shows uncertainty under the chosen model and assumptions. A mean above a threshold does not by itself confirm a scientific hypothesis.</p>${button("page:analysis", "Open guided analysis setup", "activity", true)}</div>`
      );
    return (
      nav +
      `<section class="hl-help-home"><p class="hl-note">All guides and reference documentation live here. Start with the walkthrough, learn the analysis choices, or inspect the statistical details.</p><div class="hl-help-cards">${[
        [
          "walkthrough",
          "play",
          "Getting started",
          "A captioned video, chapters, transcript, and a separate practice investigation.",
        ],
        [
          "setup",
          "activity",
          "Starting assumptions",
          "What to do when you have no prior information or no observations.",
        ],
        [
          "methodology",
          "book",
          "Model methodology",
          "The equations, assumptions, limitations, and reproducibility record.",
        ],
      ]
        .map(
          ([key, glyph, title, description]) =>
            `<button class="hl-help-card" data-action="help:${key}">${icon(glyph, 22)}<strong>${h(title)}</strong><span>${h(description)}</span><small>Open guide ${icon("arrowRight", 12)}</small></button>`,
        )
        .join("")}</div></section>`
    );
  }

  function documentContent() {
    return (
      pageHeader() +
      {
        question: questionDocument,
        sources: sourcesDocument,
        evidence: evidenceDocument,
        analysis: analysisDocument,
        notes: notesDocument,
        graph: () =>
          `${note("A map of attached sources and your annotations. Connections represent literature context, not causal or statistical certainty.")}${evidenceGraph(current)}${button("page:evidence", "Review source relationships", "gitBranch")}`,
        report: reportDocument,
        help: helpDocument,
      }[page]()
    );
  }
  function modelInspector() {
    const a = activeAnalysis();
    return `<div class="hl-inspector-heading"><h3>${icon("activity", 14)} Analysis summary</h3>${tool("inspector", "Toggle inspector", "panelRight")}</div><p class="hl-note">The posterior is the updated result. The app calculates it; you never need to supply it.</p><div class="hl-divider"></div><div class="hl-section-label">Starting assumptions</div><p class="hl-note">${h(a?.assumption_summary || "Choose a starting assumption in guided setup.")}</p><div class="hl-divider"></div><div class="hl-section-label">Current observations</div><p class="hl-note">${current.setup.data_mode === "literature_only" ? "Not available yet · literature review only" : `${current.events} events / ${current.trials} observations · ${current.synthetic ? "synthetic" : "researcher-entered"}`}</p><div class="hl-divider"></div><div class="hl-section-label">${a?.ready ? "Updated estimate · calculated" : "Numerical analysis pending"}</div>${a?.ready ? `<div class="hl-result-value">${pct(a.mean)}</div><div class="hl-note">Posterior mean event probability</div><div class="hl-result-line"><span>95% credible interval</span><strong>${pct(a.interval[0])}–${pct(a.interval[1])}</strong></div>` : `<ul class="hl-setup-pending">${(a?.missing_setup || []).map((item) => `<li>${h(item)}</li>`).join("")}</ul>`}<div class="hl-divider"></div>${button("page:analysis", "Edit analysis setup", "activity")}<button class="hl-link" style="margin-top:16px" data-action="help:setup">How starting assumptions work ${icon("help", 12)}</button>`;
  }
  function guidedSetup() {
    const setup = current.setup,
      locked = busy && pending !== "update";
    const choice = (key, value, title, description) =>
      `<label class="hl-setup-choice${setup[key] === value ? " hl-selected" : ""}"><input type="radio" name="hl-${key}" data-setup="${key}" value="${value}" ${setup[key] === value ? "checked" : ""} ${locked ? "disabled" : ""}><span><strong>${h(title)}</strong><small>${h(description)}</small></span></label>`;
    return `<section class="hl-panel hl-guided-setup"><div class="hl-panel-head"><h2>Guided analysis setup</h2><button class="hl-link" data-action="help:setup">${icon("help", 13)} Explain these choices</button></div><p class="hl-note">You provide the question and observations. The app calculates the updated estimate (posterior).</p><div class="hl-setup-step"><h3><span>1</span> What event are you measuring?</h3>${field("What counts as an event?", "success_definition", current.success_definition || "", { rows: 2, disabled: locked, hint: "For example: a visible radicle within seven days. Use the same definition for every trial." })}${field("Sampling design and conditions", "sampling_description", current.sampling_description || "", { rows: 2, disabled: locked })}</div><div class="hl-setup-step"><h3><span>2</span> Do you have observations to analyze?</h3><div class="hl-setup-choices">${choice("data_mode", "literature_only", "Not yet", "Collect papers and notes. Numerical analysis stays pending.")}${choice("data_mode", "available", "I have event counts", "Enter how often the defined event occurred.")}</div>${setup.data_mode === "available" ? `<div class="hl-form-row">${field("Total eligible observations", "trials", current.trials, { type: "number", min: "0", step: "1", disabled: locked })}${field("Observations with the event", "events", current.events, { type: "number", min: "0", step: "1", disabled: locked })}</div><label class="hl-check-label"><input type="checkbox" data-synthetic ${current.synthetic ? "checked" : ""} ${locked ? "disabled" : ""}> These are synthetic / teaching observations</label>` : ""}</div><div class="hl-setup-step"><h3><span>3</span> What do you already know?</h3><div class="hl-setup-choices hl-prior-choices">${choice("prior_mode", "little", "Little previous knowledge", "Use a documented uniform starting assumption.")}${choice("prior_mode", "previous", "An independent previous study", "Use comparable historical counts with a source.")}${choice("prior_mode", "custom", "Specify my own assumptions", "Advanced: enter your own Beta parameters.")}</div>${setup.prior_mode === "little" ? note("<strong>Uniform starting assumption · Beta(1,1).</strong> Every event probability from 0 to 1 has equal density before these observations. This is still an assumption; compare alternatives in prior sensitivity.") : setup.prior_mode === "previous" ? `<div class="hl-form-row">${field("Previous study: total observations", "setup.previous_trials", setup.previous_trials, { type: "number", min: "0", step: "1", disabled: locked })}${field("Previous study: events", "setup.previous_successes", setup.previous_successes, { type: "number", min: "0", step: "1", disabled: locked })}</div>${field("Previous-study source or DOI", "setup.prior_reference", setup.prior_reference, { disabled: locked, hint: "Keep these historical observations separate from your current dataset." })}<label class="hl-check-label"><input type="checkbox" data-previous-independent ${setup.previous_independent ? "checked" : ""} ${locked ? "disabled" : ""}> I checked that these are independent, comparable observations, not the current data</label><p class="hl-note">The app updates Beta(1,1) with the historical counts, then applies the current observations separately. Check overlap and comparability before using this option.</p>` : `<details class="hl-method-details" data-detail="advanced-prior" open><summary>Advanced prior parameters</summary><div class="hl-form-row">${field("Alpha · α", "prior.alpha", current.prior.alpha, { type: "number", min: ".01", step: "any", disabled: locked })}${field("Beta · β", "prior.beta", current.prior.beta, { type: "number", min: ".01", step: "any", disabled: locked })}</div>${field("Why did you choose this prior?", "setup.prior_rationale", setup.prior_rationale, { rows: 2, disabled: locked, hint: "Record the source or reasoning so others can retrace your assumptions." })}</details>`}</div></section>`;
  }
  function sourceInspector() {
    const p = current.publications[selectedSource] || current.publications[0];
    return `<div class="hl-inspector-heading"><h3>${icon("book", 14)} Source inspector</h3>${tool("inspector", "Toggle inspector", "panelRight")}</div>${p ? `<span class="hl-badge">SOURCE ${String(selectedSource + 1).padStart(2, "0")}</span><h4 class="hl-inspector-title">${h(p.title)}</h4><div class="hl-inspector-facts"><span>Publication year</span><strong>${h(p.year || "Unknown")}</strong><span>Provider</span><strong>${h(p.provider)}</strong><span>Abstract</span><strong>${p.abstract ? "Available" : "Unavailable"}</strong></div><div class="hl-divider"></div><div class="hl-section-label">Authors</div><p class="hl-note">${h(p.authors.join(", ") || "Unavailable")}</p><div class="hl-section-label">Persistent identifier</div><p class="hl-mono hl-break">${h(p.doi || p.id)}</p>${safeHref(p.url) ? `<a class="hl-button" href="${safeHref(p.url)}" target="_blank" rel="noopener noreferrer">${icon("external")} Open original</a>` : ""}<div class="hl-divider"></div><p class="hl-note">${p.abstract ? "Abstract-backed excerpts are available for review. The full text has not been analyzed." : "No abstract was supplied. No findings are inferred from the title or metadata."}</p>${button("page:evidence", "Review evidence", "gitBranch")}` : '<p class="hl-note">Attach a source to inspect its provenance here.</p>'}<div class="hl-divider"></div><div class="hl-section-label">Retrieval connection</div><p class="hl-note">${server.openalex_configured ? '<span class="hl-connected">●</span> OpenAlex key loaded from environment' : "OpenAlex public access · no key configured"}</p><p class="hl-note">Only public source metadata is requested. Your API key stays on the server.</p>`;
  }
  function explorer() {
    return `<div class="hl-section-label" style="margin-top:0">Explorer ${tool("dialog:new", "New investigation", "plus")}</div><button class="hl-project-select" data-action="dialog:projects">${icon("folder")}<span>${h(current.title)}</span>${icon("chevronDown", 13)}</button><div class="hl-project-meta">${current.is_demo ? "Read, explore, then make it yours" : "Local research investigation"}</div><div class="hl-section-label">Investigation files</div>${["question", "sources", "evidence", "analysis", "notes", "graph", "report"].map((route) => `<button class="hl-tree-item${page === route ? " hl-active" : ""}" data-action="page:${route}" ${page === route ? 'aria-current="page"' : ""}>${icon(documents[route].icon, 15)}<span>${documents[route].file}</span>${route === "sources" ? `<span class="hl-badge">${current.publications.length}</span>` : route === "evidence" ? `<span class="hl-badge">${current.evidence.length}</span>` : ""}</button>`).join("")}<div class="hl-section-label">Resources</div><div class="hl-help-tree-header"><button class="hl-icon-button" data-action="help-toggle" aria-label="Toggle help documents" aria-expanded="${helpExpanded}">${icon(helpExpanded ? "chevronDown" : "chevronRight", 13)}</button><button class="hl-tree-item${page === "help" ? " hl-active" : ""}" data-action="help:overview">${icon("help", 15)} Help & docs</button></div>${
      helpExpanded
        ? `<div class="hl-help-tree">${[
            ["walkthrough", "Video walkthrough"],
            ["setup", "Starting assumptions"],
            ["methodology", "Model methodology"],
          ]
            .map(
              ([key, title]) =>
                `<button class="hl-tree-item${page === "help" && helpTopic === key ? " hl-active" : ""}" data-action="help:${key}">${icon("file", 13)} ${h(title)}</button>`,
            )
            .join("")}</div>`
        : ""
    }<div class="hl-divider"></div><button class="hl-tree-item" data-action="dialog:new">${icon("plus", 15)} New investigation</button><button class="hl-tree-item hl-getting-started-link" data-action="help:walkthrough">${icon("play", 15)} Watch getting started</button><button class="hl-tree-item" data-action="demo">${icon("flask", 15)} Open guided demo</button><button class="hl-tree-item" data-action="dialog:projects">${icon("folder", 15)} Saved investigations <span class="hl-badge">${server.investigations.length}</span></button><div class="hl-explorer-bottom"><div class="hl-source-meta">${icon("terminal", 13)} Local Python workspace</div><small>Mac Labs AI · v0.2</small></div>`;
  }
  function modal() {
    if (!dialog) return "";
    let content = "";
    if (dialog === "new")
      content = `<h2>New investigation</h2><p>Start with a clean question, source library, and model. The guided demo will remain available.</p><button class="hl-link hl-new-help-link" data-action="help:walkthrough">${icon("play", 14)} First time here? Watch the 2-minute walkthrough</button><form data-form="new"><div class="hl-field"><label for="hl-new-title">Investigation name</label><input id="hl-new-title" name="title" maxlength="160" required placeholder="e.g. Urban heat and tree cover" autofocus></div><div class="hl-toolbar">${button("submit", "Create investigation", "plus", true, busy ? "disabled" : 'type="submit"')}${button("close-dialog", "Cancel", "close")}</div></form>`;
    if (dialog === "link")
      content = `<h2>Add a research source</h2><p>Paste a DOI, OpenAlex URL, or HTTPS research link. DOI and OpenAlex links resolve publication metadata. Other links are kept as unverified references.</p><form data-form="link"><div class="hl-field"><label for="hl-source-link">DOI or research URL</label><input id="hl-source-link" name="link" maxlength="2000" required placeholder="https://doi.org/10.…" autofocus></div><div class="hl-toolbar">${button("submit", "Add source", "link", true, busy ? "disabled" : 'type="submit"')}${button("close-dialog", "Cancel", "close")}</div></form>`;
    if (dialog === "save")
      content = `<h2>Make this investigation yours</h2><p>Save a working copy with your changes. The original guided demo stays available.</p><form data-form="save"><div class="hl-field"><label for="hl-save-title">Investigation name</label><input id="hl-save-title" name="title" value="Extreme heat · my investigation" maxlength="160" required autofocus></div><div class="hl-toolbar">${button("submit", "Save working copy", "save", true, busy ? "disabled" : 'type="submit"')}${button("close-dialog", "Cancel", "close")}</div></form>`;
    if (dialog === "projects")
      content = `<h2>Open investigation</h2><button class="hl-command-item" data-action="demo">${icon("flask")} Extreme heat · guided demo <small>Starter</small></button><div class="hl-divider"></div>${
        server.investigations
          .filter((t) => t !== "current")
          .map(
            (title, i) =>
              `<button class="hl-command-item" data-action="load:${i}">${icon("folder")} ${h(title)}</button>`,
          )
          .join("") || "<p>No saved investigations yet.</p>"
      }<div class="hl-divider"></div>${button("dialog:new", "New investigation", "plus")}`;
    if (dialog === "command") {
      const actions = [
        ...Object.entries(documents).map(([key, doc]) => ({
          action: `page:${key}`,
          label: doc.title,
          icon: doc.icon,
          shortcut: doc.file,
        })),
        ...[
          ["walkthrough", "Video walkthrough"],
          ["setup", "Starting assumptions"],
          ["methodology", "Model methodology"],
        ].map(([key, title]) => ({
          action: `help:${key}`,
          label: `Help: ${title}`,
          icon: "help",
          shortcut: "Documentation",
        })),
        {
          action: "dialog:new",
          label: "New investigation",
          icon: "plus",
          shortcut: "New",
        },
        {
          action: "save",
          label: "Save investigation",
          icon: "save",
          shortcut: "⌘ S",
        },
        {
          action: "theme",
          label: "Toggle light / dark appearance",
          icon: "sun",
          shortcut: "",
        },
        {
          action: "demo",
          label: "Open guided demo",
          icon: "flask",
          shortcut: "",
        },
      ].filter((a) =>
        `${a.label} ${a.shortcut}`.toLowerCase().includes(filter.toLowerCase()),
      );
      content = `<div class="hl-command-search">${icon("search")}<input id="hl-command-search" data-local="filter" value="${h(filter)}" placeholder="Jump to a file or run an action…" aria-label="Command palette search" autofocus></div><div class="hl-command-list">${actions.map((a) => `<button class="hl-command-item" data-action="${a.action}">${icon(a.icon)}${h(a.label)}<small>${h(a.shortcut)}</small></button>`).join("")}</div>`;
    }
    if (dialog === "switch")
      content = `<h2>Save your changes first?</h2><p>Your investigation has unsaved changes. Save them before opening another investigation, or choose to discard this draft.</p><div class="hl-toolbar">${button("save", "Save changes", "save", true)}${button("discard", "Discard draft", "close")}${button("close-dialog", "Cancel", "arrowLeft")}</div>`;
    return `<div class="hl-dialog-backdrop" data-backdrop><section class="hl-dialog${dialog === "command" ? " hl-command" : ""}" role="dialog" aria-modal="true" aria-label="${dialog === "command" ? "Command palette" : "Investigation action"}">${tool("close-dialog", "Close dialog", "close")}${content}${localError || server.error ? `<p class="hl-error-text" role="alert">${h(localError || server.error)}</p>` : ""}</section></div>`;
  }
  let switchAction = null;
  function requestSwitch(action) {
    if (dirty) {
      switchAction = action;
      dialog = "switch";
      draw();
      return;
    }
    action();
  }
  function perform(action) {
    if (action === "ollama-models") {
      send("ollama_models");
      return;
    }
    if (action === "interpret") {
      send("interpret", { model: selectedModel });
      return;
    }
    if (action === "help-toggle") {
      helpExpanded = !helpExpanded;
      draw();
      return;
    }
    if (action.startsWith("help:")) {
      const topic = action.slice(5);
      if (!["overview", "walkthrough", "setup", "methodology"].includes(topic))
        return;
      navigate("help");
      helpTopic = topic;
      helpExpanded = true;
      draw(false);
      return;
    }
    if (action.startsWith("page:")) return navigate(action.slice(5));
    if (action.startsWith("dialog:")) {
      returnFocus = document.activeElement;
      dialog = action.slice(7);
      filter = "";
      draw(false);
      return;
    }
    if (action === "close-dialog") {
      dialog = "";
      switchAction = null;
      localError = "";
      draw();
      queueMicrotask(() =>
        el
          .querySelector(
            `[data-action="${returnFocus?.dataset?.action || "command"}"]`,
          )
          ?.focus(),
      );
      return;
    }
    if (action === "command") {
      returnFocus = document.activeElement;
      dialog = "command";
      filter = "";
      draw(false);
      return;
    }
    if (action === "theme") {
      theme = theme === "dark" ? "light" : "dark";
      try {
        localStorage.setItem("hypothesis-lab-theme", theme);
      } catch {}
      draw();
      return;
    }
    if (action === "show-inspector") {
      hideInspector = false;
      showInspector = true;
      draw();
      return;
    }
    if (action === "inspector") {
      if (window.matchMedia("(min-width:1120px)").matches)
        hideInspector = !hideInspector;
      else showInspector = !showInspector;
      draw();
      return;
    }
    if (action === "explorer") {
      if (window.matchMedia("(min-width:800px)").matches)
        hideExplorer = !hideExplorer;
      else showExplorer = !showExplorer;
      draw();
      return;
    }
    if (busy && ["save", "demo", "tutorial", "discard"].includes(action))
      return;
    if (busy && /^(attach:|load:|export:)/.test(action)) return;
    if (action === "save") {
      if (current.is_demo) {
        dialog = "save";
        draw(false);
      } else send("save");
      return;
    }
    if (action.startsWith("chapter:")) {
      const video = el.querySelector("#hl-walkthrough-video");
      if (video) {
        video.currentTime = Number(action.slice(8));
        video.play().catch(() => {});
      }
      return;
    }
    if (action === "tutorial") {
      requestSwitch(() => {
        dialog = "";
        page = "question";
        send("tutorial");
      });
      return;
    }
    if (action === "demo") {
      requestSwitch(() => {
        dialog = "";
        page = "question";
        send("demo");
      });
      return;
    }
    if (action === "discard") {
      dirty = false;
      dialog = "";
      const next = switchAction;
      switchAction = null;
      next?.();
      return;
    }
    if (action.startsWith("load:")) {
      const title = server.investigations.filter((t) => t !== "current")[
        Number(action.slice(5))
      ];
      requestSwitch(() => {
        dialog = "";
        page = "question";
        send("load", { title });
      });
      return;
    }
    if (action === "clear-search") {
      server.search_results = [];
      draw();
      return;
    }
    if (action.startsWith("attach:")) {
      const paper = server.search_results[Number(action.slice(7))];
      if (paper) {
        current.publications.push(structuredClone(paper));
        dirty = true;
        send("update");
      }
      return;
    }
    if (action.startsWith("inspect:")) {
      selectedSource = Number(action.slice(8));
      hideInspector = false;
      showInspector = true;
      draw();
      return;
    }
    if (action === "note-preview") {
      notePreview = !notePreview;
      draw();
      return;
    }
    if (action.startsWith("export:")) {
      downloadFormat = action.slice(7);
      send("export");
      return;
    }
  }
  function draw(preserve = true) {
    if (!server || !current) return;
    for (const detail of el.querySelectorAll("details[data-detail]")) {
      if (detail.open) expandedDetails.add(detail.dataset.detail);
      else expandedDetails.delete(detail.dataset.detail);
    }
    const oldVideo = el.querySelector("#hl-walkthrough-video");
    const videoState = oldVideo
      ? { time: oldVideo.currentTime, playing: !oldVideo.paused }
      : null;
    const focused = el.contains(document.activeElement)
      ? document.activeElement
      : null;
    const focusId = focused?.id;
    const selection = focused?.selectionStart;
    const selectionEnd = focused?.selectionEnd;
    const scroll = preserve
      ? el.querySelector(".hl-document")?.scrollTop || 0
      : 0;
    el.innerHTML = `<div class="hl-app${model.get("fullscreen") ? " hl-fullscreen" : ""}${showInspector ? " show-inspector" : ""}${showExplorer ? " show-explorer" : ""}${hideInspector || page === "help" ? " hide-inspector" : ""}${hideExplorer ? " hide-explorer" : ""}" data-theme="${h(theme)}"><header class="hl-titlebar"><div class="hl-brand">${icon("flask", 19)} Hypothesis Lab <small>Scientific research workspace</small></div><div class="hl-toolbar"><button class="hl-command-trigger" data-action="command">${icon("search", 13)}<span>Search files & actions</span><kbd>⌘ K</kbd></button>${tool("theme", theme === "dark" ? "Switch to light theme" : "Switch to dark theme", theme === "dark" ? "sun" : "moon")}${page === "help" ? "" : tool("inspector", "Toggle inspector", "panelRight")}${button("save", current.is_demo ? "Save a copy" : "Save", "save", false, busy ? "disabled" : "")}</div></header><div class="hl-body"><nav class="hl-rail" aria-label="Workspace tools">${tool("explorer", "Toggle file explorer", "files", showExplorer)}${tool("page:sources", "Find literature", "search", page === "sources")}${tool("page:graph", "Source graph", "graph", page === "graph")}${tool("command", "Command palette", "command")}${tool("help:overview", "Help & documentation", "help", page === "help")}</nav><aside class="hl-explorer" aria-label="Investigation explorer">${explorer()}</aside><main class="hl-workbench"><nav class="hl-tabs" aria-label="Open documents" role="tablist">${openTabs.map((route) => `<button class="hl-tab${page === route ? " hl-active" : ""}" data-action="page:${route}" role="tab" aria-selected="${page === route}">${icon(documents[route].icon, 13)}${h(documents[route].file)}${dirty && route === "question" ? '<span class="hl-unsaved-dot" aria-label="Unsaved changes">●</span>' : ""}</button>`).join("")}</nav><div class="hl-crumb"><span>${h(page === "help" ? "Help & docs" : current.is_demo ? "demo" : "investigations")} ${icon("chevronRight", 11)} ${h(page === "help" ? { overview: "Overview", walkthrough: "getting-started.md", setup: "starting-assumptions.md", methodology: "methodology.md" }[helpTopic] : documents[page].file)}</span><span>${busy ? '<span class="hl-spinner"></span> Working…' : dirty ? "Unsaved changes" : current.is_demo ? "Bundled starter" : "Local workspace"}</span></div><div class="hl-document">${!dialog && (localError || server.error) ? `<div class="hl-banner hl-error" role="alert">${icon("info")} ${h(localError || server.error)}</div>` : ""}${documentContent()}</div></main><aside class="hl-inspector" aria-label="Context inspector">${["sources", "evidence", "graph"].includes(page) ? sourceInspector() : modelInspector()}</aside></div><footer class="hl-status"><span><span class="hl-connected">●</span> Python runtime <span class="hl-status-separator">│</span>${icon("gitBranch", 12)} ${current.is_demo ? "demo" : "local"} <span data-dirty-status>${busy ? "Working…" : dirty ? "Unsaved changes" : "Ready"}</span></span><span>${current.publications.length} sources · ${current.evidence.length} excerpts <span class="hl-status-separator">│</span> ${server.openalex_configured ? "OpenAlex configured" : "Offline demo ready"} <span class="hl-status-separator">│</span> UTF-8 · Markdown</span></footer>${toast ? `<div class="hl-toast" role="status">${h(toast)}</div>` : ""}${modal()}</div>`;
    for (const detail of el.querySelectorAll("details[data-detail]")) {
      detail.open = expandedDetails.has(detail.dataset.detail);
    }
    const newVideo = el.querySelector("#hl-walkthrough-video");
    if (newVideo && videoState) {
      const restore = () => {
        newVideo.currentTime = videoState.time;
        if (videoState.playing) newVideo.play().catch(() => {});
      };
      if (newVideo.readyState) restore();
      else newVideo.addEventListener("loadedmetadata", restore, { once: true });
    }
    const doc = el.querySelector(".hl-document");
    if (doc) doc.scrollTop = scroll;
    if (focusId) {
      const target = el.querySelector(`[id="${CSS.escape(focusId)}"]`);
      if (target && !target.disabled) {
        target.focus({ preventScroll: true });
        if (
          typeof selection === "number" &&
          ["textarea", "input"].includes(target.tagName.toLowerCase())
        ) {
          try {
            target.setSelectionRange(selection, selectionEnd);
          } catch {}
        }
      }
    }
    if (!preserve && dialog)
      queueMicrotask(() => el.querySelector("[autofocus]")?.focus());
  }
  function receive() {
    server = model.get("data");
    const previous = pending;
    const hasNewEdits = revision > sentRevision && previous === "update";
    if (!hasNewEdits && !server.error)
      current = structuredClone(server.workspace);
    else
      current.evidence = server.workspace.evidence.map((record) => ({
        ...record,
        ...current.evidence.find(
          (e) => e.publication_id === record.publication_id,
        ),
      }));
    busy = false;
    pending = "";
    localError = "";
    if (server.error) {
      if (["update", "save", "export"].includes(previous)) invalidModel = true;
      draw();
      if (hasNewEdits) {
        clearTimeout(updateTimer);
        updateTimer = setTimeout(() => send("update"), 80);
      }
      return;
    }
    invalidModel = false;
    if (["new", "load", "demo", "tutorial", "save"].includes(previous))
      dirty = false;
    if (["new", "load", "demo", "tutorial", "save", "link"].includes(previous))
      dialog = "";
    if (["update", "link", "tutorial", "interpret"].includes(previous))
      dirty = true;
    if (server.download && server.download.id !== lastDownload) {
      lastDownload = server.download.id;
      const data = server.download[downloadFormat];
      const blob = new Blob([data], {
        type: downloadFormat === "json" ? "application/json" : "text/markdown",
      });
      const url = URL.createObjectURL(blob),
        link = document.createElement("a");
      link.href = url;
      link.download = `${current.title.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.${downloadFormat === "json" ? "json" : "md"}`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    }
    draw();
    if (hasNewEdits) {
      clearTimeout(updateTimer);
      updateTimer = setTimeout(() => send("update"), 80);
    }
    if (server.message && previous !== "update") notify(server.message);
    if (previous === "save" && switchAction) {
      const next = switchAction;
      switchAction = null;
      next();
    }
  }
  model.on("change:data", receive);
  el.addEventListener(
    "timeupdate",
    (event) => {
      if (event.target.id !== "hl-walkthrough-video") return;
      const chapter = guide.chapters.find(
        (c) =>
          event.target.currentTime >= c.start &&
          event.target.currentTime < c.end,
      );
      el.querySelectorAll("[data-action^='chapter:']").forEach((button) => {
        const active =
          Number(button.dataset.action.slice(8)) === chapter?.start;
        button.classList.toggle("hl-active", active);
        if (active) button.setAttribute("aria-current", "step");
        else button.removeAttribute("aria-current");
      });
    },
    { signal, capture: true },
  );
  el.addEventListener(
    "click",
    (event) => {
      const action = event.target.closest("[data-action]");
      if (action) {
        if (action.dataset.action === "submit") return;
        event.preventDefault();
        perform(action.dataset.action);
        return;
      }
      const source = event.target.closest("[data-source]");
      if (
        source &&
        !source.dataset.source.startsWith("search:") &&
        !event.target.closest("a,summary,details")
      ) {
        selectedSource = Number(source.dataset.source);
        draw();
      }
      if (event.target.matches("[data-backdrop]")) {
        dialog = "";
        draw();
      }
    },
    { signal },
  );
  el.addEventListener(
    "input",
    (event) => {
      const target = event.target;
      if (target.dataset.local) {
        if (target.dataset.local === "filter") filter = target.value;
        else sourceFilter = target.value;
        draw();
        return;
      }
      if (!target.dataset.field) return;
      let value = target.value;
      if (target.type === "number") {
        if (value === "" || !Number.isFinite(Number(value))) return;
        value = Number(value);
      }
      edit(target.dataset.field, value);
    },
    { signal },
  );
  el.addEventListener(
    "change",
    (event) => {
      const target = event.target;
      if (target.hasAttribute("data-ollama-model")) {
        selectedModel = target.value;
        return;
      }
      if (target.dataset.setup) {
        current.setup[target.dataset.setup] = target.value;
        if (target.dataset.setup === "prior_mode" && target.value === "little")
          current.prior = { alpha: 1, beta: 1 };
        dirty = true;
        revision += 1;
        if (!busy) send("update");
        return;
      }
      if (target.hasAttribute("data-previous-independent")) {
        current.setup.previous_independent = target.checked;
        dirty = true;
        revision += 1;
        if (!busy) send("update");
        return;
      }
      if (target.dataset.annotation !== undefined) {
        current.evidence[Number(target.dataset.annotation)].relationship =
          target.value;
        dirty = true;
        revision += 1;
        if (!busy) send("update");
      }
      if (target.dataset.reviewed !== undefined) {
        current.evidence[Number(target.dataset.reviewed)].requires_review =
          !target.checked;
        dirty = true;
        revision += 1;
        if (!busy) send("update");
      }
      if (target.hasAttribute("data-synthetic")) {
        current.synthetic = target.checked;
        current.observation_batches = [];
        dirty = true;
        revision += 1;
        if (!busy) send("update");
      }
    },
    { signal },
  );
  el.addEventListener(
    "submit",
    (event) => {
      const form = event.target.closest("[data-form]");
      if (!form) return;
      event.preventDefault();
      const values = new FormData(form);
      if (form.dataset.form === "search") {
        current.search_query = String(values.get("query") || "");
        send("search", { query: current.search_query });
      }
      if (form.dataset.form === "link")
        send("link", { link: String(values.get("link") || "") });
      if (form.dataset.form === "new") {
        const title = String(values.get("title") || "");
        requestSwitch(() => {
          page = "question";
          send("new", { title });
        });
      }
      if (form.dataset.form === "save")
        send("save", { title: String(values.get("title") || "") });
    },
    { signal },
  );
  document.addEventListener(
    "keydown",
    (event) => {
      if (!el.isConnected) return;
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        dialog = dialog === "command" ? "" : "command";
        filter = "";
        draw(false);
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        perform("save");
      }
      if (event.key === "Escape") {
        dialog = "";
        showInspector = false;
        showExplorer = false;
        draw();
      }
      if (dialog && event.key === "Tab") {
        const focusable = [
          ...el.querySelectorAll(
            ".hl-dialog button:not(:disabled), .hl-dialog input:not(:disabled), .hl-dialog select, .hl-dialog textarea, .hl-dialog a[href]",
          ),
        ];
        if (!focusable.length) return;
        const first = focusable[0],
          last = focusable.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
      if (
        dialog === "command" &&
        event.key === "Enter" &&
        document.activeElement?.id === "hl-command-search"
      ) {
        const first = el.querySelector(".hl-command-list [data-action]");
        if (first) {
          event.preventDefault();
          perform(first.dataset.action);
        }
      }
    },
    { signal },
  );
  window.addEventListener(
    "beforeunload",
    (event) => {
      if (dirty) {
        event.preventDefault();
        event.returnValue = "";
      }
    },
    { signal },
  );
  draw(false);
  return () => {
    abort.abort();
    clearTimeout(updateTimer);
    clearTimeout(toastTimer);
    model.off("change:data", receive);
  };
}
export default { render };
