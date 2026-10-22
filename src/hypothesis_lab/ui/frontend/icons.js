const paths = {
  play: '<path d="m9 5 11 7-11 7z"/>',
  flask:
    '<path d="M9 3h6M10 3v6l-6 10a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2L14 9V3M8 14h8"/>',
  files: '<path d="M8 3h9l4 4v14H8zM17 3v5h4M4 7H3v14h1"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  graph:
    '<circle cx="5" cy="6" r="2"/><circle cx="18" cy="5" r="2"/><circle cx="12" cy="18" r="2"/><path d="m7 6 9-1M6 8l5 8m6-9-4 9"/>',
  settings:
    '<path d="m9 3-.5 3-2 1-3-.5-1.5 3 2 2v2l-2 2 1.5 3 3-.5 2 1L9 22h5l.5-3 2-1 3 .5 1.5-3-2-2v-2l2-2-1.5-3-3 .5-2-1L14 3z"/><circle cx="11.5" cy="12.5" r="3"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  chevronDown: '<path d="m6 9 6 6 6-6"/>',
  chevronRight: '<path d="m9 6 6 6-6 6"/>',
  file: '<path d="M5 3h9l5 5v13H5zM14 3v6h5"/>',
  book: '<path d="M3 4h6l3 2 3-2h6v16h-6l-3 2-3-2H3zM12 6v16"/>',
  activity: '<path d="M2 12h5l3-8 4 16 3-8h5"/>',
  note: '<path d="M4 3h16v14l-4 4H4zM8 8h8M8 12h8m-1 9v-5h5"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  arrowRight: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  arrowLeft: '<path d="M20 12H4m6-6-6 6 6 6"/>',
  external: '<path d="M14 3h7v7m0-7L10 14M10 4H4v16h16v-6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1"/>',
  moon: '<path d="M21 13A9 9 0 0 1 11 3a9 9 0 1 0 10 10Z"/>',
  save: '<path d="M4 3h14l3 3v15H3V3h1Zm3 0v6h10V3M7 21v-8h10v8"/>',
  panelRight:
    '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M15 4v16"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  terminal: '<path d="m4 5 6 6-6 6m9 0h7"/>',
  command:
    '<path d="M9 7V5a2 2 0 1 0-2 2h10a2 2 0 1 0-2-2v14a2 2 0 1 0 2-2H7a2 2 0 1 0 2 2V7"/>',
  gitBranch:
    '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M6 7v10m12-10v3c0 5-12 1-12 7"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
  filter: '<path d="M3 5h18l-7 8v7l-4-2v-5z"/>',
  copy: '<rect x="8" y="8" width="12" height="13" rx="1"/><path d="M16 8V3H3v13h5"/>',
  refresh:
    '<path d="M20 8a8 8 0 0 0-14-3L3 8m0-5v5h5m-4 8a8 8 0 0 0 14 3l3-3m0 5v-5h-5"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 0 1 6 0c0 2-3 2-3 5m0 3v.1"/>',
  folder: '<path d="M3 5h7l2 2h9v13H3z"/>',
  link: '<path d="m10 14 4-4m-6 6-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m2 10a4 4 0 0 0 6 0l5-5a4 4 0 0 0-6-6l-2 2" transform="translate(1 0) scale(.9)"/>',
  more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
};

export function icon(name, size = 16) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.file}</svg>`;
}
