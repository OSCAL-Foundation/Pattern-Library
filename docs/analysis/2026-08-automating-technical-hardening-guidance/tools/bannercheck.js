#!/usr/bin/env node
"use strict";

// Dependency-free regression checks for analysis-scoped progress notices.
// Run with: node tools/bannercheck.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

const analysis = path.resolve(__dirname, "..");
const docs = path.resolve(analysis, "../..");
const read = (file) => fs.readFileSync(file, "utf8");
const active = JSON.parse(read(path.join(analysis, "analysis.json")));
const key = "pattern-library-wip-dismissed:" + active.id;
const initializer = () => {
  const source = read(path.join(analysis, "assets/site.js"));
  const match = source.match(/  function initProgressBanner\(\) \{[\s\S]*?\n  \}/);
  assert.ok(match, "banner initializer exists");
  assert.match(source.replace(match[0], ""), /\binitProgressBanner\(\);/,
    "site startup calls the initializer");
  return match[0];
};

async function mount(metadata = active, storage = memoryStorage(), options = {}) {
  let onClick;
  let focused = false;
  let requests = 0;
  const close = {
    hidden: true,
    addEventListener(event, callback) {
      assert.equal(event, "click");
      onClick = callback;
    }
  };
  const banner = {
    hidden: true,
    querySelector(selector) {
      assert.equal(selector, ".wip-banner__dismiss");
      return close;
    }
  };
  const ready = vm.runInNewContext(initializer() + "\ninitProgressBanner();", {
    IS_FILE: options.file || false,
    BASE: ".",
    sessionStorage: storage,
    bundled(file) {
      assert.equal(file, "analysis.json");
      return metadata;
    },
    fetch(url, config) {
      requests += 1;
      assert.equal(url, "./analysis.json");
      assert.equal(config.cache, "no-store");
      if (options.networkError) return Promise.reject(new Error("Offline"));
      return Promise.resolve({
        ok: !options.httpError,
        json: () => options.invalidJson
          ? Promise.reject(new SyntaxError("Invalid JSON"))
          : Promise.resolve(metadata)
      });
    },
    document: {
      querySelector(selector) {
        if (selector === ".wip-banner") return options.absent ? null : banner;
        assert.equal(selector, ".site-title a");
        return { focus() { focused = true; } };
      }
    }
  });
  assert.equal(banner.hidden, true, "hidden while status is loading");
  await ready;
  return { banner, close, requests, click: () => onClick(), focused: () => focused };
}

const memoryStorage = () => {
  const values = new Map();
  return {
    getItem: (k) => values.get(k) || null,
    setItem: (k, v) => values.set(k, v)
  };
};

test("active analysis: dismissible, focus restored, persisted on reload", async () => {
  const storage = memoryStorage();
  const first = await mount(active, storage);
  assert.equal(first.banner.hidden, false);
  assert.equal(first.close.hidden, false);
  assert.equal(first.requests, 1);
  first.click();
  assert.equal(first.banner.hidden, true);
  assert.equal(first.focused(), true);
  assert.equal(storage.getItem(key), "true");
  assert.equal((await mount(active, storage)).banner.hidden, true);
  assert.equal((await mount()).banner.hidden, false);
});

for (const [label, metadata] of [
  ["concluded", { ...active, status: "concluded" }],
  ["superseded", { ...active, status: "superseded" }],
  ["unknown status", { ...active, status: "unknown" }],
  ["missing status", { ...active, status: null }],
  ["conclusion date", { ...active, concluded: "2026-09-09" }],
  ["recommendation", { ...active, recommendation: "guidance-decision" }],
  ["decision", { ...active, decision: { outcome: "adopted" } }],
  ["decision date", { ...active, decided: "2026-09-09" }],
  ["replacement analysis", { ...active, supersededBy: "another-analysis" }],
  ["missing identifier", { ...active, id: null }],
  ["empty identifier", { ...active, id: " " }],
  ["missing metadata", null],
  ["invalid metadata", []]
]) {
  test(`${label}: no notice even with other active fields`, async () => {
    const page = await mount(metadata);
    assert.equal(page.banner.hidden, true);
    assert.equal(page.close.hidden, true);
  });
}

test("no planned recommendation does not imply the analysis has concluded", async () => {
  assert.equal((await mount({ ...active, makesRecommendation: false })).banner.hidden, false);
});

for (const failure of ["networkError", "httpError", "invalidJson"]) {
  test(`${failure}: hidden instead of falling back to a stale active status`, async () => {
    const page = await mount(active, memoryStorage(), { [failure]: true });
    assert.equal(page.banner.hidden, true);
    assert.equal(page.close.hidden, true);
  });
}

test("file copies use bundled metadata without fetching", async () => {
  for (const metadata of [active, { ...active, status: "concluded" }, null]) {
    const page = await mount(metadata, memoryStorage(), { file: true });
    assert.equal(page.requests, 0);
    assert.equal(page.banner.hidden, metadata !== active);
  }
});

test("the offline bundle mirrors analysis metadata", () => {
  const context = { window: {} };
  vm.runInNewContext(read(path.join(analysis, "assets/bundle.js")), context);
  assert.deepEqual(JSON.parse(JSON.stringify(context.window.TFGBundle["analysis.json"])), active);
});

test("dismissal affects only the current analysis", async () => {
  const storage = memoryStorage();
  (await mount(active, storage)).click();
  assert.equal((await mount(active, storage)).banner.hidden, true);
  assert.equal((await mount({ ...active, id: "another-analysis" }, storage)).banner.hidden, false);
});

test("the old sitewide dismissal does not hide analysis notices", async () => {
  const storage = memoryStorage();
  storage.setItem("pattern-library-wip-dismissed", "true");
  assert.equal((await mount(active, storage)).banner.hidden, false);
});

test("blocked or absent storage does not prevent dismissal", async () => {
  for (const storage of [null, {
    getItem() { throw new Error("Storage blocked"); },
    setItem() { throw new Error("Storage blocked"); }
  }]) {
    const page = await mount(active, storage);
    assert.equal(page.banner.hidden, false);
    page.click();
    assert.equal(page.banner.hidden, true);
    assert.equal(page.focused(), true);
  }
});

test("missing banner is harmless and does not fetch status", async () => {
  assert.equal((await mount(active, null, { absent: true })).requests, 0);
});

test("compact styling hides ineligible banners without layout space", () => {
  const css = read(path.join(analysis, "assets/site.css"));
  assert.match(css, /\.wip-banner\[hidden\].*display: none/);
  assert.match(css, /background: #FFEB00; color: #12161C/);
  assert.match(css, /min-height: 2\.25rem/);
});

for (const name of ["index.html", "patterns/index.html", "analysis/index.html",
  "recommendations/index.html", "assets/site.js", "assets/site.css"]) {
  test(`${name}: no sitewide progress banner`, () => {
    assert.doesNotMatch(read(path.join(docs, name)), /wip-banner|initProgressBanner/);
  });
}

const pages = fs.readdirSync(analysis).filter((name) => name.endsWith(".html"))
  .map((name) => path.join(analysis, name));
for (const file of pages) {
  test(`${path.relative(docs, file)}: one hidden notice pending analysis status`, () => {
    const html = read(file);
    assert.equal((html.match(/class="wip-banner"/g) || []).length, 1);
    assert.match(html, /<aside class="wip-banner" aria-label="Analysis status" hidden>/);
    assert.match(html, /<span>Work in progress<\/span>/);
    assert.match(html, /<button type="button" class="wip-banner__dismiss" aria-label="Dismiss work in progress notice" hidden><span aria-hidden="true">×<\/span><\/button>/);
    assert.ok(html.indexOf('class="wip-banner"') < html.indexOf('<header class="site-header">'));
    const script = html.match(/<script src="([^"]*\/assets\/site\.js)"><\/script>/);
    assert.ok(script, "banner behavior is loaded");
    assert.ok(fs.existsSync(path.resolve(path.dirname(file), script[1])));
  });
}