/* Renders the analysis and recommendation indexes from their registry files.
   Adding an entry means appending to the JSON; no page is edited.

   Everything is built with createElement and textContent rather than markup
   strings. The registries are repository-controlled, but a renderer that
   interpolates into innerHTML is one careless field away from injecting, and
   there is no reason to write it that way. */

(function () {
  "use strict";

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function statusClass(status) {
    return "status status--" + String(status || "unknown").replace(/[^a-z-]/gi, "");
  }

  function card(entry, hrefBase) {
    var li = el("li", "card");

    var h3 = el("h3");
    var a = el("a", null, entry.title || entry.id);
    a.href = hrefBase + entry.id + "/";
    h3.appendChild(a);
    li.appendChild(h3);

    if (entry.question) li.appendChild(el("p", null, entry.question));
    else if (entry.summary) li.appendChild(el("p", null, entry.summary));

    var meta = el("div", "card__meta");
    meta.appendChild(el("span", statusClass(entry.status), entry.status));
    if (entry.opened) meta.appendChild(el("span", null, "opened " + entry.opened));
    if (entry.concluded) meta.appendChild(el("span", null, "concluded " + entry.concluded));
    if (entry.decided) meta.appendChild(el("span", null, "decided " + entry.decided));
    if (entry.approaches && entry.approaches.length) {
      meta.appendChild(el("span", "card__count",
        entry.approaches.length + " approaches compared"));
    }
    li.appendChild(meta);

    return li;
  }

  function render(mount, entries, hrefBase) {
    var list = el("ul", "cards");
    entries.forEach(function (entry) { list.appendChild(card(entry, hrefBase)); });
    mount.replaceChildren(list);
  }

  function failure(mount, detail) {
    var box = el("div", "empty");
    box.appendChild(el("p", null,
      "This index could not read its registry, so nothing below is the list."));
    box.appendChild(el("p", null, detail));
    mount.replaceChildren(box);
  }

  document.querySelectorAll("[data-registry]").forEach(function (mount) {
    var url = mount.getAttribute("data-registry");
    var hrefBase = mount.getAttribute("data-href-base") || "./";
    var emptyId = mount.getAttribute("data-empty");

    fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error(r.status + " " + r.statusText);
        return r.json();
      })
      .then(function (entries) {
        if (!Array.isArray(entries)) throw new Error("registry is not an array");
        if (!entries.length) {
          // The empty state is written into the page rather than built here,
          // so an area with nothing in it still says something without script.
          var empty = emptyId && document.getElementById(emptyId);
          if (empty) empty.hidden = false;
          mount.replaceChildren();
          return;
        }
        render(mount, entries, hrefBase);
      })
      .catch(function (err) {
        // A page opened from a folder gets an opaque origin and fetch is
        // blocked, which is the usual reason to land here.
        failure(mount, location.protocol === "file:"
          ? "The page was opened from a folder rather than served, so the "
            + "browser blocked the read. Serve the directory over HTTP."
          : String(err.message || err));
      });
  });
})();
