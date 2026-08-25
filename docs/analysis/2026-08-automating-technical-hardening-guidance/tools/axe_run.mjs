/*
 * axe_run.mjs: run axe-core over every page of the site in a headless browser.
 *
 * The pages are markup plus data: assets/site.js fills the hooks from data/ at
 * load time. So an accessibility audit has to run after the renderers have run,
 * which means a real browser and a real HTTP origin. A file:// page has an
 * opaque origin and fetch() is blocked, so this serves the site on a loopback
 * port first and drives the browser at that.
 *
 * Requires axe-core and puppeteer, which tools/verify.py installs in CI. It
 * writes a human summary to stdout and, as its last line, one JSON object
 * mapping each page to its violations, which verify.py parses.
 *
 *     npm install --no-save axe-core puppeteer
 *     node tools/axe_run.mjs
 */

import { createServer } from "node:http";
import { readFile, readdir } from "node:fs/promises";
import { extname, join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml"
};

/* The same rules tools/serve.py follows: no caching, nothing written, and a
   4xx is visible rather than silent. */
function serve() {
  return new Promise((ok) => {
    const server = createServer(async (req, res) => {
      const path = decodeURIComponent(req.url.split("?")[0]);
      const file = join(ROOT, path === "/" ? "/index.html" : path);
      if (!file.startsWith(ROOT)) { res.writeHead(403).end(); return; }
      try {
        const body = await readFile(file);
        res.writeHead(200, {
          "Content-Type": TYPES[extname(file)] || "application/octet-stream",
          "Cache-Control": "no-store"
        }).end(body);
      } catch {
        console.error(`  404 ${path}`);
        res.writeHead(404).end("not found");
      }
    });
    server.listen(0, "127.0.0.1", () => ok(server));
  });
}

const server = await serve();
const port = server.address().port;

const puppeteer = (await import("puppeteer")).default;
const axePath = join(ROOT, "node_modules", "axe-core", "axe.min.js");
const axeSource = await readFile(axePath, "utf8");

const pages = (await readdir(ROOT))
  .filter((f) => f.endsWith(".html"))
  .sort();

const browser = await puppeteer.launch({
  args: ["--no-sandbox", "--disable-setuid-sandbox"]
});

const report = {};
let total = 0;

for (const name of pages) {
  const page = await browser.newPage();
  const problems = [];
  page.on("console", (m) => {
    if (m.type() === "error") problems.push(m.text());
  });
  page.on("pageerror", (e) => problems.push(String(e)));

  await page.goto(`http://127.0.0.1:${port}/${name}`, {
    waitUntil: "networkidle0", timeout: 60000
  });

  /* Every disclosure is opened before the audit. A collapsed <details> hides
     its contents from axe, and the verbatim extracts live inside them, so
     auditing the page closed would audit about half of it. */
  await page.evaluate(() => {
    document.querySelectorAll("details").forEach((d) => { d.open = true; });
  });

  await page.evaluate(axeSource);
  const result = await page.evaluate(async () => {
    /* eslint-disable no-undef */
    return await axe.run(document, {
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
      resultTypes: ["violations"]
    });
  });

  report[name] = result.violations.map((v) => ({
    id: v.id,
    impact: v.impact,
    help: v.help,
    nodes: v.nodes.map((n) => n.target.join(" "))
  }));
  total += result.violations.length;

  const label = result.violations.length
    ? result.violations.map((v) => `${v.id}(${v.nodes.length})`).join(" ")
    : "clean";
  console.log(`  ${name.padEnd(24)} ${label}`);
  for (const p of problems) console.log(`      console error: ${p}`);

  await page.close();
}

await browser.close();
server.close();

console.log(`  ${pages.length} pages audited, ${total} violation type(s) found`);
/* Last line is the machine-readable report verify.py reads. */
console.log(JSON.stringify(report));
