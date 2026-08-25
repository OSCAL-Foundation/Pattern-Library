/* 74-slot-strip.js
 *
 * What each approach answers, as a labelled list. A component rather than a
 * file, because it renders on every approach card, in every page header and in
 * every row of the comparison matrix, and because what it says has to change
 * when data/six-questions.json changes and never otherwise.
 *
 * This file is the one implementation. assets/site.js delegates to it, so it
 * cannot drift between the two.
 *
 *     <div class="slot-strip" data-strip="catalog-first" data-size="lg"></div>
 *     <div class="slot-strip" data-strip="assessment-first" data-size="sm"></div>
 *     TFGSlotStrip.render(el, sixQuestions, {approach: "component-first", size: "sm"});
 *
 * `sixQuestions` is the parsed data/six-questions.json. Nothing here fetches: the caller
 * owns the cache, so a page with nine of these loads the file once.
 *
 * WHY THIS IS A LIST AND NOT A ROW OF BOXES
 *
 * It was eight small coloured boxes carrying a number, and it asked a reader to
 * decode two encodings at once. The tint said which question, using a six-hue
 * palette a reader had to have learned. The border and fill said which of five
 * answer states, using solid, dashed, hollow, hollow-with-a-dot and
 * hollow-with-a-dotted-fill. Neither was written down where it was used, so a
 * reader who had not memorised both saw a row of coloured squares.
 *
 * Worse than illegible, it was misleading. The three unanswered states were
 * three different geometries, which reads as three degrees of the same thing.
 * They are not degrees. They are one fact, not answered, with three different
 * reasons behind it, and one of those reasons is that the approach answers it
 * deliberately by not answering it.
 *
 * So every row now writes what it means: the question's number and name, then
 * the state in words, then the reason where there is one. The question tint
 * survives as a small chip, which is where a palette belongs: reinforcing a
 * label rather than replacing it. The geometry survives on the swatch, so
 * grayscale and print still separate the states. Neither is load-bearing any
 * more, because the words are.
 */

(function (root) {
  "use strict";

  var STATE_CLASS = {
    "filled": "is-filled",
    "partial": "is-partial",
    "empty-absent": "is-empty-absent"
  };

  /* Wording lives in data/six-questions.json so it is stated once. The fallbacks are
     for a data file written before answer_states existed. */
  var FALLBACK = {
    "filled": { label: "Answered", reason: "" },
    "partial": { label: "Partly answered", reason: "" }
  };

  function stateOf(sixQuestions, key) {
    var found = (sixQuestions.answer_states || []).filter(function (s) {
      return s.key === key;
    })[0];
    if (found) return found;
    if (FALLBACK[key]) return FALLBACK[key];
    var e = (sixQuestions.empty_states || []).filter(function (x) {
      return x.key === key;
    })[0];
    return e ? { label: e.label, reason: "", meaning: e.meaning }
             : { label: key, reason: "" };
  }

  function cellFor(sixQuestions, slotNumber, approach) {
    return sixQuestions.matrix.filter(function (c) {
      return c.slot === slotNumber && c.approach === approach;
    })[0];
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }

  /**
   * Render one approach's answers into `node`.
   *
   * @param {Element} node     the container, usually .slot-strip
   * @param {Object}  sixQuestions  parsed data/six-questions.json
   * @param {Object}  [opts]   {approach, size}. Defaults come from data-*.
   * @returns {Element} node
   */
  function render(node, sixQuestions, opts) {
    opts = opts || {};
    var approach = opts.approach || node.getAttribute("data-strip");
    var size = opts.size || node.getAttribute("data-size") || "lg";
    if (!approach) throw new Error("74-slot-strip: no approach given");

    node.textContent = "";
    node.classList.add("slot-strip", "answers");
    node.classList.remove("slot-strip--sm", "slot-strip--lg",
                          "answers--sm", "answers--lg");
    node.classList.add(size === "sm" ? "slot-strip--sm" : "slot-strip--lg");
    node.classList.add(size === "sm" ? "answers--sm" : "answers--lg");
    /* A strip whose rows link is a list of links, so it is announced as one
       rather than as a list containing links. Without data-link it stays a
       plain list, which is what the start page wants: three strips side by
       side there have no per-approach page section to point at. */
    var link = node.getAttribute("data-link");
    if (!link) node.setAttribute("role", "list");

    var name = (sixQuestions.approaches.filter(function (a) {
      return a.key === approach;
    })[0] || {}).label || approach;
    node.setAttribute("aria-label", "What " + name + " answers, question by question");

    sixQuestions.slots.forEach(function (slot) {
      var cell = cellFor(sixQuestions, slot.number, approach);
      if (!cell) return;
      var st = stateOf(sixQuestions, cell.state);

      var cls = "answers__row slot-strip__cell slot-" + slot.number +
                " " + STATE_CLASS[cell.state];
      var row;
      if (link) {
        /* 6a and 6b are two rows against one subsection, which is why the
           target is the slot's own heading id rather than the row number. */
        row = el("a", cls + " answers__row--link");
        row.setAttribute("href", "#" + link + (slot.number.charAt(0)));
      } else {
        row = el("div", cls);
        row.setAttribute("role", "listitem");
      }
      /* The evidence is the matrix cell's own note, verbatim, because that note
         is what the site stands behind for this cell. */
      row.title = "Question " + slot.number + ", " + slot.name + ". " +
                  st.label + ". " + cell.note;

      row.appendChild(el("span", "answers__n slot-strip__n", slot.number));
      row.appendChild(el("span", "answers__q slot-strip__name",
                         slot.short || slot.name));

      var state = el("span", "answers__state");
      state.appendChild(el("span", "answers__swatch"));
      state.appendChild(el("span", "answers__word", st.label));
      row.appendChild(state);

      row.appendChild(el("span", "visually-hidden",
        slot.name + ": " + st.label + ". " + cell.note));
      node.appendChild(row);
    });
    return node;
  }

  /** Render every [data-strip] on the page from one already-loaded sixQuestions. */
  function renderAll(sixQuestions, scope) {
    var nodes = (scope || document).querySelectorAll("[data-strip]");
    Array.prototype.forEach.call(nodes, function (n) { render(n, sixQuestions); });
    return nodes.length;
  }

  /** One legend, built from data/six-questions.json.
   *
   *  Two groups, because there are two axes and an answer carries a mark from
   *  each: whether the published content answers the question, and what the
   *  capability would have to rest on to answer it at all. They were two
   *  legends in two places on the page, which read as two subjects, and a
   *  reader meeting a swatch and a badge on the same answer had to find two
   *  keys to decode one cell.
   *
   *  The second group is only drawn where the page draws badges. index.html
   *  and questions.html show marks and no badges, so a mechanism vocabulary
   *  there would define a mark that never appears. */
  function renderLegend(node, sixQuestions, withMechanisms) {
    var lg = sixQuestions.legend || {};
    node.textContent = "";
    node.className = "answers-legend";
    node.setAttribute("aria-label", lg.label || "What each mark means");

    var states = (sixQuestions.answer_states || []).length
      ? sixQuestions.answer_states
      : [{ key: "filled", label: "Answered" },
         { key: "partial", label: "Partly answered" }]
          .concat((sixQuestions.empty_states || []).map(function (e) {
            return { key: e.key, label: e.label, meaning: e.meaning };
          }));

    /* Three words, and the mark beside each. The legend used to name the
       geometry too, as in "Answered. Drawn as a solid mark.", and spell out a
       reason after the state, as in "Not answered, no position stated." Both
       were describing the drawing rather than saying what the row means: a
       reader looking at the swatch beside the word can see the shape, and the
       longer form made three short labels into three sentences. The meaning
       stays on the title attribute for anyone who wants it. */
    var g1 = group(node, lg.answers_title);
    states.forEach(function (s) {
      var wrap = el("span", "answers-legend__item");
      wrap.appendChild(el("span", "answers__swatch " + STATE_CLASS[s.key]));
      var txt = el("span", "answers-legend__text");
      txt.appendChild(el("span", "answers__word", s.label));
      wrap.appendChild(txt);
      if (s.meaning) wrap.title = s.meaning;
      g1.appendChild(wrap);
    });

    /* A badge rather than a swatch, because the geometry channel is already
       carrying the answer state and a second set of shapes in the same place
       would read as one vocabulary.

       These keep their sentence where the answer states lost theirs. Answered,
       partly answered and not answered mean what they say. "Proposed" does not
       tell a reader that no tool can read the content until the schema lands,
       and that is the sentence this page turns on. */
    var mechs = sixQuestions.mechanism_states || [];
    if (withMechanisms && mechs.length) {
      var g2 = group(node, lg.mechanism_title, "mech-legend");
      mechs.forEach(function (m) {
        var wrap = el("span", "mech-legend__item");
        wrap.appendChild(el("span", "mech mech--" + m.key, m.short));
        var txt = el("span", "answers-legend__text");
        txt.appendChild(el("span", "answers__word", m.label));
        txt.appendChild(document.createTextNode(". " + m.meaning));
        wrap.appendChild(txt);
        g2.appendChild(wrap);
      });
    }
    return node;
  }

  /* A titled group, appended to the legend. Returns the element the caller puts
     items in, which is not the group: the title sits beside the items grid
     rather than spanning it, because spanning would need grid-column 1 / -1 and
     verify.py --css bans that string outright to keep a full-span child off the
     sticky rail. */
  function group(node, title, extraClass) {
    var g = el("div", "answers-legend__group"
                      + (extraClass ? " " + extraClass : ""));
    if (title) g.appendChild(el("p", "answers-legend__title", title));
    var items = el("div", "answers-legend__items");
    g.appendChild(items);
    node.appendChild(g);
    return items;
  }

  /* One row of badges for a cell, in the order the legend lists them so two
     cells are comparable at a glance. */
  function mechanismRow(sixQuestions, cell) {
    var keys = (cell || {}).mechanisms || [];
    if (!keys.length) return null;
    var order = (sixQuestions.mechanism_states || []).map(function (m) { return m.key; });
    var row = el("span", "mech-row");
    order.filter(function (k) { return keys.indexOf(k) !== -1; }).forEach(function (k) {
      var m = (sixQuestions.mechanism_states || []).filter(function (x) {
        return x.key === k;
      })[0] || { short: k, label: k };
      var b = el("span", "mech mech--" + k, m.short);
      b.title = m.label;
      row.appendChild(b);
    });
    return row;
  }

  var api = { render: render, renderAll: renderAll, renderLegend: renderLegend,
              mechanismRow: mechanismRow,
              STATE_CLASS: STATE_CLASS };

  root.TFGSlotStrip = api;
  if (typeof module === "object" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
