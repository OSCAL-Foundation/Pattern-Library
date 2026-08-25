/* highlight.js
 *
 * A tiny, self-contained syntax highlighter for the only two languages this
 * site shows: JSON and Markdown.
 *
 * Why not Prism. The build spec called for vendoring Prism locally. Prism could
 * not be retrieved as text through the tooling available in the build session,
 * and fetching it by other means is out of scope. Rather than add a CDN
 * reference, which the spec forbids, this file replaces it. For two languages
 * and a few hundred lines of JSON per page it is a fair trade: no supply chain,
 * nothing to keep patched, and the whole thing is auditable in one sitting.
 *
 * Contract: highlight(text, language) returns an HTML string with every
 * character HTML-escaped. It never returns unescaped input.
 */

(function (global) {
  "use strict";

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function span(cls, text) {
    return '<span class="' + cls + '">' + esc(text) + "</span>";
  }

  /* The extractor marks every truncated string with this suffix. It is shown,
     never hidden, so a reader always knows the snippet was cut. */
  var TRUNC = " [truncated]";

  function jsonString(raw, isKey) {
    var inner = raw.slice(1, -1);
    var cls = isKey ? "tok-key" : "tok-str";
    var idx = inner.lastIndexOf(TRUNC);
    if (!isKey && idx !== -1 && idx === inner.length - TRUNC.length) {
      return (
        '<span class="' + cls + '">"' + esc(inner.slice(0, idx)) + "</span>" +
        span("tok-trunc", TRUNC) +
        '<span class="' + cls + '">"</span>'
      );
    }
    return span(cls, raw);
  }

  function highlightJson(src) {
    var out = "";
    var i = 0;
    var n = src.length;
    while (i < n) {
      var ch = src[i];

      if (ch === '"') {
        var j = i + 1;
        while (j < n) {
          if (src[j] === "\\") { j += 2; continue; }
          if (src[j] === '"') break;
          j++;
        }
        var raw = src.slice(i, Math.min(j + 1, n));
        var k = j + 1;
        while (k < n && /\s/.test(src[k])) k++;
        out += jsonString(raw, src[k] === ":");
        i = j + 1;
        continue;
      }

      if (/[-0-9]/.test(ch) && /[\s:,[]/.test(src[i - 1] || " ")) {
        var m = /^-?\d+(\.\d+)?([eE][+-]?\d+)?/.exec(src.slice(i));
        if (m) { out += span("tok-num", m[0]); i += m[0].length; continue; }
      }

      if (src.startsWith("true", i) || src.startsWith("false", i)) {
        var lit = src.startsWith("true", i) ? "true" : "false";
        out += span("tok-bool", lit); i += lit.length; continue;
      }
      if (src.startsWith("null", i)) { out += span("tok-null", "null"); i += 4; continue; }

      if ("{}[],:".indexOf(ch) !== -1) { out += span("tok-punct", ch); i++; continue; }

      out += esc(ch);
      i++;
    }
    return out;
  }

  function highlightMarkdown(src) {
    var lines = src.split("\n");
    var inFence = false;
    return lines
      .map(function (line) {
        if (/^\s*```/.test(line)) { inFence = !inFence; return span("tok-md-code", line); }
        if (inFence) return span("tok-md-code", line);
        if (/^\s*#{1,6}\s/.test(line)) return span("tok-md-h", line);
        if (/^\s*[-*+]\s/.test(line) || /^\s*\d+\.\s/.test(line)) {
          var m = /^(\s*(?:[-*+]|\d+\.)\s)(.*)$/.exec(line);
          return span("tok-punct", m[1]) + inline(m[2]);
        }
        return inline(line);
      })
      .join("\n");
  }

  function inline(text) {
    var out = "";
    var re = /`[^`]+`/g;
    var last = 0;
    var m;
    while ((m = re.exec(text)) !== null) {
      out += esc(text.slice(last, m.index));
      out += span("tok-md-code", m[0]);
      last = m.index + m[0].length;
    }
    return out + esc(text.slice(last));
  }

  function highlight(text, language) {
    if (language === "json") return highlightJson(text);
    if (language === "markdown") return highlightMarkdown(text);
    return esc(text);
  }

  global.TFGHighlight = { highlight: highlight };
})(window);
