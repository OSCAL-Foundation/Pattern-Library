#!/usr/bin/env node
/*
 * pagecheck.js: run a page's renderers against the real data and inspect what
 * they produced.
 *
 * Every page on this site is markup plus data. The markup carries hooks like
 * data-matrix and data-slot-fill; assets/site.js fills them from data/ at load
 * time, which is what plan section 8 asks for so that regenerating data never
 * touches markup. The cost of that choice is that a broken hook, a dangling
 * snippet id or a renderer that silently produced nothing is invisible to any
 * check that only reads the HTML.
 *
 * There is no browser and no network in the environment this site is built in,
 * so this supplies a DOM small enough to run site.js and large enough to be
 * honest about it, loads the page, runs boot(), and then asserts on the result.
 * It is a test harness, not a browser, and it is not part of the published site.
 *
 *     node tools/pagecheck.js                 check every page
 *     node tools/pagecheck.js six-questions.html    check one
 */

"use strict";

const fs = require("fs");
const path = require("path");

const TOOLS = __dirname;
const ROOT = path.dirname(TOOLS);

/* ------------------------------------------------------------------ results */

let pass = 0;
const failures = [];

function check(name, ok, detail) {
  if (ok) { pass += 1; return true; }
  failures.push(detail ? `${name}  |  ${detail}` : name);
  return false;
}

/* ------------------------------------------------------- a very small DOM */

const VOID = new Set(["area", "base", "br", "col", "embed", "hr", "img",
  "input", "link", "meta", "param", "source", "track", "wbr"]);

class ClassList {
  constructor(node) { this.node = node; }
  get _list() {
    return (this.node.className || "").split(/\s+/).filter(Boolean);
  }
  _set(l) { this.node.className = l.join(" "); }
  add() {
    const l = this._list;
    for (const c of arguments) if (c && l.indexOf(c) === -1) l.push(c);
    this._set(l);
  }
  remove() {
    const drop = Array.from(arguments);
    this._set(this._list.filter((c) => drop.indexOf(c) === -1));
  }
  contains(c) { return this._list.indexOf(c) !== -1; }
}

class Node {
  constructor(tag) {
    this.tagName = (tag || "").toUpperCase();
    this.nodeName = this.tagName;
    this.childNodes = [];
    this.parentNode = null;
    this.attributes = Object.create(null);
    /* dataset has to write through to the attribute, the way a browser's does.
       Without that, an element built by a renderer is invisible to the
       [data-quote] selectors the same renderers use to find their own work. */
    this._data = Object.create(null);
    const self = this;
    this.dataset = new Proxy(this._data, {
      get: (t, k) => t[k],
      has: (t, k) => k in t,
      set: (t, k, v) => {
        t[k] = String(v);
        self.attributes["data-" + String(k).replace(/[A-Z]/g, (c) => "-" + c.toLowerCase())] = String(v);
        return true;
      },
      deleteProperty: (t, k) => {
        delete t[k];
        delete self.attributes["data-" + String(k).replace(/[A-Z]/g, (c) => "-" + c.toLowerCase())];
        return true;
      }
    });
    this._text = null;          // set only for text nodes
    this._html = null;          // whatever innerHTML was assigned
    this.hidden = false;
    this.classList = new ClassList(this);
  }
  get className() { return this.attributes["class"] || ""; }
  set className(v) { this.attributes["class"] = v; }
  get id() { return this.attributes["id"] || ""; }
  set id(v) { this.attributes["id"] = v; }
  get title() { return this.attributes["title"] || ""; }
  set title(v) { this.attributes["title"] = v; }
  get type() { return this.attributes["type"] || ""; }
  set type(v) { this.attributes["type"] = v; }
  get href() { return this.attributes["href"] || ""; }
  set href(v) { this.attributes["href"] = v; }
  get rel() { return this.attributes["rel"] || ""; }
  set rel(v) { this.attributes["rel"] = v; }
  get value() { return this.attributes["value"] || ""; }
  set value(v) { this.attributes["value"] = v; }
  get placeholder() { return this.attributes["placeholder"] || ""; }
  set placeholder(v) { this.attributes["placeholder"] = v; }
  get style() { return this._style || (this._style = {}); }
  get children() { return this.childNodes.filter((c) => c.tagName); }

  setAttribute(k, v) {
    this.attributes[k] = String(v);
    if (k.indexOf("data-") === 0) {
      this._data[k.slice(5).replace(/-([a-z])/g, (m, c) => c.toUpperCase())] =
        String(v);
    }
  }
  getAttribute(k) {
    return Object.prototype.hasOwnProperty.call(this.attributes, k)
      ? this.attributes[k] : null;
  }
  removeAttribute(k) { delete this.attributes[k]; }
  appendChild(n) { n.parentNode = this; this.childNodes.push(n); return n; }
  /* Needed by the two banners site.js can put at the top of main. Neither runs
     when the page is served, which is why the harness went six phases without
     this method and the file:// path could not be tested at all. */
  insertBefore(n, ref) {
    n.parentNode = this;
    const at = ref ? this.childNodes.indexOf(ref) : -1;
    if (at === -1) this.childNodes.push(n);
    else this.childNodes.splice(at, 0, n);
    return n;
  }
  get firstChild() { return this.childNodes[0] || null; }
  removeChild(n) {
    const at = this.childNodes.indexOf(n);
    if (at !== -1) this.childNodes.splice(at, 1);
    return n;
  }
  addEventListener(type, fn) {
    (this._on || (this._on = {}))[type] = (this._on[type] || []).concat(fn);
  }
  dispatchEvent(e) {
    if (!e.target) e.target = this;
    const l = (this._on || {})[e.type] || [];
    l.forEach((fn) => fn.call(this, e));
    if (this.parentNode) return this.parentNode.dispatchEvent(e);
    if (this._document) this._document.dispatchEvent(e);
    return true;
  }
  click() { this.dispatchEvent({ type: "click", target: this }); }
  focus() {}
  getBoundingClientRect() { return { top: 0, left: 0, bottom: 0, right: 0 }; }
  /* A browser scrolls; the harness does not, but the method has to exist
     or the code path that opens a deep link throws before it finishes. */
  scrollIntoView() {}
  closest(sel) {
    let n = this;
    while (n) { if (matches(n, sel)) return n; n = n.parentNode; }
    return null;
  }
  get textContent() {
    if (this._text !== null) return this._text;
    return this.childNodes.map((c) => c.textContent).join("");
  }
  set textContent(v) {
    this.childNodes = [];
    this._html = null;
    if (v === "" || v === null || v === undefined) return;
    const t = new Node(null);
    t._text = String(v);
    t.parentNode = this;
    this.childNodes.push(t);
  }
  get innerHTML() { return this._html === null ? "" : this._html; }
  /* Assigning innerHTML used to store the string and stop there, which meant
     anything a renderer built by assignment was invisible to every check on
     this page. The SC-28 panes are built that way, and the marks on them went
     unnoticed until a check asked for them. Parse it, and keep the string for
     the getter so checks that read innerHTML back still behave. */
  set innerHTML(v) {
    this._html = String(v);
    this.childNodes = [];
    const frag = parse(this._html);
    frag.childNodes.forEach((c) => { c.parentNode = this; });
    this.childNodes = frag.childNodes;
  }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
  querySelectorAll(sel) {
    const out = [];
    const want = sel.split(",").map((s) => s.trim()).filter(Boolean);
    (function walk(n) {
      n.childNodes.forEach((c) => {
        if (!c.tagName) return;
        if (want.some((s) => matchesDescendant(c, s))) out.push(c);
        walk(c);
      });
    })(this);
    return out;
  }
}

/* Selector support is exactly what site.js uses: tag, .class, #id, [attr],
   [attr="v"], [attr^="v"], compounds of those, and descendant combinators. */
function matches(node, sel) {
  if (!node.tagName) return false;
  /* The tag alternative allows digits, or h3 parses as the tag "h". */
  const parts = sel.match(/(^[a-zA-Z][a-zA-Z0-9]*)|\.[\w-]+|#[\w-]+|\[[^\]]+\]/g) || [];
  return parts.every((p) => {
    if (p[0] === ".") return node.classList.contains(p.slice(1));
    if (p[0] === "#") return node.id === p.slice(1);
    if (p[0] === "[") {
      const m = p.slice(1, -1).match(/^([\w-]+)(?:(\^?=)"([^"]*)")?$/);
      if (!m) return false;
      const v = node.getAttribute(m[1]);
      if (v === null) return false;
      if (!m[2]) return true;
      return m[2] === "^=" ? v.indexOf(m[3]) === 0 : v === m[3];
    }
    return node.tagName === p.toUpperCase();
  });
}

function matchesDescendant(node, sel) {
  const chain = sel.split(/\s+/).filter(Boolean);
  if (chain.length === 1) return matches(node, chain[0]);
  if (!matches(node, chain[chain.length - 1])) return false;
  let n = node.parentNode, i = chain.length - 2;
  while (n && i >= 0) {
    if (matches(n, chain[i])) i -= 1;
    n = n.parentNode;
  }
  return i < 0;
}

/* --------------------------------------------------------------- parsing */

function parse(html) {
  const root = new Node("html-root");
  const stack = [root];
  const re = /<!--[\s\S]*?-->|<\/([a-zA-Z][\w-]*)\s*>|<([a-zA-Z][\w-]*)((?:\s+[^\s"'>/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>`]+))?)*)\s*(\/?)>/g;
  let last = 0, m;
  while ((m = re.exec(html))) {
    const text = html.slice(last, m.index);
    if (text.trim()) {
      const t = new Node(null);
      t._text = text;
      stack[stack.length - 1].appendChild(t);
    }
    last = re.lastIndex;
    if (m[0].indexOf("<!--") === 0) continue;
    if (m[1]) {
      for (let i = stack.length - 1; i > 0; i -= 1) {
        if (stack[i].tagName === m[1].toUpperCase()) { stack.length = i; break; }
      }
      continue;
    }
    const node = new Node(m[2]);
    const attrs = m[3] || "";
    const ar = /([^\s"'>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>`]+)))?/g;
    let a;
    while ((a = ar.exec(attrs))) {
      node.setAttribute(a[1], a[2] !== undefined ? a[2]
        : a[3] !== undefined ? a[3] : a[4] !== undefined ? a[4] : "");
    }
    stack[stack.length - 1].appendChild(node);
    /* script and style hold text, not markup. */
    if (m[2].toLowerCase() === "script" || m[2].toLowerCase() === "style") {
      const close = new RegExp("</" + m[2] + "\\s*>", "i");
      const rest = html.slice(re.lastIndex);
      const end = rest.search(close);
      if (end !== -1) {
        const t = new Node(null);
        t._text = rest.slice(0, end);
        node.appendChild(t);
        re.lastIndex += end + rest.slice(end).match(close)[0].length;
        last = re.lastIndex;
      }
      continue;
    }
    if (!m[4] && !VOID.has(m[2].toLowerCase())) stack.push(node);
  }
  /* The loop only emits text that sits before a tag, so anything after the last
     tag was silently dropped, and a string with no tags at all produced nothing.
     Every check that reads textContent off markup a renderer built by assignment
     was therefore reading a truncated version of it, which made those checks
     weaker than they looked rather than failing outright. */
  const tail = html.slice(last);
  if (tail.trim()) {
    const t = new Node(null);
    t._text = tail;
    stack[stack.length - 1].appendChild(t);
  }
  return root;
}

/* ------------------------------------------------------------ environment */

function makeWindow(pageHtml, pageName) {
  const root = parse(pageHtml);
  const html = root.querySelector("html") || new Node("html");
  const body = root.querySelector("body") || new Node("body");

  const docListeners = {};
  const document = {
    documentElement: html,
    body: body,
    _root: root,
    _listeners: docListeners,
    createElement: (t) => new Node(t),
    createTextNode: (t) => { const n = new Node(null); n._text = String(t); return n; },
    getElementById: (id) => root.querySelectorAll("#" + id)[0] || null,
    querySelector: (s) => root.querySelector(s),
    querySelectorAll: (s) => root.querySelectorAll(s),
    /* Real, because site.js binds the term cards by delegation here. A stub
       would make the regression this exists to catch invisible. */
    addEventListener: (type, fn) => {
      (docListeners[type] = docListeners[type] || []).push(fn);
    },
    dispatchEvent: (e) => {
      (docListeners[e.type] || []).forEach((fn) => fn(e));
      return true;
    },
    activeElement: null,
    importNode: (n) => n,
    readyState: "complete"
  };
  root._document = document;

  const pending = [];
  const win = {
    document: document,
    /* The real location carries pathname and protocol, and site.js reads
       both: pathname to mark the current nav item, protocol to decide whether
       to consult the offline bundle. A stub with only hash made both throw.
       Served is the case under test, so protocol is http. */
    location: {
      hash: "",
      protocol: "http:",
      pathname: "/" + (pageName || "index.html"),
      href: "http://127.0.0.1/" + (pageName || "index.html")
    },
    matchMedia: () => ({ matches: false, addEventListener: () => {} }),
    /* A browser has both of these and site.js uses both: rAF to scroll after a
       disclosure has changed the page height, and replaceState to keep the
       address naming what is open. */
    requestAnimationFrame: (fn) => { pending.push(Promise.resolve().then(fn)); },
    history: { replaceState: () => {}, pushState: () => {} },
    /* The rail's active-section tracking is decoration and the harness does not
       simulate scrolling, so this stays undefined on purpose: site.js checks for
       it and skips the tracking, which is the no-support path a real browser
       without it would take. */
    IntersectionObserver: undefined,
    addEventListener: () => {},
    scrollX: 0, scrollY: 0,
    CustomEvent: function (type, init) {
      return Object.assign({ type: type }, init || {});
    },
    fetch: (url) => {
      const rel = String(url).replace(/^\.\//, "").replace(/^\.\.\//, "");
      const file = path.join(ROOT, rel.replace(/^\//, ""));
      const p = fs.promises.readFile(file, "utf8").then((txt) => ({
        ok: true, status: 200,
        json: () => Promise.resolve(JSON.parse(txt)),
        text: () => Promise.resolve(txt)
      })).catch(() => ({ ok: false, status: 404,
        json: () => Promise.reject(new Error("404")),
        text: () => Promise.reject(new Error("404")) }));
      pending.push(p);
      return p;
    },
    _pending: pending
  };
  win.DOMParser = function () {};
  win.DOMParser.prototype.parseFromString = function (str) {
    const r = parse(str);
    const svg = r.querySelector("svg");
    return { documentElement: svg || new Node("parsererror") };
  };
  win.window = win;
  win.globalThis = win;
  return win;
}

async function settle(win, rounds) {
  for (let i = 0; i < (rounds || 12); i += 1) {
    const n = win._pending.length;
    await Promise.allSettled(win._pending.slice());
    await new Promise((r) => setImmediate(r));
    if (win._pending.length === n) await new Promise((r) => setImmediate(r));
  }
}

function run(scriptPath, win) {
  const src = fs.readFileSync(scriptPath, "utf8");
  /* The script runs with an explicit parameter list rather than against a real
     global object, so anything site.js reads off the global has to be named
     here. Two were missing and the disclosure layer needs both. */
  const fn = new Function(
    "window", "document", "fetch", "localStorage", "matchMedia", "location",
    "CustomEvent", "DOMParser", "globalThis", "navigator", "setTimeout", "console",
    "requestAnimationFrame", "history", "IntersectionObserver",
    src + "\n//# sourceURL=" + scriptPath);
  fn(win, win.document, win.fetch, {
    getItem: () => null, setItem: () => {}
  }, win.matchMedia, win.location, win.CustomEvent, win.DOMParser, win,
    { clipboard: { writeText: () => Promise.resolve() } },
    (f) => f, { error: () => {}, log: () => {}, warn: () => {} },
    win.requestAnimationFrame, win.history, win.IntersectionObserver);
}

/* Load the scripts the page itself declares, in document order.
 *
 * This used to be a hardcoded pair: 74-slot-strip.js and site.js, loaded into
 * every page whether or not the page asked for them. That made the harness
 * dishonest in the one direction that matters. A page that draws state marks
 * and does not declare 74-slot-strip.js finds no TFGSlotStrip in a browser and
 * draws no legend, leaving the marks with nothing saying what they mean, while
 * every legend check on that page passed anyway because the harness had quietly
 * supplied the missing file.
 *
 * A check that supplies what the page is missing is not a check. So the loader
 * reads <script src> off the parsed document and loads exactly that.
 *
 * highlight.js is the one exception, and it is skipped rather than supplied:
 * the caller stubs TFGHighlight so that extract bodies stay byte-comparable
 * with their source files, which is what --snippets needs to mean anything.
 */
function runDeclared(win, opts) {
  opts = opts || {};
  const srcs = win.document.querySelectorAll("script")
    .map((n) => n.getAttribute("src"))
    .filter(Boolean)
    .map((s) => s.replace(/^\.\//, ""))
    .filter((s) => !/highlight\.js$/.test(s))
    .filter((s) => opts.skipBundle ? !/bundle\.js$/.test(s) : true);
  for (const src of srcs) run(path.join(ROOT, src.split("/").join(path.sep)), win);
  return srcs;
}

/* --------------------------------------------------------------- helpers */

const FAIL_TEXT = /could not be loaded|is not in/i;

function textOf(n) { return (n.textContent || "").replace(/\s+/g, " ").trim(); }

/* ----------------------------------------------------------------- checks */

/* The pre-read's option-letter order: A, B, C. */
const OPTION_ORDER = ["Catalog-first", "Component-first", "Assessment-first"];

const RENDERED = {};

async function checkPage(file) {
  const name = path.basename(file);
  const win = makeWindow(fs.readFileSync(file, "utf8"), name);
  win.TFGHighlight = { highlight: (s) => String(s) };
  const doc = win.document;

  runDeclared(win);
  await settle(win);

  /* Nothing may be left showing its own error message. */
  const errs = doc.querySelectorAll(".small.muted")
    .filter((n) => FAIL_TEXT.test(textOf(n)))
    .map((n) => textOf(n).slice(0, 70));
  check(`${name}: no renderer reported a load failure`, errs.length === 0,
        JSON.stringify(errs.slice(0, 3)));

  /* --- the contents list has to say what the headings say -----------------
     Every section title lives in two places, the table of contents and the
     heading itself, and nothing compared them. Renaming a section meant
     remembering to edit both, and renumbering meant remembering to edit both
     for every section below the change. That had already gone wrong once and
     shipped: the index kept a subsection numbered 7.1 under a section 6 after
     two sections above it were removed, and no check noticed, because each half
     was internally consistent.

     The comparison is on the rendered text, so a heading assembled from a
     question chip plus a title still has to match what the contents claims it
     says. The chip is dropped first: it is a marker rather than part of the
     title. */
  const tocLinks = doc.querySelectorAll(".toc a");
  tocLinks.forEach((a) => {
    const id = (a.getAttribute("href") || "").replace(/^#/, "");
    const target = doc.getElementById(id);
    if (!target) {
      check(`${name}: contents entry "${textOf(a)}" points at a section`, false, `#${id}`);
      return;
    }
    const head = /^H[1-6]$/.test(target.tagName)
      ? target
      : target.querySelectorAll("h2")[0] || target.querySelectorAll("h3")[0];
    if (!head) {
      check(`${name}: #${id} has a heading`, false);
      return;
    }
    const headText = head.childNodes
      .filter((n) => !(n.classList && n.classList.contains("slot-chip")))
      .map((n) => n.textContent || "")
      .join(" ").replace(/\s+/g, " ").trim();
    check(`${name}: contents and heading agree for #${id}`,
          headText === textOf(a), `contents "${textOf(a)}" against heading "${headText}"`);
  });

  /* --- the one thing the footer still carries ----------------------------
     The footer was four paragraphs: the no-recommendation statement, the
     provenance and sources, and the licence. Three of those were removed by
     decision. The statement was kept, and it is now the only place on the site
     that says it, so it is asserted per page rather than assumed. It is also a
     standing rule of the build rather than a piece of copy, which is why the
     wording is matched rather than the element. */
  const foot = doc.querySelectorAll(".site-footer");
  check(`${name}: carries the footer once`, foot.length === 1, `${foot.length}`);
  check(`${name}: the footer states that the site makes no recommendation`,
      /No recommendation is made\./.test(textOf(foot[0] || { textContent: "" })));

    const metadata = JSON.parse(fs.readFileSync(path.join(ROOT, "analysis.json"), "utf8"));
    const ongoing = metadata.status === "active" && !metadata.concluded
      && !metadata.recommendation && !metadata.decision && !metadata.decided
      && !metadata.supersededBy;
    const notice = doc.querySelector(".wip-banner");
    check(`${name}: progress banner reflects analysis status`,
      Boolean(notice) && notice.hidden === !ongoing);

    if (/^(assessment|catalog|component)-first\.html$/.test(name)) {
      const mapping = doc.querySelector(".stakeholders");
      const copy = textOf(mapping || { textContent: "" });
      check(`${name}: stakeholder mapping names technology providers`,
        /Technology providers/.test(copy));
      check(`${name}: stakeholder mapping has no software-provider label`,
        !/Software providers/i.test(copy));
    }

  /* Every hook the page uses has to be one a script actually wires. Both
     scripts are read, not just site.js: the answer strip is drawn by
     74-slot-strip.js and reads hooks of its own, and reading only site.js meant
     those had to be hand-listed below as though they were unhandled. */
  const siteJs = fs.readFileSync(path.join(ROOT, "assets", "site.js"), "utf8")
    + fs.readFileSync(
        path.join(ROOT, "assets", "diagrams", "74-slot-strip.js"), "utf8");
  const wired = new Set((siteJs.match(/querySelectorAll\("\[([\w-]+)/g) || [])
    .map((s) => s.replace(/.*\[/, "")));
  //  and the ones a script reads with getAttribute rather than selects on
  (siteJs.match(/getAttribute\("(data-[\w-]+)"\)/g) || []).forEach((m) =>
    wired.add(m.replace(/.*"(data-[\w-]+)".*/, "$1")));
  const hooks = new Set();
  (function walk(n) {
    Object.keys(n.attributes || {}).forEach((k) => {
      if (k.indexOf("data-") === 0) hooks.add(k);
    });
    n.childNodes.forEach((c) => { if (c.tagName) walk(c); });
  })(doc._root);
  const known = new Set([...wired, "data-base", "data-theme",
    "data-size", "data-repo", "data-term", "data-label", "data-home",
    "data-destination", "data-scale-controls", "data-scale-live",
    "data-copied", "data-haystack", "data-schema", "data-heading-level",
    "data-status", "data-state", "data-criterion", "data-section"]);
  const unwired = [...hooks].filter((h) => !known.has(h));
  check(`${name}: every data hook on the page is wired in site.js`,
        unwired.length === 0, JSON.stringify(unwired));

  /* Every snippet named on the page exists and rendered. */
  doc.querySelectorAll(".snippet__body pre").forEach((pre, index) => {
    check(`${name}: scrollable extract ${index + 1} is keyboard accessible`,
          pre.getAttribute("tabindex") === "0"
          && pre.getAttribute("role") === "region"
          && Boolean(pre.getAttribute("aria-label")));
  });
  const snippets = doc.querySelectorAll("[data-snippet]");
  snippets.forEach((s) => {
    const id = s.getAttribute("data-snippet");
    const exists = fs.existsSync(path.join(ROOT, "data", "snippets", id + ".json"))
      || fs.existsSync(path.join(ROOT, "data", "schema-evidence", id + ".json"));
    check(`${name}: snippet ${id} exists in data/`, exists);
    check(`${name}: snippet ${id} rendered a body`,
          s.querySelectorAll(".snippet__body").length === 1);
  });

  /* Every schema fragment named on the page exists and rendered, and is
     labelled as schema evidence rather than as corpus content. */
  doc.querySelectorAll("[data-schema]").forEach((s2) => {
    const id = s2.getAttribute("data-schema");
    check(`${name}: schema fragment ${id} exists in data/schema-evidence`,
          fs.existsSync(path.join(ROOT, "data", "schema-evidence", id + ".json")));
    check(`${name}: schema fragment ${id} rendered a body`,
          s2.querySelectorAll(".snippet__body").length === 1);
    check(`${name}: schema fragment ${id} is labelled schema evidence`,
          /schema evidence, not corpus content/.test(textOf(s2)));
  });

  /* Gate 7: the site carries no quotations and names nobody. The name list
     comes from data/quotes.json, which is retained as provenance and is
     therefore the register of who must not appear. Snippet source paths carry
     the organizations and are excluded, because a path is provenance and
     stripping it would break the thing the whole site rests on. */
  check(`${name}: renders no quotation`,
        doc.querySelectorAll("[data-quote]").length === 0 &&
        doc.querySelectorAll(".quote").length === 0);
  const people = [...new Set(JSON.parse(
    fs.readFileSync(path.join(ROOT, "data", "quotes.json"), "utf8"))
    .quotes.map((q) => q.speaker).filter(Boolean))];
  let visible = "";
  (function walk(n) {
    n.childNodes.forEach((c) => {
      if (!c.tagName) { visible += " " + c.textContent; return; }
      if (c.classList.contains("snippet__src")) return;
      if (c.classList.contains("path")) return;
      if (["SCRIPT", "STYLE", "SVG"].indexOf(c.tagName) !== -1) return;
      walk(c);
    });
  })(doc._root);
  const named = people.filter((p2) => visible.indexOf(p2) !== -1);
  check(`${name}: names none of the ${people.length} people on the record`,
        named.length === 0, JSON.stringify(named));
  const orgs = ["Easy Dynamics", "IBM"].filter((o) => {
    const main = doc.querySelectorAll("main")[0];
    if (!main) return false;
    let t = "";
    (function walk(n) {
      n.childNodes.forEach((c) => {
        if (!c.tagName) { t += " " + c.textContent; return; }
        /* A file path is provenance and legitimately names the organization
           whose repository it came from. Prose may not.
           .verbatim marks reproduced source text, which is exempt for the same
           reason: three of the thirteen editorial rules are rules about how the
           publishing organizations are treated and name them, and publishing an
           editorial policy with the policy redacted would be pointless. The
           exemption covered the reproduction and not a sentence the site
           wrote. The methodology page has been removed and with it the only use
           of .verbatim, so the branch below is now unreachable; it is kept
           because the exemption is a rule about markup rather than about that
           page, and a reproduced rule could be published again. */
        if (c.classList.contains("snippet__src")) return;
        if (c.classList.contains("path")) return;
        if (c.classList.contains("verbatim")) return;
        if (["SCRIPT", "STYLE", "SVG", "DETAILS"].indexOf(c.tagName) !== -1) return;
        walk(c);
      });
    })(main);
    return t.indexOf(o) !== -1;
  });
  /* A renderer reading a field that no longer exists prints the word undefined
     into the page. Gate 7 removed the organization from data/six-questions.json and one
     renderer kept reading it, so every question heading on two pages read
     "(Option C, undefined)" until this check existed. */
  check(`${name}: renders no missing value as the word undefined`,
        !/\bundefined\b/.test(visible),
        (visible.match(/.{0,40}\bundefined\b.{0,20}/) || [""])[0].trim());

  /* The rule keeps an argument from being attributed to a company anywhere it
     is being weighed, and it now has no exception.

     The artifacts page used to be one: its subject is which group published
     which document, and an inventory redacting the publisher was held to be
     useless. It is not. The inventory is of what each approach ships, which is
     the same set of files under the name the rest of the site uses for them,
     and every other page had been talking about approaches for weeks while
     this one talked about companies.

     What is banned is proponent attribution. The publishers of the guidance
     being read, CIS, DISA, CISA, NIST and AWS in its Security Hub role, are
     named wherever they are the source of a document, because a benchmark
     cannot be cited without citing who wrote it. */
  check(`${name}: names no proponent organization in its prose`,
        orgs.length === 0, JSON.stringify(orgs));

  /* The head is prose too, and it was exempt because the walk above starts at
     <main>. The artifacts page was relabelled by approach and its meta
     description was not, so it went on reading "Every OSCAL document AWS, IBM
     and Easy Dynamics have published" for as long as the body said otherwise.
     Nothing on the page showed it and every check passed; a search engine and a
     link preview would have shown it to everybody. */
  const desc = (doc.querySelectorAll('meta[name="description"]')[0] || {})
    .getAttribute ? doc.querySelectorAll('meta[name="description"]')[0]
      .getAttribute("content") || "" : "";
  const titled = doc.querySelectorAll("title")[0];
  const head = desc + " " + (titled ? titled.textContent : "");
  const headOrgs = ["Easy Dynamics", "IBM"].filter((o) => head.indexOf(o) !== -1);
  check(`${name}: nor in the title and description a search engine shows`,
        headOrgs.length === 0, JSON.stringify(headOrgs));
  check(`${name}: which is written, and says something`,
        desc.split(/\s+/).filter(Boolean).length >= 12, desc.slice(0, 40));

  /* --- how a capability is enabled ---------------------------------------
     The second axis, and the second group of the one legend. It was a legend of
     its own in a section of its own, two screens below the answers it decoded;
     it is a group inside the answer legend now, and the legend sits above the
     answers rather than under them.

     Every badge has to be decodable from it: a badge on a cell with no entry in
     the legend is a mark a reader cannot read. That used to be checked only
     where a legend already existed, so the one failure it was written to catch,
     badges drawn and no legend to read them by, was the one it could not see.
     Since the group is opt-in per page it is now the first thing asserted. */
  const sixQ = JSON.parse(
    fs.readFileSync(path.join(path.dirname(__dirname), "data", "six-questions.json"), "utf8"));
  const mechLegend = doc.querySelectorAll(".mech-legend");
  if (doc.querySelectorAll(".mech-row").length) {
    check(`${name}: draws mechanism badges, so it carries the vocabulary`,
          mechLegend.length === 1,
          `${doc.querySelectorAll(".mech-row").length} badge row(s), `
          + `${mechLegend.length} legend group(s)`);
  }
  if (mechLegend.length) {
    check(`${name}: the mechanism legend appears once`, mechLegend.length === 1,
          `${mechLegend.length}`);
    const shown = mechLegend[0].querySelectorAll(".mech")
      .map((b) => textOf(b));
    check(`${name}: it covers every mechanism the data defines`,
          JSON.stringify(shown) === JSON.stringify(
            sixQ.mechanism_states.map((m) => m.short)),
          JSON.stringify(shown));
    check(`${name}: and says what each one means`,
          sixQ.mechanism_states.every((m) =>
            textOf(mechLegend[0]).includes(m.meaning.slice(0, 40))));
  }
  /* Every badge drawn anywhere has to be one the legend defines. */
  const vocab = new Set(sixQ.mechanism_states.map((m) => m.short));
  const badges = doc.querySelectorAll(".mech").map((b) => textOf(b));
  check(`${name}: every mechanism badge is one the legend defines`,
        badges.every((b) => vocab.has(b)),
        JSON.stringify(badges.filter((b) => !vocab.has(b)).slice(0, 4)));

  /* --- an extract carries its own address --------------------------------
     An extract is evidence, so a reader has to be able to reach the file it
     came from and see which question it answers. Both used to be missing: the
     path was plain text and the question was a box with a digit in it. */
  doc.querySelectorAll("[data-snippet]").forEach((s) => {
    const id = s.getAttribute("data-snippet");
    const src = s.querySelectorAll(".snippet__src")[0];
    if (!src) return;
    check(`${name}: extract ${id} shows where it came from`,
          textOf(src).length > 10, textOf(src));
    /* Only one publisher has a public repository on the record, so only that
       one gets a link. A link for the other two would go nowhere. */
    const linked = src.querySelectorAll("a")[0];
    const fromRepo = textOf(src).indexOf("AWS/oscal-content-for-aws-services") === 0;
    if (fromRepo) {
      check(`${name}: extract ${id} links to the published file`,
            !!linked && /^https:\/\/github\.com\//.test(linked.getAttribute("href")),
            linked ? linked.getAttribute("href") : "no link");
    } else {
      check(`${name}: extract ${id} does not link where no repository exists`,
            !linked, linked ? linked.getAttribute("href") : "");
    }
    check(`${name}: extract ${id} offers an obvious way to open it`,
          s.querySelectorAll(".snippet__open").length === 1);
  });
  /* A question chip has to name the question, not just number it. */
  doc.querySelectorAll(".slot-chip").forEach((c) => {
    check(`${name}: a question chip is labelled, not a bare digit`,
          c.querySelectorAll(".slot-chip__name").length === 1
          && textOf(c.querySelectorAll(".slot-chip__name")[0]).length > 2,
          textOf(c));
  });

  /* --- every answer is written down, not encoded -------------------------
     This replaced a row of coloured boxes that encoded the question as a
     hue and the answer as a border treatment, and wrote neither down. The check
     is that every row says what it means in words, so the palette can never
     quietly become load-bearing again. */
  doc.querySelectorAll("[data-strip]").forEach((s) => {
    const key = s.getAttribute("data-strip");
    const rows = s.querySelectorAll(".answers__row");
    if (!rows.length) return;
    check(`${name}: ${key} answers all seven rows`, rows.length === 7,
          `${rows.length}`);
    const named = rows.filter((r) => textOf(r.querySelectorAll(".answers__q")[0] ||
                                            { textContent: "" }).length > 2);
    check(`${name}: ${key} names every question rather than numbering it only`,
          named.length === rows.length, `${named.length} of ${rows.length}`);
    const worded = rows.filter((r) => {
      const w = textOf(r.querySelectorAll(".answers__word")[0] || { textContent: "" });
      return /^(Answered|Partly answered|Not answered)$/.test(w);
    });
    check(`${name}: ${key} states every answer in words`,
          worded.length === rows.length, `${worded.length} of ${rows.length}`);
    /* The reason is not on the row. It was, and a row that sometimes carried
       one and sometimes did not made the three lists drift out of alignment, so
       a reader comparing across them had to find question 4 three times. It
       lives in the row's tooltip and in the legend now. */
    check(`${name}: ${key} keeps the reason off the row`,
          rows.every((r) => r.querySelectorAll(".answers__why").length === 0));
    /* The reason used to be appended to the tooltip too, as "Not answered, no
       position stated". The state is one of three words now, everywhere it is
       written, and the tooltip carries the cell's own note, which is the
       evidence and says more than a stock phrase would. */
    const unanswered = rows.filter((r) =>
      textOf(r.querySelectorAll(".answers__word")[0] || { textContent: "" }) === "Not answered");
    check(`${name}: ${key} says why on every unanswered row, from the cell`,
          unanswered.every((r) => (r.getAttribute("title") || "").length > 40),
          `${unanswered.length} unanswered`);
    check(`${name}: ${key} carries its evidence on every row`,
          rows.every((r) => (r.getAttribute("title") || "").length > 40));
    /* Every row is the same shape, which is what lets three lists line up. */
    check(`${name}: ${key} rows are all the same shape`,
          rows.every((r) => r.querySelectorAll(".answers__n").length === 1
                         && r.querySelectorAll(".answers__q").length === 1
                         && r.querySelectorAll(".answers__swatch").length === 1
                         && r.querySelectorAll(".answers__word").length === 1));
  });

  /* --- a number means nothing on its own -------------------------------
     The six questions are numbered 1 to 6, with 6a and 6b. Those numbers are
     shorthand and carry nothing by themselves, so a page may use one only where
     a reader can find out what it means: either the page shows the list, or the
     number is accompanied by the question's name.

     The primer broke both halves: it referred to "question 2" twice, showed no
     list, and never introduced the framework, because it was the page a reader
     met before the framework existed for them. That page is gone and its list of
     the six questions is now section 3 of the start page, which is the half of
     the fix that mattered. */
  const showsTheList =
    doc.querySelectorAll("[data-board]").length > 0 ||
    doc.querySelectorAll("[data-strip]").length > 0 ||
    doc.querySelectorAll(".matrix").length > 0 ||
    /* The accordion stack is a list of the six questions with their names, so a
       page carrying it can use a bare number: the reader can look it up on the
       same screen. */
    doc.querySelectorAll(".qacc").length > 0 ||
    doc.querySelectorAll("[data-slot-fill]").length > 0;
  if (!showsTheList) {
    const anat = JSON.parse(
      fs.readFileSync(path.join(ROOT, "data", "six-questions.json"), "utf8"));
    const names = anat.slots.reduce((acc, s) => {
      acc[s.number] = [s.short, s.name].filter(Boolean);
      return acc;
    }, {});
    let prose = "";
    (function walk(n) {
      n.childNodes.forEach((c) => {
        if (!c.tagName) { prose += " " + c.textContent; return; }
        if (c.classList.contains("path")) return;
        if (["SCRIPT", "STYLE", "SVG", "PRE"].indexOf(c.tagName) !== -1) return;
        walk(c);
      });
    })(doc.querySelectorAll("main")[0] || doc._root);
    prose = prose.replace(/\s+/g, " ");

    const re = /questions? (6a|6b|\d)\b/gi;
    let m;
    const bare = [];
    while ((m = re.exec(prose))) {
      const num = m[1].toLowerCase();
      const around = prose.slice(Math.max(0, m.index - 90),
                                 m.index + m[0].length + 110).toLowerCase();
      /* The prose is allowed to name the question in its own words: "the link
         to a control" is the name of question 2 even though the canonical name
         reads "how the rule links to a control". So the match is on the
         distinctive words of the name rather than on the whole string, compared
         by four-character prefix so a plural or a tense does not break it. */
      const STOP = new Set(["how", "the", "and", "for", "that", "this", "with",
        "what", "whether", "someone", "else", "can", "add", "later", "does",
        "itself", "its", "was", "when", "who", "runs", "against"]);
      const stems = (s2) => (String(s2).toLowerCase().match(/[a-z]+/g) || [])
        .filter((w) => w.length >= 4 && !STOP.has(w))
        .map((w) => w.slice(0, 4));
      const want = [...new Set((names[num] || []).flatMap(stems))];
      const have = new Set(stems(around));
      const hits = want.filter((w) => have.has(w)).length;
      const named = (names[num] || []).some((n2) =>
                      around.indexOf(String(n2).toLowerCase()) !== -1)
                    || hits >= Math.min(2, want.length);
      if (!named) bare.push(prose.slice(m.index, m.index + 60).trim());
    }
    check(`${name}: no question number appears without its name`,
          bare.length === 0, JSON.stringify(bare.slice(0, 3)));
  }

  /* --- a mark is only worth reading if something says what it means -------
     The swatch carries which of the three kinds of unanswered a row is, now
     that the reason is off the row. So any page showing answer lists has to
     show a legend, and the legend has to name the geometry rather than only the
     state, or the dotted fill and the plain outline are two marks a reader has
     no way to tell apart. */
  /* The gate is the mark itself, not the answer list that was the first thing
     to carry one. It used to be `.answers__row`, which is only the list, so the
     two pages that draw marks another way were never asked the question:
     questions.html paints six in its fills and was exempt from every assertion
     in this block. A reader does not know which renderer drew a dotted box. If a
     page draws one, it owes an answer. */
  const marks = doc.querySelectorAll(".state-swatch").length +
                doc.querySelectorAll(".answers__swatch").length;
  if (marks) {
    const legends = doc.querySelectorAll(".answers-legend")
    .filter((l) => !l.classList.contains("mech-legend"));
    check(`${name}: shows a legend for the marks`, legends.length > 0,
          `${marks} mark(s), no legend`);
    /* Two legends is a reader asking which one is current. The mechanism
       vocabulary was a second one until it became a group inside this one. */
    check(`${name}: shows the legend once`, legends.length <= 1,
          `${legends.length} legends`);
    /* A key belongs before the thing it decodes. This one was under the
       answers, so a reader met three swatches and a badge row with nothing
       yet to read them by and had to scroll past all seven questions to find
       out what they meant. Compared on source position, which is what the
       reading order follows. */
    if (legends.length === 1) {
      const src = fs.readFileSync(path.join(ROOT, name), "utf8");
      check(`${name}: the legend comes before the answers it decodes`,
            src.indexOf("data-answers-legend") < src.indexOf("data-question-stack")
            || src.indexOf("data-question-stack") === -1);
    }
    legends.forEach((lg, i) => {
      const items = lg.querySelectorAll(".answers-legend__item");
      /* Counted from the data rather than hardcoded. The list shrank when a
         state stopped describing any cell, and a hardcoded five then failed on
         seven pages at once for a reason that had nothing to do with the pages. */
      check(`${name}: legend ${i + 1} covers every state the data declares`,
            items.length === sixQ.answer_states.length,
            `${items.length} of ${sixQ.answer_states.length}`);
      /* Three words and three marks. The legend used to spell out the
         geometry beside each label and a reason after it; both described the
         drawing a reader can already see, so the check now asserts the
         opposite: that neither is there and the label stands alone. */
      check(`${name}: legend ${i + 1} states each answer state in one label`,
            items.every((it) =>
              textOf(it.querySelectorAll(".answers__word")[0] ||
                     { textContent: "" }).trim().length > 3));
      check(`${name}: legend ${i + 1} does not describe the drawing`,
            lg.querySelectorAll(".answers-legend__shape").length === 0
            && lg.querySelectorAll(".answers__why").length === 0);
    });
  }

  /* --- one order, everywhere ---------------------------------------------
     The three approaches appear in the pre-read's option-letter order: A, B, C.
     Ordering is the single easiest way for this site to argue without saying
     anything, so it is asserted on every page and for every construct that
     carries the three, rather than only where a page happens to state it.

     This is what caught six places still carrying the old order after the
     change: two hard-coded lists inside renderers, three sets of cards written
     into markup, and one page map. */
  const ORDER_KEYS = ["catalog-first", "component-first", "assessment-first"];
  [["[data-strip]", "data-strip", "strips"],
   ["[data-appendix]", "data-appendix", "appendix sections"]].forEach(
    ([sel, attr, what]) => {
      const found = doc.querySelectorAll(sel).map((n) => n.getAttribute(attr));
      if (!found.length) return;
      /* A page may repeat the set, as the start page does. Every run of three
         has to be in the order. */
      for (let i = 0; i + 3 <= found.length; i += 3) {
        check(`${name}: ${what} ${i / 3 + 1} in option-letter order`,
              JSON.stringify(found.slice(i, i + 3)) === JSON.stringify(ORDER_KEYS),
              JSON.stringify(found.slice(i, i + 3)));
      }
    });
  const approachLinks = doc.querySelectorAll(".cards .card h3 a")
    .map((a) => (a.getAttribute("href") || "").replace(/^\.\//, "").replace(/\.html$/, ""))
    .filter((h) => ORDER_KEYS.indexOf(h) !== -1);
  if (approachLinks.length === 3) {
    check(`${name}: approach cards in option-letter order`,
          JSON.stringify(approachLinks) === JSON.stringify(ORDER_KEYS),
          JSON.stringify(approachLinks));
  }
  const fillHeads = doc.querySelectorAll(".slot-fill__head")
    .map((h) => textOf(h).split(" (")[0]);
  for (let i = 0; i + 3 <= fillHeads.length; i += 3) {
    check(`${name}: question block ${i / 3 + 1} in option-letter order`,
          JSON.stringify(fillHeads.slice(i, i + 3)) === JSON.stringify(OPTION_ORDER),
          JSON.stringify(fillHeads.slice(i, i + 3)));
  }
  /* And the navigation, which is the order a reader meets first. */
  const navApproaches = doc.querySelectorAll(".site-nav a")
    .map((a) => (a.getAttribute("href") || "").replace(/^\.\//, "").replace(/\.html$/, ""))
    .filter((h) => ORDER_KEYS.indexOf(h) !== -1);
  check(`${name}: the navigation lists the three in option-letter order`,
        JSON.stringify(navApproaches) === JSON.stringify(ORDER_KEYS),
        JSON.stringify(navApproaches));

  /* --- the overview-first layer -----------------------------------------
     Collapsing content is only an improvement if every collapsed thing is still
     addressable and still reachable. Both are properties of the markup rather
     than of the script, so both are checked here. */
  const discs = doc.querySelectorAll("details.qcard, details.panel");
  if (discs.length) {
    /* Addressable: a card carries its own id, and a panel is reached through the
       section that holds it, which site.js opens on arrival. */
    const unaddressable = discs.filter(
      (d) => !d.id && !(d.closest("section") || {}).id);
    check(`${name}: every collapsible block can be linked to`,
          unaddressable.length === 0,
          `${unaddressable.length} of ${discs.length} reachable by no anchor`);
    const ids = discs.map((d) => d.id).filter(Boolean);
    check(`${name}: those ids are unique`,
          new Set(ids).size === ids.length, JSON.stringify(ids));
    /* Direct-child summaries only. A panel legitimately contains extracts, and
       every extract is a details with a summary of its own. */
    const own = (d, sel) => d.querySelectorAll(sel).filter((n) => n.parentNode === d);
    const summaries = discs.filter((d) => own(d, "summary").length === 1);
    check(`${name}: every collapsible block has exactly one summary of its own`,
          summaries.length === discs.length,
          `${summaries.length} of ${discs.length}`);
    /* A panel holds a whole section, so its heading has to stay in the summary
       where it is announced and where the numbering check can see it. */
    const panels = doc.querySelectorAll("details.panel");
    const headed = panels.filter((p) => {
      const s = p.querySelectorAll("summary").filter((n) => n.parentNode === p)[0];
      return s && s.querySelectorAll("h2, h3").length === 1;
    });
    check(`${name}: every panel keeps its heading in its summary`,
          headed.length === panels.length, `${headed.length} of ${panels.length}`);
    const subbed = panels.filter((p) => p.querySelectorAll(".panel__sub").length === 1);
    check(`${name}: every panel says what is inside it before you open it`,
          subbed.length === panels.length, `${subbed.length} of ${panels.length}`);
  }

  /* Every diagram named on the page exists as a file. */
  doc.querySelectorAll("[data-diagram]").forEach((d) => {
    const n2 = d.getAttribute("data-diagram");
    check(`${name}: diagram ${n2}.svg exists`,
          fs.existsSync(path.join(ROOT, "assets", "diagrams", n2 + ".svg")));
  });

  /* Every same-page link resolves to something on the page. */
  const ids = new Set();
  (function walk(n) {
    if (n.id) ids.add(n.id);
    n.childNodes.forEach((c) => { if (c.tagName) walk(c); });
  })(doc._root);
  const dangling = doc.querySelectorAll("a")
    .map((a) => a.getAttribute("href") || "")
    .filter((h) => h.indexOf("#") === 0 && h.length > 1)
    .filter((h) => !ids.has(h.slice(1)));
  check(`${name}: every same-page link resolves`, dangling.length === 0,
        JSON.stringify([...new Set(dangling)].slice(0, 5)));

  /* Term cards. Regression test for a real bug: initGlossary used to bind a
     listener per .dfn button at boot, so it wired only the buttons written into
     the markup and silently missed every one a renderer produced afterwards.
     Clicking a renderer-made button is the only way to see that, so the check
     clicks one of each kind and asserts the card filled. */
  const dfns = doc.querySelectorAll(".dfn");
  if (dfns.length) {
    const gloss = JSON.parse(
      fs.readFileSync(path.join(ROOT, "data", "glossary.json"), "utf8"));
    const known = new Set(gloss.terms.map((t) => t.term));
    const unknown = dfns.map((b) => b.getAttribute("data-term"))
      .filter((t) => !known.has(t));
    check(`${name}: every term card names a glossary term`,
          unknown.length === 0, JSON.stringify([...new Set(unknown)]));

    const card = doc.getElementById("dfn-card");
    check(`${name}: the term card element exists`, !!card);
    /* One button from the markup and one from a renderer, if the page has
       both. The renderer-made one is the case that used to fail. */
    const inMarkup = dfns.filter((b) => !b.closest("[data-models]")
                                        && !b.closest("[data-readers]"));
    const fromRenderer = dfns.filter((b) => b.closest("[data-models]")
                                            || b.closest("[data-readers]"));
    [["written into the markup", inMarkup[0]],
     ["created by a renderer", fromRenderer[0]]].forEach(([what, btn]) => {
      if (!btn || !card) return;
      card.hidden = true;
      card.innerHTML = "";
      btn.dispatchEvent({ type: "click", target: btn });
      check(`${name}: a term card ${what} opens on click`,
            card.hidden === false && card.innerHTML.indexOf(
              btn.getAttribute("data-term")) !== -1,
            `hidden=${card.hidden}, html=${card.innerHTML.slice(0, 40)}`);
    });
  }

  /* House style, recorded at Gate 5. The register is modelled on the OSCAL
     Foundation focus group discussions: numbered sections, bold lead-in labels,
     declarative technical prose. Two habits are ruled out because they read as
     rhetoric rather than as reference: aphoristic section headings, and
     headings numbered as spelled-out ordinals. */
  /* A section heading is one the author wrote. Headings inside a rendered
     component name a term, an approach or a reader, and numbering those would
     be wrong. */
  const inComponent = (h) =>
    ["card", "glossary__item", "slot-fill", "worked", "models__layer",
     "position-group", "two-up__side", "audit", "rules__item",
     "answers-row__col", "qacc"]
      .some((c) => h.closest("." + c))
    || ["data-views", "data-readers", "data-glossary", "data-slot-fill",
        "data-matrix", "data-sc28", "data-position-questions", "data-contribute",
        "data-question-sides", "data-approach-cards",
        "data-audits", "data-rules", "data-does-not", "data-verification",
        "data-answers-row"].some((d) => h.closest("[" + d + "]"));
  /* The question chip's number and name land in front of the heading text. */
  const headText = (h) => {
    let out = "";
    (function walk(n) {
      n.childNodes.forEach((c) => {
        if (!c.tagName) { out += c.textContent; return; }
        if (c.classList.contains("slot-chip")) return;
        walk(c);
      });
    })(h);
    return out.replace(/\s+/g, " ").trim();
  };

  const heads = doc.querySelectorAll("main h2").filter((h) => !inComponent(h));
  const subs = doc.querySelectorAll("main h3").filter((h) => !inComponent(h));
  check(`${name}: has numbered sections`, heads.length > 0);
  const bad2 = heads.map(headText).filter((t) => !/^\d+\.\s/.test(t));
  check(`${name}: every section heading is numbered`, bad2.length === 0,
        JSON.stringify(bad2.slice(0, 4)));
  const bad3 = subs.map(headText).filter((t) => !/^\d+\.\d+\s/.test(t));
  check(`${name}: every subsection heading is numbered`, bad3.length === 0,
        JSON.stringify(bad3.slice(0, 4)));
  const ordinal = heads.concat(subs).map(headText)
    .filter((t) => /^(One|Two|Three|Four|Five|Six|Seven|Eight|Nine)\b\.?\s/.test(t));
  check(`${name}: no heading is a spelled-out ordinal`, ordinal.length === 0,
        JSON.stringify(ordinal));

  /* Heading levels have to descend by one. A jump is a real defect for anyone
     navigating by heading, and it is invisible in a visual review. */
  const levels = [];
  (function walk(n) {
    n.childNodes.forEach((c) => {
      if (!c.tagName) return;
      if (/^H[1-6]$/.test(c.tagName)) levels.push([+c.tagName[1], textOf(c).slice(0, 50)]);
      walk(c);
    });
  })(doc._root);
  const jumps = levels.filter((l, i) => i > 0 && l[0] > levels[i - 1][0] + 1)
    .map((l) => `h${l[0]} after h${levels[levels.indexOf(l) - 1][0]}: ${l[1]}`);
  check(`${name}: heading levels never skip`, jumps.length === 0,
        JSON.stringify(jumps.slice(0, 3)));

  /* Two pages have a per-page function, and the approach pages share a third.
     checkApproach, checkQuestions and checkIndex were lost to a bad edit and
     have not been rebuilt. Everything above this line runs on every page and is
     what holds the rest of the site. */
  if (name === "six-questions.html") {
    await checkSixQuestions(name, doc);
    checkRuns(name, doc);
  }
  if (/^(assessment|catalog|component)-first\.html$/.test(name)) {
    checkTradeoffs(name, doc);
    checkApproachShape(name, doc);
    checkRuns(name, doc);
  }
  RENDERED[name] = doc;
}

/* What an approach page must not carry, and where its links have to land.

   Section 3 was the six questions answered one at a time for this approach,
   with an answer strip above them. Both are gone: six-questions.html answers
   the same seven rows with all three columns visible, and one column of that
   on its own page was the same content read twice with nothing beside it to
   compare against.

   Which leaves the chain pointing off the page. Each step names the two stages
   it runs between and links each of them to the question it belongs to, and
   those links cross to the six questions page.
   A broken cross-page anchor is the kind that rots quietly: it does not 404,
   it lands at the top of the page and the reader assumes that is where they
   were sent. */
/* A run is items of one shape, so the row has something to line up on.
   Every item in a flow, a document tile or a mark, is a box on the first line
   with a word under it on the second. Mixing a two-line item with a one-line
   one is what put the marks half a caption below the tiles beside them, and a
   mark with no word under it left a reader inferring what the glyph meant. */
function checkRuns(name, doc) {
  const runs = doc.querySelectorAll(".mflow__run");
  if (!runs.length) return;
  let items = 0, boxed = 0, marks = 0, labelled = 0;
  runs.forEach((run) => {
    (run.childNodes || []).filter((k) => k.tagName).forEach((item) => {
      items += 1;
      if (item.classList && item.classList.contains("lineage__end")) {
        if (item.querySelectorAll(".lineage__box").length === 1
            && item.querySelectorAll(".lineage__q").length === 1) boxed += 1;
        if (item.classList.contains("lineage__end--mark")) {
          marks += 1;
          if (textOf(item.querySelectorAll(".lineage__q")[0] || {}).trim()) {
            labelled += 1;
          }
        }
      }
    });
  });
  check(`${name}: every item in a run is a box with a line under it`,
        boxed === items, `${boxed} of ${items}`);
  check(`${name}: and every mark in one says what it is`,
        marks > 0 && labelled === marks, `${labelled} of ${marks}`);
}

function checkApproachShape(name, doc) {
  check(`${name}: carries no answer strip, the six questions page has it`,
        doc.querySelectorAll(".slot-strip").length === 0);
  check(`${name}: carries no per-question walk`,
        doc.querySelectorAll("#slots").length === 0 &&
        doc.querySelectorAll("[id^=slot-]").length === 0);

  /* Two links a step, one per end, plus one for the block that opens the list.
     That first block is where the rule is defined and has one end rather than
     two, so the count is odd by exactly one. It was even before the block
     existed, and the parity was the whole check. */
  const links = doc.querySelectorAll(".joins__steps a");
  /* Descendant, not ".joins__steps > li": the shim in this file implements
     descendant and attribute selectors and not the child combinator, and it
     returns nothing rather than erroring on one it does not know. The list has
     no nested lists in it, so the two would select the same elements anyway. */
  const steps = doc.querySelectorAll(".joins__steps li").length;
  check(`${name}: every step of the chain links both of its ends`,
        steps >= 5 && links.length === (steps - 1) * 2 + 1,
        `${steps} steps, ${links.length} links`);
  const bad = links.map((a) => a.getAttribute("href") || "")
    .filter((h) => !/^\.\/six-questions\.html#q[0-9ab]+-[a-z-]+$/.test(h));
  check(`${name}: every join link crosses to the six questions page`,
        bad.length === 0, JSON.stringify(bad.slice(0, 3)));
  /* The status section is gone, and with it the completeness sentence this
     checked. It said what the published content conforms to, how complete it
     is and what the publisher says about it, which are facts about a corpus
     rather than about an approach: the artifacts page is where a corpus is
     described. On a page whose subject is the shape of an approach it read as
     a verdict on whoever published the files. */
  check(`${name}: carries no status section`,
        doc.querySelectorAll("#status").length === 0);

  const own = name.replace(".html", "");
  const foreign = links.map((a) => a.getAttribute("href") || "")
    .filter((h) => h && !h.endsWith("-" + own));
  check(`${name}: and lands in this approach's column, not another's`,
        foreign.length === 0, JSON.stringify(foreign.slice(0, 3)));
}

/* And the published extracts are gone with them.

   They were inside the per-question walk, one column of them per page, and the
   last two on each page were the evidence under the status section. Both are
   gone now, so an approach page draws no extract at all. The matrix still
   declares them per cell as snippet_ids and verify.py checks they resolve to a
   file: they stay as provenance, the record of which shipped file evidences
   which answer. */
function checkExtractsAreStatusOnly(docs) {
  Object.keys(docs).forEach((name) => {
    if (!/^(assessment|catalog|component)-first\.html$/.test(name)) return;
    check(`${name}: draws no published extract`,
          docs[name].querySelectorAll("[data-snippet]").length === 0);
  });
}

/* Resolved after every page is rendered, because the six questions page builds
   its answers in JavaScript and is read last. */
function checkJoinTargets(docs) {
  const six = docs["six-questions.html"];
  if (!six) return;
  Object.keys(docs).forEach((name) => {
    if (!/^(assessment|catalog|component)-first\.html$/.test(name)) return;
    const ids = docs[name].querySelectorAll(".joins__steps a")
      .map((a) => (a.getAttribute("href") || "").split("#")[1])
      .filter(Boolean);
    const missing = [...new Set(ids)]
      .filter((id) => six.querySelectorAll("#" + id).length === 0);
    check(`${name}: every join link lands on an answer that exists`,
          missing.length === 0, JSON.stringify(missing.slice(0, 3)));
  });
}

/* Section 1 of an approach page, as a reader meets it.

   tools/verify.py checks the data behind this block. What it cannot check is
   what the page does with the data, and the failure that matters here is
   visual: two columns of different lengths, or a figure rendering as an empty
   span, both of which read as an argument rather than as a bug. So this runs on
   the rendered page and looks at the marks a reader would see. */
function checkTradeoffs(name, doc) {
  const tr = JSON.parse(
    fs.readFileSync(path.join(ROOT, "data", "tradeoffs.json"), "utf8"));
  const key = name.replace(/\.html$/, "");
  /* Counted against this approach's own data rather than a shared number. The
     two were the same while every page carried three a side; they are not now,
     and a shared number would have asserted the rule that was dropped. */
  const mine = tr.approaches[key] || { pros: [], cons: [] };
  const sec = doc.querySelectorAll("#tradeoffs")[0];
  check(`${name}: section 2 is the strengths and risks block`, !!sec);
  if (!sec) return;

  const pros = sec.querySelectorAll(".tradeoffs__side--pro .tradeoff");
  const cons = sec.querySelectorAll(".tradeoffs__side--con .tradeoff");
  check(`${name}: renders its ${mine.pros.length} strengths`,
        pros.length === mine.pros.length, String(pros.length));
  check(`${name}: renders its ${mine.cons.length} risks`,
        cons.length === mine.cons.length, String(cons.length));

  /* Length parity, measured on what is on the page rather than on the source
     data, because that is what a reader compares.

     The bound is 30 per cent. It was 20 while every page carried three
     strengths and three risks, and with the counts now following the content a
     page can hold four of one and three of the other. A tight bound then makes
     prose length compensate for count, which is the distortion the count rule
     was retired for: it would have meant writing a fourth entry short enough
     not to unbalance the column, rather than long enough to say the thing.

     What guards the real concern is the total each approach spends, held across
     the three pages in tools/approach_pages.py. That bounds what a reader
     compares and says nothing about which column it falls in. */
  const len = (nodes) => nodes.reduce((n, e) => n + textOf(e).trim().split(/\s+/).length, 0);
  const p = len(pros), c = len(cons);
  check(`${name}: the two columns are within 30 per cent of each other`,
        Math.abs(p - c) <= Math.max(p, c) * 0.30, `${p} vs ${c}`);

  /* Every entry carries a mark, and the two marks are different drawings.
     Colour is the third channel here, after the word in the heading and the
     shape of the mark, and it is the only one a dichromat cannot use. */
  const unmarked = pros.concat(cons)
    .filter((e) => e.querySelectorAll(".tradeoff__mark").length === 0)
    .map((e) => textOf(e).slice(0, 40));
  check(`${name}: every entry carries a mark`, unmarked.length === 0,
        JSON.stringify(unmarked));
  const tick = sec.querySelectorAll(".tradeoffs__side--pro .tradeoff__mark svg path");
  const cross = sec.querySelectorAll(".tradeoffs__side--con .tradeoff__mark svg path");
  const d = (nodes) => [...new Set(nodes.map((n) => n.getAttribute("d")))];
  check(`${name}: the strength mark is one drawing`, d(tick).length === 1,
        JSON.stringify(d(tick)));
  check(`${name}: the risk mark is another`, d(cross).length === 1,
        JSON.stringify(d(cross)));
  check(`${name}: and the two are not the same drawing`,
        d(tick)[0] !== d(cross)[0]);

  /* A figure that did not resolve renders as an empty span, which on a page of
     prose looks like a typographical slip rather than a missing number. */
  const empty = sec.querySelectorAll("[data-stat], [data-cited]")
    .filter((n) => textOf(n).trim() === "")
    .map((n) => n.getAttribute("data-stat") || n.getAttribute("data-cited"));
  check(`${name}: every figure in the block resolved`, empty.length === 0,
        JSON.stringify(empty));

  /* The block says what it is for before it starts listing. */
  check(`${name}: the block says what it is for`,
        textOf(sec.querySelectorAll(".tier2 p")[0] || {}).trim().split(/\s+/).length >= 8);
}

/* ------------------------------------------------------ six-questions.html -------
 * The page is one grid and nothing else, and the grid runs north to south. A
 * four-column table was the wrong shape here: every cell had a quarter of the
 * width, and a reader following one question read across a row while their eye
 * wanted to go down. Comparing all three at once is what the comparison page is
 * for, and it keeps the table.
 *
 * So: one accordion per question, closed, with the three approaches stacked
 * inside. These checks are that the stack is complete, that nothing is in
 * columns, and that each block carries the answer plus a link to the document
 * rather than the document itself. */

async function checkSixQuestions(name, doc) {
  const anat = JSON.parse(
    fs.readFileSync(path.join(path.dirname(__dirname), "data", "six-questions.json"), "utf8"));

  const accs = doc.querySelectorAll("details.qacc");
  check(`${name}: one accordion per question`, accs.length === anat.slots.length,
        String(accs.length));
  check(`${name}: each is anchored by its question`,
        JSON.stringify(accs.map((d) => d.id))
        === JSON.stringify(anat.slots.map((s) => "q-" + s.number)),
        JSON.stringify(accs.map((d) => d.id)));
  check(`${name}: every accordion starts closed`,
        accs.every((d) => d.getAttribute("open") === null));
  check(`${name}: every summary carries the question and its chip`,
        accs.every((d) => {
          const s = d.querySelectorAll("summary")[0];
          return s && s.querySelectorAll(".slot-chip").length === 1
                   && textOf(s.querySelectorAll(".qacc__q")[0] || {}).length > 10;
        }));

  /* No columns. This is the whole point of the rearrangement, so it is asserted
     rather than left to the stylesheet. */
  check(`${name}: nothing on the page is a table of approaches`,
        doc.querySelectorAll("table.matrix").length === 0
        && doc.querySelectorAll(".answers-row").length === 0);

  const blocks = doc.querySelectorAll(".qacc__one");
  check(`${name}: three approaches inside every question`,
        blocks.length === anat.slots.length * 3, String(blocks.length));

  /* One tab group per question, three tabs each, and every tab wired to a panel
     that exists. A tab pointing at nothing is a dead control, and the panel is
     hidden, so nothing on screen would say so. */
  const groups = doc.querySelectorAll(".qacc__tabs");
  const tabs = doc.querySelectorAll('[role="tab"]');
  const panels = doc.querySelectorAll('[role="tabpanel"]');
  check(`${name}: one tab group per question`,
        groups.length === anat.slots.length, String(groups.length));
  check(`${name}: three tabs and three panels per question`,
        tabs.length === anat.slots.length * 3
        && panels.length === anat.slots.length * 3,
        `${tabs.length} tabs, ${panels.length} panels`);
  const ids = new Set(panels.map((p) => p.id));
  check(`${name}: every tab controls a panel that exists`,
        tabs.every((t) => ids.has(t.getAttribute("aria-controls"))),
        JSON.stringify(tabs.filter((t) => !ids.has(t.getAttribute("aria-controls")))
          .map((t) => t.getAttribute("aria-controls")).slice(0, 3)));
  check(`${name}: every panel is labelled by its tab`,
        panels.every((p) => p.getAttribute("aria-labelledby")),
        String(panels.filter((p) => !p.getAttribute("aria-labelledby")).length));
  /* The approach names itself. The option lettering was removed from the site:
     it was the pre-read's shorthand, and on a page that shows the three side by
     side the name is the thing a reader needs. */
  check(`${name}: each tab names its approach`,
        tabs.every((t) => /^(Catalog|Component|Assessment)-first$/.test(textOf(t))),
        JSON.stringify(tabs.map((t) => textOf(t)).slice(0, 4)));
  check(`${name}: each states an answer state`,
        blocks.every((b) => textOf(b.querySelectorAll(".qacc__state")[0] || {}).length > 3));
  check(`${name}: each carries its construct and its note`,
        blocks.every((b) => b.querySelectorAll(".matrix__note").length === 1));
  /* Every answered cell names its model and its assemblies, in that order and
     with those labels, because saying it differently in each cell is what this
     replaced. */
  const carriers = doc.querySelectorAll(".carrier");
  check(`${name}: every model-and-assembly block names the model first`,
        carriers.every((c) =>
          textOf(c.querySelectorAll("dt")[0] || {}) === "Model"
          && c.querySelectorAll(".carrier__model").length === 1),
        String(carriers.length));
  check(`${name}: and labels the assemblies for number`,
        carriers.every((c) => {
          const dts = c.querySelectorAll("dt");
          if (dts.length < 2) return true;
          const n = c.querySelectorAll(".carrier__assembly").length;
          const p = c.querySelectorAll(".carrier__prop").length;
          /* A cell can carry its answer in a prop with no assembly around it,
             and then the row is labelled for the props instead. The label
             follows whichever kind is there rather than being fixed, because
             calling a prop an assembly is the mislabelling this block exists
             to prevent. */
          if (!n) return textOf(dts[1]) === (p === 1 ? "Prop" : "Props");
          /* Where the answer is a run rather than a place, the rows are per
             path and are labelled by whose run it is. The number label would
             be wrong there: it is not one list of assemblies with a count, it
             is one list per path, and the reader needs to know which is which.
             So the rule becomes that every row after the model names either a
             count or a path, and a path row carries assemblies. */
          const rest = dts.slice(1);
          if (rest.length && rest.every((d) => /path$/.test(textOf(d)))) {
            /* dt and dd alternate, so the row after a term is the one that
               holds its codes. The mini-DOM has no element sibling walk, and
               pairing by position is what the markup guarantees anyway. */
            const kids = (c.childNodes || []).filter((k) => k.tagName);
            const dds = kids.filter((k) => k.tagName === "DD");
            return dds.length === kids.length / 2
              && dds.slice(1).every(
                   (dd) => dd.querySelectorAll(".carrier__assembly").length > 0);
          }
          return textOf(dts[1]) === (n === 1 ? "Assembly" : "Assemblies");
        }));

  /* A prop box carries the prop's own name, and says it is a prop rather than
     leaving a dotted border to be decoded. The border matches the badge, but a
     border is not a label. */
  const propBoxes = doc.querySelectorAll(".carrier__prop");
  check(`${name}: every prop box names a prop`,
        propBoxes.every((p) => textOf(p).length > 2),
        String(propBoxes.length));
  check(`${name}: and says it is a prop rather than an assembly`,
        propBoxes.every((p) => /prop, not an assembly/i.test(p.getAttribute("title") || "")));

  /* The document is embedded, not linked. The walkthrough page it used to live
     on is gone, so these are the checks that page carried: every anchor a matrix
     link can name exists here, every block with a pointer shows the lines rather
     than a promise of them, and the gaps are stated rather than left blank. */
  /* The publisher's own extract, embedded. Every cell that names snippets in
     data/six-questions.json renders one <details class="snippet"> per id, and
     every cell that names none says so. Nothing on this page is authored for the
     comparison, so no invented namespace may appear here. */
  const root = path.dirname(__dirname);
  const pattern = JSON.parse(
    fs.readFileSync(path.join(root, "data", "pattern-examples.json"), "utf8"));
  /* The same rules, in the same order, in every column that answers per rule.
     A column may instead answer once for the whole document, which is a real
     difference rather than drift, so each column has to be one of those two
     shapes and the per-rule ones have to agree. */
  const shapes = JSON.parse(
    fs.readFileSync(path.join(root, "data", "six-questions.json"), "utf8"));
  /* A third shape. Question 5 answers once per path, because the runner's
     answer depends on who runs it: an implementer building the responses in a
     plan of record, an assessor producing a result from a plan they own. So a
     column there carries one block per path it has, keyed by the path. */
  const pathKeys = {};
  shapes.matrix.forEach((c) => {
    if (c.paths) {
      pathKeys[c.slot + "/" + c.approach] = [].concat.apply([], c.paths.map(
        (p) => [p.key + "-in", p.key + "-out"]));
    }
  });
  Object.keys(pattern.examples).forEach((q) => {
    const per = pattern.examples[q];
    const ruleKeys = pattern.rules.map((r) => r.key);
    const perRule = [];
    Object.keys(per).forEach((ap) => {
      const paths = pathKeys[q + "/" + ap] || [];
      const keys = new Set(ruleKeys.concat(["both"], paths));
      const core = per[ap].filter((b) => keys.has(b.rule));
      const shape = JSON.stringify(core.map((b) => b.rule));
      const byPath = paths.length
        && JSON.stringify(core.map((b) => b.rule).slice().sort())
           === JSON.stringify(paths.slice().sort());
      check(`${name}: question ${q}/${ap} answers per rule, once, or once per path`,
            shape === JSON.stringify(ruleKeys) || shape === '["both"]' || byPath,
            shape);
      if (shape === JSON.stringify(ruleKeys)) {
        perRule.push(JSON.stringify(core.map((b) => b.label)));
      } else if (byPath) {
        core.forEach((b) => check(
          `${name}: question ${q}/${ap}/${b.rule} says what that path shows`,
          b.label.length > 12, b.label));
      } else {
        check(`${name}: question ${q}/${ap} shared block says what it covers`,
              core.length === 1 && core[0].label.length > 12,
              core.map((b) => b.label).join(", "));
      }
    });
    check(`${name}: question ${q} uses the same rules in every option answering per rule`,
          new Set(perRule).size <= 1, perRule.join(" vs "));
  });
  const cells = {};
  anat.matrix.forEach((c) => { cells[c.slot + "|" + c.approach] = c; });

  let withSnips = 0, without = 0;
  anat.slots.forEach((s) => {
    ["catalog-first", "component-first", "assessment-first"].forEach((ap) => {
      const id = "q" + s.number + "-" + ap;
      const block = blocks.filter((b) => b.id === id)[0];
      check(`${name}: ${id} exists`, !!block);
      if (!block) return;
      /* Where we author the encodings, the block is ours and the label is the
         same in every column. That sameness is the whole point, so it is
         checked rather than trusted. */
      const pat = pattern.examples[s.number];
      const mine = (pat || {})[ap];
      if (pat && !(mine && mine.length)) {
        without += 1;
        /* Two shapes for the same fact. A cell that recorded what it looked
           for and what it found instead shows that evidence; one that did not
           says so in a sentence. Either way it shows no extract. */
        const why = block.querySelectorAll(".nothing__why")[0];
        check(`${name}: ${id} states that nothing is encoded here`,
              block.querySelectorAll("details.snippet").length === 0
              && (why
                  ? textOf(why).indexOf("Looked for") !== -1
                  : /position rather than a gap/
                    .test(textOf(block.querySelectorAll(".matrix__nojson")[0] || {}))));
        return;
      }
      if (mine && mine.length) {
        const dets = block.querySelectorAll("details.snippet");
        check(`${name}: ${id} carries our ${mine.length} encoding(s)`,
              dets.length === mine.length, `${dets.length}`);
        check(`${name}: ${id} labels them by rule`,
              JSON.stringify(dets.map((d) =>
                textOf(d.querySelectorAll(".snippet__title")[0] || {})))
              === JSON.stringify(mine.map((b) => b.label)));
        withSnips += mine.length;
        return;
      }
      /* Fallback for a question added to the framework before its encodings
         are written. Every question has them today, so this branch is the
         safety net rather than the path. */
      const cell = cells[s.number + "|" + ap] || {};
      const ids = cell.snippet_ids || [];
      const dets = block.querySelectorAll("details.snippet");
      if (ids.length) {
        withSnips += ids.length;
        check(`${name}: ${id} embeds its ${ids.length} published extract(s)`,
              dets.length === ids.length, `${dets.length}`);
        check(`${name}: ${id} names the extracts the data names`,
              JSON.stringify(dets.map((d) => d.getAttribute("data-snippet")))
              === JSON.stringify(ids),
              JSON.stringify(dets.map((d) => d.getAttribute("data-snippet"))));
        ids.forEach((sid) => {
          check(`${name}: ${sid} is a real extract on disk`,
                fs.existsSync(path.join(root, "data", "snippets", sid + ".json")));
        });
      } else {
        without += 1;
        check(`${name}: ${id} says nothing is published there`,
              dets.length === 0
              && /its position rather than a gap/
                 .test(textOf(block.querySelectorAll(".matrix__nojson")[0] || {})));
      }
    });
  });
  check(`${name}: every extract the data names is embedded`, withSnips > 0,
        String(withSnips));
  /* Every cell that has no encoding says so, and the number of them is the
     number the data has. This asserted "at least one" until the catalog
     approach's runner answer was written, which was the last cell on the site
     with nothing in it; a rule requiring the site to keep a gap is a rule
     against finishing. What is worth holding is the count: a cell that loses
     its encodings silently would push this above what the data declares. */
  let expected = 0;
  Object.keys(pattern.examples).forEach((q) => {
    ["catalog-first", "component-first", "assessment-first"].forEach((ap) => {
      const b = pattern.examples[q][ap];
      if (!(b && b.length)) expected += 1;
    });
  });
  check(`${name}: the ${expected} cell(s) with no encoding say so`,
        without === expected, `${without} against ${expected}`);
  check(`${name}: nothing links out to a separate walkthrough`,
        doc.querySelectorAll("a.matrix__json").length === 0);

  /* The whole point of sourcing from the publishers: no namespace of our own. */
  check(`${name}: no invented namespace appears on the page`,
        !/component-definition-focus-group/.test(doc.documentElement.innerHTML || ""));
}

/* The bare word is banned too, not just the numbered forms. index.html was
   carrying "the implementation slot expects a narrative one" and the earlier
   version of this pattern, which only looked for "six slots" and "slot N",
   walked straight past it. Slot was never an English word on this site: it
   was always the framework's name for a question. */
const RETIRED = /\bslots?\b/i;

function headingNumberAt(doc, anchor) {
  const node = doc.querySelectorAll(`#${anchor}`)[0];
  if (!node) return null;
  const heading = /^H[1-6]$/.test(node.tagName)
    ? node : node.querySelectorAll("h2, h3, h4")[0];
  if (!heading) return null;
  /* An h2 is numbered "2. Title"; an h3 is numbered "2.2 Title" with no dot
     after it. One alternative each, sub-heading first so the longer number
     wins. */
  const m = textOf(heading).match(/(\d+\.\d+(?:\.\d+)*)\s|(\d+)\.\s/);
  return m ? (m[1] || m[2]) : null;
}

/* The encodings live in one place, and all of them are there.

   They used to be on the approach pages too, and this function compared the two
   and asserted they were identical, which they were. They are on the six
   questions page only now: the same block on two pages was the same block
   twice, and the page that shows all three columns of it is the one where the
   comparison a reader is making is possible.

   So the check inverts. Every block data/pattern-examples.json declares has to
   be drawn on the six questions page, and no other page may draw one. Losing a
   block would be silent otherwise: the six questions page builds them in a
   loop, so a block dropped from the data disappears from the site without
   anything looking wrong. */
function checkEncodingsComplete() {
  const six = RENDERED["six-questions.html"];
  if (!six) return;
  const pattern = JSON.parse(fs.readFileSync(
    path.join(ROOT, "data", "pattern-examples.json"), "utf8"));

  const want = [];
  Object.keys(pattern.examples).forEach((q) => {
    const per = pattern.examples[q];
    Object.keys(per).forEach((ap) => {
      per[ap].forEach((b) => want.push(`q${q}-${ap}-${b.rule}`));
    });
  });

  const drawn = new Set();
  six.querySelectorAll("details.snippet").forEach((d) => {
    const id = d.getAttribute("id");
    if (id && d.querySelectorAll("pre").length) drawn.add(id);
  });

  const missing = want.filter((id) => !drawn.has(id));
  check(`six-questions.html: draws all ${want.length} encodings the data declares`,
        missing.length === 0, JSON.stringify(missing));

  /* The runner sits between an input and an output, and both ends are
     documents shown at other questions. The strip is a link rather than a third
     copy, so what is asserted is that both ends resolve to a question this page
     actually draws: a tile pointing at an anchor that is not there sends a
     reader to the top of the page and looks like nothing happened. */
  const sq = JSON.parse(fs.readFileSync(
    path.join(ROOT, "data", "six-questions.json"), "utf8"));
  sq.matrix.filter((c) => c.lineage).forEach((c) => {
    const panel = six.querySelectorAll(`#q${c.slot}-${c.approach}`)[0];
    const strip = panel ? panel.querySelectorAll(".lineage") : [];
    check(`six-questions.html: q${c.slot}/${c.approach} shows what the runner sits between`,
          strip.length === 1, `${strip.length} strips`);
    if (strip.length !== 1) return;
    const ends = strip[0].querySelectorAll(".lineage__end");
    const want = 1 + (c.lineage.out || []).length;
    check(`six-questions.html: q${c.slot}/${c.approach} names ${want} ends`,
          ends.length === want, `${ends.length}`);
    const bad = ends.map((a) => a.getAttribute("href") || "")
      .filter((h) => six.querySelectorAll(h).length !== 1);
    check(`six-questions.html: q${c.slot}/${c.approach} every end reaches its question`,
          bad.length === 0, JSON.stringify(bad));
    check(`six-questions.html: q${c.slot}/${c.approach} draws the runner mark`,
          strip[0].querySelectorAll(".mflow__runtime").length === 1);
  });

  /* An accordion holds nothing between its summary and its tabs. A paragraph
     stating something true of all three sat there briefly, above the tabs, and
     was removed as saying at length what the cell notes say in place. If one
     returns, this is where the check for it goes. */
  six.querySelectorAll("details.qacc").forEach((box) => {
    const body = box.querySelectorAll(".qacc__body")[0];
    const kids = (body ? body.childNodes : []).filter((n) => n.classList);
    check(`six-questions.html: ${box.getAttribute("id")} opens on its answers`,
          kids.length > 0 && kids[0].classList.contains("tabs"),
          kids.length ? (kids[0].getAttribute("class") || "?") : "empty");
  });

  /* And lights the part of each that answers the question. The spans are
     computed by the generator and committed; what this asserts is that the
     renderer actually applies them, which is the half the data cannot prove.
     Counted rather than sampled: a renderer that lit the first line of every
     block would pass a spot check and tell a reader nothing. */
  Object.keys(pattern.examples).forEach((q) => {
    const per = pattern.examples[q];
    Object.keys(per).forEach((ap) => {
      per[ap].forEach((b) => {
        const det = six.querySelectorAll(`details.snippet#q${q}-${ap}-${b.rule}`)[0];
        if (!det) return;
        const all = det.querySelectorAll(".snippet__line").length;
        const lit = det.querySelectorAll(".snippet__line.is-lit").length;
        const wantLines = b.content.split("\n").length;
        const wantLit = (b.focus || [])
          .reduce((n, s) => n + (s[1] - s[0] + 1), 0);
        check(`six-questions.html: q${q}/${ap}/${b.rule} wraps every line`,
              all === wantLines, `${all} of ${wantLines}`);
        check(`six-questions.html: q${q}/${ap}/${b.rule} lights ${wantLit} of them`,
              lit === wantLit, `${lit} of ${wantLit}`);
        /* Wrapping lines cannot change what the block says.
           A line is a block element, so it already starts on a line of its own.
           A newline left between two of them is a text node inside a <pre>,
           where white-space is preserved, and renders as a second break: the
           whole encoding came out double-spaced, and every count above still
           passed, because the line and lit totals were both right.
           So the lines are joined with nothing, and the newlines live in the
           layout rather than in the text. The clipboard is unaffected: the Copy
           button writes the block's own content, and a browser puts newlines
           back between block elements on a manual selection.
           What is asserted is that nothing else moved. Every character of every
           line, in order, with the line breaks taken out on both sides. If a
           newline survives into the markup this fails, because the left side
           will still have it and the right side will not. */
        const code = det.querySelectorAll("pre code")[0];
        const got = code ? (code.textContent || "") : "";
        const want = b.content.split("\n").join("");
        check(`six-questions.html: q${q}/${ap}/${b.rule} reads back unchanged`,
              got === want,
              got.length === want.length
                ? "same length, different text"
                : `${got.length} chars against ${want.length}`);
        /* Read off the markup, not the tree. The first version of this check
           compared textContent and passed with the bug still in: the shim drops
           a whitespace-only text node, so the newlines between the lines were
           invisible to it and both sides came out newline-free. A browser does
           not drop them, which is the whole reason the encoding was
           double-spaced on the page and green in the harness. */
        const raw = code ? (code.innerHTML || "") : "";
        check(`six-questions.html: q${q}/${ap}/${b.rule} leaves no newline `
              + `between its lines`,
              raw.indexOf("\n") === -1,
              `${raw.split("\n").length - 1} newline(s) in the markup`);
      });
    });
  });
  check("six-questions.html: and every one of them renders its JSON",
        want.every((id) => drawn.has(id)));

  ["assessment-first.html", "catalog-first.html", "component-first.html",
   "index.html", "questions.html", "scenario.html", "oscal-artifacts.html"]
    .forEach((page) => {
      const doc = RENDERED[page];
      if (!doc) return;
      check(`${page}: draws no encoding, they are on the six questions page`,
            doc.querySelectorAll("[data-pattern]").length === 0);
    });
}


function checkCrossPageReferences(docs) {
  const cited = /section (\d+(?:\.\d+)*) of the ([a-z ]+) page/;
  Object.keys(docs).forEach((name) => {
    const doc = docs[name];

    /* No page may show the retired vocabulary to a reader. Paths and source
       pointers are provenance and are exempt, as they are everywhere else. */
    let visible = "";
    (function walk(n) {
      n.childNodes.forEach((c) => {
        if (!c.tagName) { visible += " " + c.textContent; return; }
        if (c.classList.contains("snippet__src")) return;
        if (c.classList.contains("path")) return;
        if (["SCRIPT", "STYLE", "PRE", "CODE"].indexOf(c.tagName) !== -1) return;
        walk(c);
      });
    })(doc.querySelectorAll("main")[0] || doc._root);
    const retired = visible.match(RETIRED);
    check(`${name}: does not show the retired slot vocabulary`, !retired,
          retired ? JSON.stringify(retired[0]) : "");

    doc.querySelectorAll("a").forEach((a) => {
      const href = a.getAttribute("href") || "";
      const m = href.match(/^\.\/([a-z0-9-]+\.html)#([\w-]+)$/);
      if (!m) return;
      const said = textOf(a).match(cited);
      if (!said) return;
      const target = docs[m[1]];
      check(`${name}: cites a page that exists, ${m[1]}`, !!target);
      if (!target) return;
      const actual = headingNumberAt(target, m[2]);
      check(`${name}: "section ${said[1]}" matches the heading at ${m[1]}#${m[2]}`,
            actual === said[1], `heading says ${actual}`);
    });
  });
}

/* ------------------------------------------------------------------- main */

module.exports = { makeWindow, settle, run, parse, checkPage };

/* ----------------------------------------------------- arriving at a link ---
 * Collapsing content is only an improvement if a link still opens what it names.
 * Plan section 8 requires a stable id on every section and claim so a discussion
 * comment can address exactly one of them, and a closed disclosure with the
 * right id in the address is worse than no disclosure at all: the reader sees a
 * heading and nothing else and has no reason to think anything is missing.
 *
 * Two ways it broke while this was being built, and both are checked here. A
 * panel is a child of the section whose id is cited, so walking up from the
 * target never reached it. And the cards are built asynchronously, so a hash
 * naming one was resolved before it existed.
 */

async function checkArrival(file, anchors) {
  const name = path.basename(file);
  for (const anchor of anchors) {
    const win = makeWindow(fs.readFileSync(file, "utf8"), name);
    win.TFGHighlight = { highlight: (s) => String(s) };
    win.location.hash = "#" + anchor;
    runDeclared(win);
    await settle(win);

    const el = win.document.getElementById(anchor);
    check(`${name}: #${anchor} exists`, !!el);
    if (!el) continue;
    const closed = [];
    let n = el;
    while (n && n.tagName !== "BODY") {
      if (n.tagName === "DETAILS" && !n.open) closed.push(n.className || "details");
      n = n.parentNode;
    }
    el.querySelectorAll("details.panel").forEach((d) => {
      if (!d.open) closed.push("child " + d.className);
    });
    check(`${name}: arriving at #${anchor} opens what it names`,
          closed.length === 0, JSON.stringify(closed));
  }
}

/* Every anchor another page cites, plus one card, because a card is the one
   addressable thing the markup does not contain. */
const ARRIVALS = {
  /* One section. The page was eight, and seven of them are gone: the page is
     now the grid and nothing else, because the grid is what it was for. What
     went with them is recorded in the build log, including the parts nothing
     else on the site carries. */
  "six-questions.html": ["slots"],
  /* "strips" was a section of its own and is gone: it carried the same three
     approaches and the same three answer lists that the cards in "approaches"
     already carry. "readers" became "stakeholders", because publisher,
     implementer and assessor are roles in the process rather than audiences,
     and "stakeholders" is now "paths": the detailed stakeholder mapping lives
     on each approach page, seven parties deep, and this section is about the
     one recommendation branching rather than about the parties. */
  "index.html": ["paths", "two-paths", "approaches", "satisfaction"]
};

/* ------------------------------------------------- opened from a folder ---
 * The site has to work when someone double-clicks index.html, and until
 * assets/bundle.js existed it did not: a file:// page has an opaque origin and
 * fetch() is blocked, so every data-driven block failed at once.
 *
 * This runs each page the way that browser would: protocol file:, fetch
 * rejecting on every call, and the bundle loaded first. If a page renders its
 * extracts and its diagrams with zero fetches, opening from a folder works.
 * Asserting it here is the only way it stays working, because nothing else in
 * the build exercises that path. */

async function checkOffline(file) {
  const name = path.basename(file);
  const win = makeWindow(fs.readFileSync(file, "utf8"), name);
  win.TFGHighlight = { highlight: (s) => String(s) };
  win.location.protocol = "file:";
  let fetches = 0;
  win.fetch = () => {
    fetches += 1;
    return Promise.reject(new Error("blocked, as a browser does under file://"));
  };

  runDeclared(win);
  await settle(win);

  const doc = win.document;
  check(`${name}: opened from a folder, makes no network request`,
        fetches === 0, `${fetches} fetch call(s)`);

  const errs = doc.querySelectorAll(".small.muted")
    .filter((n) => FAIL_TEXT.test(textOf(n)))
    .map((n) => textOf(n).slice(0, 60));
  check(`${name}: opened from a folder, no renderer reported a failure`,
        errs.length === 0, JSON.stringify(errs.slice(0, 3)));

  check(`${name}: opened from a folder, shows no missing-fallback banner`,
        doc.querySelectorAll('[role="alert"]').length === 0);

  const hooks = doc.querySelectorAll("[data-snippet]");
  const filled = hooks.filter((d) => d.querySelectorAll(".snippet__body").length);
  check(`${name}: opened from a folder, every extract still rendered`,
        filled.length === hooks.length, `${filled.length} of ${hooks.length}`);

  const diagrams = doc.querySelectorAll("[data-diagram]");
  const drawn = diagrams.filter((d) => d.querySelectorAll("svg").length);
  check(`${name}: opened from a folder, every diagram still rendered`,
        drawn.length === diagrams.length, `${drawn.length} of ${diagrams.length}`);

  /* The build stamp went with the footer. What made it worth checking was that
     it proved the page had reached the provenance data under file://, and the
     extract and diagram checks above already prove the same thing more
     directly. */

  /* A reader looking at the mirror is told it is a mirror. */
  check(`${name}: opened from a folder, says the content came from the fallback`,
        doc.querySelectorAll("#bundle-note").length === 1);
}

if (require.main !== module) return;

(async function main() {
  const only = process.argv[2];
  const pages = (only ? [only] : fs.readdirSync(ROOT).filter((f) => /\.html$/.test(f)))
    .map((f) => path.join(ROOT, f))
    .filter((f) => fs.existsSync(f));

  for (const p of pages) {
    /* index.html is still a placeholder from phase 1. */
    if (fs.readFileSync(p, "utf8").length < 400) continue;
    await checkPage(p);
  }
  checkCrossPageReferences(RENDERED);
  checkJoinTargets(RENDERED);
  checkExtractsAreStatusOnly(RENDERED);
  checkEncodingsComplete();

  for (const [page, anchors] of Object.entries(ARRIVALS)) {
    const file = path.join(ROOT, page);
    if (fs.existsSync(file)) await checkArrival(file, anchors);
  }

  if (fs.existsSync(path.join(ROOT, "assets", "bundle.js"))) {
    for (const p of pages) {
      if (fs.readFileSync(p, "utf8").length < 400) continue;
      await checkOffline(p);
    }
  } else {
    failures.push("assets/bundle.js is missing, so the file:// path could not "
                  + "be checked. Run python tools/bundle.py");
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log(`${pass}/${pass + failures.length} page checks passed`);
  if (failures.length) {
    console.log("\nFailures:");
    failures.forEach((f) => console.log("  - " + f));
    process.exit(1);
  }
})();
