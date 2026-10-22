/** Dependency-free SVG views. All research labels are escaped at this boundary. */
const escape = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const finite = (value) => (Number.isFinite(Number(value)) ? Number(value) : 0);
const bounded = (value) => Math.max(0, Math.min(1, finite(value)));
const percent = (value) => `${(bounded(value) * 100).toFixed(1)}%`;
const palette = {
  posterior: "#b7a0ff",
  prior: "#817794",
  likelihood: "#56c4b4",
  grid: "currentColor",
};
const line = (xs, ys, x, y) =>
  xs
    .map((v, i) => `${i ? "L" : "M"}${x(v).toFixed(2)},${y(ys[i]).toFixed(2)}`)
    .join(" ");
const text = (x, y, value, anchor = "middle") =>
  `<text class="hl-chart-axis" x="${x}" y="${y}" text-anchor="${anchor}" fill="currentColor" font-size="11" font-family="ui-monospace,monospace">${escape(value)}</text>`;
const legend = () =>
  `<div class="hl-chart-legend" aria-label="Chart legend" style="display:flex;gap:18px;flex-wrap:wrap;font-size:11px;opacity:.8;padding:0 12px 10px"><span><span aria-hidden="true" style="color:${palette.prior}">┄</span> Prior</span><span><span aria-hidden="true" style="color:${palette.likelihood}">┈</span> Likelihood · normalized</span><span><span aria-hidden="true" style="color:${palette.posterior}">━</span> Posterior</span></div>`;

export function densityChart(analysis, { compact = false } = {}) {
  const curves = analysis?.curves;
  if (!curves?.x?.length)
    return '<div class="hl-chart" role="status">Set model parameters to inspect the distribution.</div>';
  const W = 760,
    H = compact ? 210 : 260;
  const left = 48,
    right = 18,
    top = 16,
    bottom = H - 42;
  const xs = curves.x.map(bounded);
  const series = ["prior", "likelihood", "posterior"];
  const values = series.flatMap((key) => (curves[key] ?? []).map(finite));
  const maximum = Math.max(1, ...values.filter((v) => v >= 0)) * 1.09;
  const x = (p) => left + bounded(p) * (W - left - right);
  const y = (p) => bottom - (Math.max(0, finite(p)) / maximum) * (bottom - top);
  const lo = bounded(analysis.interval?.[0]),
    hi = bounded(analysis.interval?.[1]);
  const grid = Array.from({ length: 5 }, (_, i) => {
    const value = (maximum * i) / 4,
      py = y(value);
    return `<line x1="${left}" x2="${W - right}" y1="${py}" y2="${py}" stroke="currentColor" opacity=".08"/>${text(left - 10, py + 4, value < 10 ? value.toFixed(1) : Math.round(value), "end")}`;
  }).join("");
  const ticks = Array.from({ length: 6 }, (_, i) =>
    text(x(i / 5), H - 22, `${i * 20}%`),
  ).join("");
  const posterior = line(xs, curves.posterior ?? [], x, y);
  const fill = `${posterior} L${x(xs.at(-1))},${bottom} L${x(xs[0])},${bottom} Z`;
  const paths = series
    .map(
      (key) =>
        `<path d="${line(xs, curves[key] ?? [], x, y)}" fill="none" stroke="${palette[key]}" stroke-width="${key === "posterior" ? 2.5 : 1.6}" ${key === "prior" ? 'stroke-dasharray="5 5"' : key === "likelihood" ? 'stroke-dasharray="2 4"' : ""} vector-effect="non-scaling-stroke"/>`,
    )
    .join("");
  return `<div class="hl-chart">${legend()}<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Prior, normalized likelihood, and posterior event probability distributions"><title>Posterior mean ${percent(analysis.mean)}. 95% credible interval ${percent(lo)} to ${percent(hi)}.</title><defs><clipPath id="hl-density-clip-${compact ? "small" : "full"}"><rect x="${left}" y="${top}" width="${W - left - right}" height="${bottom - top}"/></clipPath></defs>${grid}<g clip-path="url(#hl-density-clip-${compact ? "small" : "full"})"><rect x="${x(lo)}" y="${top}" width="${Math.max(0, x(hi) - x(lo))}" height="${bottom - top}" fill="${palette.posterior}" opacity=".065"><title>95% credible interval</title></rect><path d="${fill}" fill="${palette.posterior}" opacity=".08"/>${paths}<line x1="${x(analysis.mean)}" x2="${x(analysis.mean)}" y1="${top}" y2="${bottom}" stroke="${palette.posterior}" opacity=".4" stroke-dasharray="3 5"><title>Posterior mean ${percent(analysis.mean)}</title></line></g>${ticks}${text((left + W - right) / 2, H - 3, "Event probability · p")}</svg></div>`;
}

export function sequenceChart(analysis) {
  const points = analysis?.sequence ?? [];
  if (!points.length)
    return '<div class="hl-chart" role="status">Add observation batches to see sequential updates.</div>';
  const W = 760,
    H = 250,
    left = 48,
    right = 24,
    top = 20,
    bottom = 205;
  const x = (i) =>
    points.length === 1
      ? (left + W - right) / 2
      : left + (i * (W - left - right)) / (points.length - 1);
  const y = (p) => bottom - bounded(p) * (bottom - top);
  const upper = points
    .map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.upper)}`)
    .join(" ");
  const lower = [...points]
    .reverse()
    .map((p, i) => `L${x(points.length - 1 - i)},${y(p.lower)}`)
    .join(" ");
  const means = points
    .map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p.mean)}`)
    .join(" ");
  const grid = [0, 0.25, 0.5, 0.75, 1]
    .map(
      (v) =>
        `<line x1="${left}" x2="${W - right}" y1="${y(v)}" y2="${y(v)}" stroke="currentColor" opacity=".08"/>${text(left - 10, y(v) + 4, `${v * 100}%`, "end")}`,
    )
    .join("");
  const dots = points
    .map(
      (p, i) =>
        `<g data-chart-point="${i}"><title>${escape(p.label ?? `Batch ${i + 1}`)}: mean ${percent(p.mean)}, interval ${percent(p.lower)}–${percent(p.upper)}; ${finite(p.n)} observations</title><line x1="${x(i)}" x2="${x(i)}" y1="${y(p.upper)}" y2="${y(p.lower)}" stroke="${palette.posterior}" opacity=".35"/><circle cx="${x(i)}" cy="${y(p.mean)}" r="4" fill="${palette.posterior}"/>${text(x(i), bottom + 23, p.batch ?? i + 1)}</g>`,
    )
    .join("");
  return `<div class="hl-chart"><svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Sequential posterior means and 95 percent credible intervals"><title>Posterior updates across observation batches. Shading shows the 95% credible interval.</title>${grid}<path d="${upper} ${lower} Z" fill="${palette.posterior}" opacity=".1"/><path d="${means}" fill="none" stroke="${palette.posterior}" stroke-width="2.4"/>${dots}${text((left + W - right) / 2, H - 3, "Observation batch")}</svg></div>`;
}

export function evidenceGraph(workspace) {
  const sources = (workspace?.publications ?? workspace?.sources ?? []).slice(
    0,
    8,
  );
  const annotations = workspace?.annotations ?? workspace?.evidence ?? [];
  const W = 760,
    H = 330,
    cx = 380,
    cy = 158;
  const nodes = sources.map((source, i) => {
    const angle =
      -Math.PI / 2 + (i * 2 * Math.PI) / Math.max(3, sources.length);
    const x = cx + Math.cos(angle) * 227,
      y = cy + Math.sin(angle) * 105;
    const title = String(source.title ?? "Untitled source");
    const label = title.length > 34 ? `${title.slice(0, 31)}…` : title;
    const annotation = Array.isArray(annotations)
      ? annotations.find(
          (a) => a.publication_id === source.id || a.source_id === source.id,
        )
      : annotations[source.id];
    const relationship =
      typeof annotation === "string" ? annotation : annotation?.relationship;
    const status = ["supporting", "contradicting", "inconclusive"].includes(
      relationship,
    )
      ? relationship
      : "unclassified";
    const candidate = String(source.url ?? source.doi ?? "");
    const safeURL = /^https:\/\//i.test(candidate) ? escape(candidate) : "";
    const node = `<g><title>${escape(title)} · ${escape(status)}. Literature context; does not update numerical inference.</title><circle cx="${x}" cy="${y}" r="17" fill="var(--panel,#24232b)" stroke="${palette.prior}" stroke-width="1.4"/><text x="${x}" y="${y + 4}" text-anchor="middle" fill="${palette.posterior}" font-size="11" font-family="ui-monospace,monospace">${i + 1}</text>${text(x, y + 35, label)}${text(x, y + 51, `${source.year ?? "n.d."} · ${status}`)}</g>`;
    return {
      edge: `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="${palette.prior}" opacity=".35" stroke-dasharray="3 5"/>`,
      node: safeURL
        ? `<a href="${safeURL}" target="_blank" rel="noopener noreferrer">${node}</a>`
        : node,
    };
  });
  return `<div class="hl-graph"><svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Research hypothesis linked to literature sources; edges indicate context, not causal or statistical certainty"><title>Literature map. Source relationships require researcher review.</title>${nodes.map((n) => n.edge).join("")}<circle cx="${cx}" cy="${cy}" r="43" fill="var(--panel,#24232b)" stroke="${palette.posterior}" stroke-width="1.5"/><text x="${cx}" y="${cy - 2}" fill="${palette.posterior}" text-anchor="middle" font-size="20">H</text>${text(cx, cy + 17, "hypothesis")}${nodes.map((n) => n.node).join("")}${!sources.length ? text(cx, H - 27, "Add literature to build your source map.") : ""}</svg></div>`;
}
