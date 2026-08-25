#!/usr/bin/env python3
"""
diagrams.py: emit every SVG in assets/diagrams/ from data/.

Why a generator rather than eighteen hand-authored files.

  1. Plan section 6 forbids hand-typing anything that came out of a corpus. The
     join diagrams print literal identifier strings; typed, they can drift from
     the files. Here every literal is read from data/snippets/ at generation
     time, and every field name printed on a node is asserted to exist in the
     snippet it claims to come from. A wrong field name is a build failure, not
     a reader's problem.

  2. Plan section 3 rule 5 requires equal budget "enforced by construction".
     The three-approach families are emitted from one function each, iterating
     over one list of three. Giving one approach an extra node or an extra join
     would take deliberate effort and would show up in the verifier's counts.

Every emitted file:
    has a viewBox and no width or height, so it scales to its container
    opens with <title> then <desc>, written for someone who cannot see it
    names colour only as var(--token), never as a literal
    sets no text below MIN_FS user units
    carries its own legend
    survives grayscale, because shape and position carry the meaning

Usage:
    python tools/diagrams.py                 write into assets/diagrams/
    python tools/diagrams.py --out DIR       write elsewhere, for verification
"""

from __future__ import annotations

import argparse
import json
import os

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.dirname(TOOLS_DIR)
DATA = os.path.join(SITE_ROOT, "data")
OUT_DEFAULT = os.path.join(SITE_ROOT, "assets", "diagrams")

W = 960        # authoring width for every diagram. See .diagram in site.css.
MIN_FS = 16    # smallest text anywhere, in user units. 960 * 12/16 = 720px.


# --------------------------------------------------------------------------- #
# 1. data                                                                      #
# --------------------------------------------------------------------------- #

def _load(rel: str):
    with open(os.path.join(DATA, rel), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _snip(sid: str):
    return json.loads(_load(f"snippets/{sid}.json")["content"])


def _ptr(sid: str) -> str:
    return _load(f"snippets/{sid}.json")["pointer"]


def F(container, name: str, where: str) -> str:
    """Return a field name only if it really occurs in the source.

    This is the guard that makes 'real field names, verbatim from the files'
    checkable instead of asserted. Every field name printed on any node passes
    through here, and generation stops if one does not exist.
    """
    pool: set[str] = set()
    if isinstance(container, dict):
        pool |= set(container)
    elif isinstance(container, list):
        for it in container:
            if isinstance(it, dict):
                pool |= set(it)
                if isinstance(it.get("name"), str):
                    pool.add(it["name"])
            elif isinstance(it, str):
                pool.add(it)
    #  Check the whole name first: IBM writes a key that literally contains a
    #  slash, "assessment-asset/component-uuid", so splitting on the separator
    #  before looking would reject a field that is really there.
    if name in pool:
        return name
    base = name.split("/")[0].split("[")[0]
    if base not in pool:
        raise AssertionError(
            f"field {base!r} (from {name!r}) is not present in {where}. "
            f"Present: {sorted(pool)}")
    return name


class Corpus:
    """Every literal any diagram prints, resolved once, from data/ only."""

    def __init__(self) -> None:
        self.six_questions = _load("six-questions.json")
        self.views = _load("views.json")
        self.statsdoc = _load("corpus-stats.json")
        self.scenario = _load("scenario.json")
        self.quotes = {q["id"]: q for q in _load("quotes.json")["quotes"]}
        self.mapping_item = _load("schema-evidence/mapping-item.json")
        self.observation = _load("schema-evidence/observation.json")
        self.finding = _load("schema-evidence/finding.json")
        self.finding_target = _load("schema-evidence/finding-target.json")

        # ---- catalog-first ------------------------------------------------
        ct = _snip("aws-acm2-control")
        self.aws_ptr = _ptr("aws-acm2-control")
        self.aws_control_id = ct[F(ct, "id", "aws-acm2-control")]
        F(ct, "parts", "aws-acm2-control")
        am = [p for p in ct["parts"] if p["name"] == "assessment-method"][0]
        self.aws_part_name = am["name"]
        self.aws_tci_prop = am["props"][0]["name"]
        self.aws_tci = am["props"][0]["value"]

        comp = _snip("aws-acm-rsa-check-component")
        self.aws_comp_ptr = _ptr("aws-acm-rsa-check-component")
        self.aws_comp_title = comp[F(comp, "title", "aws-acm-rsa-check-component")]
        self.aws_comp_type = comp[F(comp, "type", "aws-acm-rsa-check-component")]
        self.aws_config_rule = [p for p in comp["props"]
                                if p["name"] == "ConfigRuleId"][0]["value"]
        ci = comp[F(comp, "control-implementations", "aws-acm-rsa-check-component")][0]
        self.aws_source_field = F(ci, "source", "aws control-implementation")
        self.aws_source = ci["source"]
        ir = ci[F(ci, "implemented-requirements", "aws control-implementation")][0]
        self.aws_ir_control_id = ir[F(ir, "control-id", "aws implemented-requirement")]
        self.aws_ir_desc = ir["description"]

        bm = _snip("aws-acm-backmatter-source")
        res = [r for r in bm["resources"] if "#" + r["uuid"] == self.aws_source][0]
        self.aws_res_uuid = res["uuid"]
        self.aws_res_title = res["title"]
        self.aws_res_href = res["rlinks"][0]["href"]

        # ---- component-first -----------------------------------------------
        val = _snip("ibm-validation-ansible")["component-definition"]["components"][0]
        self.ibm_val_uuid = val[F(val, "uuid", "ibm-validation-ansible")]
        self.ibm_val_type = val[F(val, "type", "ibm-validation-ansible")]
        self.ibm_val_title = val["title"]
        F(val, "checks", "ibm-validation-ansible")
        chk = [c for c in val["checks"]
               if c["rule-id"].endswith("hyperprotect_key_configured")][0]
        self.ibm_check_id = chk[F(chk, "id", "ibm check")]
        self.ibm_check_rule_field = F(chk, "rule-id", "ibm check")
        self.ibm_check_rule_id = chk["rule-id"]
        self.ibm_check_target_field = F(chk, "target-component-uuid", "ibm check")
        self.ibm_check_target = chk["target-component-uuid"]

        cos = _snip("ibm-cos-component")
        self.ibm_cos_ptr = _ptr("ibm-cos-component")
        self.ibm_cos_uuid = cos[F(cos, "uuid", "ibm-cos-component")]
        self.ibm_cos_type = cos[F(cos, "type", "ibm-cos-component")]
        self.ibm_cos_title = cos["title"]
        F(cos, "rules", "ibm-cos-component")
        rule = [r for r in cos["rules"] if r["id"] == self.ibm_check_rule_id][0]
        self.ibm_rule_id_field = F(rule, "id", "ibm rule")
        self.ibm_rule_id = rule["id"]
        self.ibm_rule_params_field = F(cos["rules"][0], "params", "ibm rule")
        cim = cos[F(cos, "control-implementations", "ibm-cos-component")][0]
        self.ibm_cim_source = F(cim, "source", "ibm control-implementation")
        ibm_ir = [x for x in cim["implemented-requirements"]
                  if any(r["rule-id"] == self.ibm_rule_id
                         for r in x.get("implementing-rules", []))][0]
        self.ibm_ir_control_id = ibm_ir[F(ibm_ir, "control-id", "ibm ir")]
        self.ibm_implementing_field = F(ibm_ir, "implementing-rules", "ibm ir")

        obs = _snip("ibm-ar-observation")
        self.ibm_obs_ptr = _ptr("ibm-ar-observation")
        self.ibm_obs_check_field = F(obs, "assessment-check-id", "ibm-ar-observation")
        self.ibm_obs_check_id = obs["assessment-check-id"]
        self.ibm_obs_result_field = F(obs, "result", "ibm-ar-observation")
        self.ibm_obs_result = obs["result"]
        self.ibm_obs_subjects_field = F(obs, "subjects", "ibm-ar-observation")
        self.ibm_obs_subject_type = obs["subjects"][0]["type"]
        self.ibm_obs_asset_field = F(obs, "assessment-asset/component-uuid",
                                     "ibm-ar-observation")
        self.ibm_obs_asset = obs["assessment-asset/component-uuid"]

        ibm_ap = _snip("ibm-ap-activity")
        self.ibm_ap_ptr = _ptr("ibm-ap-activity")
        acts = ibm_ap[0]["activities"]
        self.ibm_ap_asset_field = F(acts[0], "assessment-asset-uuid",
                                    "ibm-ap-activity")
        self.ibm_ap_checkids_field = F(acts[0], "check-ids", "ibm-ap-activity")
        #  The observation names a check id and an assessment asset. Resolve the
        #  pair against the plan rather than assuming which validation component
        #  it belongs to: the corpus has two, and the observation's asset is not
        #  the ANSIBLE one shown in the first panel.
        self.ibm_ap_match = [a for a in acts
                             if a["assessment-asset-uuid"] == self.ibm_obs_asset
                             and self.ibm_obs_check_id in a["check-ids"]]
        if len(self.ibm_ap_match) != 1:
            raise AssertionError(
                f"the observation's check id {self.ibm_obs_check_id!r} and asset "
                f"{self.ibm_obs_asset!r} resolve to "
                f"{len(self.ibm_ap_match)} plan activities, expected exactly one")
        self.ibm_ap_activity = self.ibm_ap_match[0]

        # ---- assessment-first -----------------------------------------------
        act = _snip("ez-stig-activity-v259312")
        self.ez_act_ptr = _ptr("ez-stig-activity-v259312")
        self.ez_activity_uuid = act[F(act, "uuid", "ez-stig-activity")]
        self.ez_group_field = F(act["props"], "stig-group-id",
                                "ez-stig-activity props")
        self.ez_group_id = [p for p in act["props"]
                            if p["name"] == "stig-group-id"][0]["value"]
        self.ez_method_field = F(act["props"], "method", "ez-stig-activity props")
        self.ez_activity_method = [p for p in act["props"]
                                   if p["name"] == "method"][0]["value"]
        self.ez_steps_field = F(act, "steps", "ez-stig-activity")
        self.ez_steptype_field = F(act["steps"][0]["props"], "step-type",
                                   "ez-stig step props")
        self.ez_steps = [
            {"uuid": s["uuid"],
             "type": [p for p in s["props"] if p["name"] == "step-type"][0]["value"]}
            for s in act["steps"]]
        self.ez_related_field = F(act, "related-controls", "ez-stig-activity")
        self.ez_related_control = (act["related-controls"]["control-selections"][0]
                                   ["include-controls"][0]["control-id"])

        ctxprops = _snip("ez-cisa-context-activity")
        self.ez_context_field = F(ctxprops, "context", "ez-cisa-context-activity")
        self.ez_context_raw = [p for p in ctxprops
                               if p["name"] == "context"][0]["value"]
        self.ez_context_uuid = json.loads(self.ez_context_raw)["component-uuid"]

        assets = _snip("ez-cisa-assessment-assets")
        self.ez_assets_ptr = _ptr("ez-cisa-assessment-assets")
        acomp = [c for c in assets["components"]
                 if c["uuid"] == self.ez_context_uuid][0]
        self.ez_asset_uuid = acomp["uuid"]
        self.ez_asset_title = acomp["title"]
        self.ez_asset_script = json.loads(
            [p for p in acomp["props"]
             if p["name"] == "context"][0]["value"])["script-path"]
        self.ez_platforms_field = F(assets, "assessment-platforms",
                                    "ez-cisa-assessment-assets")
        self.ez_platform_title = assets["assessment-platforms"][0]["title"]
        self.ez_uses_field = F(assets["assessment-platforms"][0], "uses-components",
                               "ez assessment-platform")

        subj = _snip("ez-subjects-includeall")[0]
        self.ez_subj_type_field = F(subj, "type", "ez-subjects-includeall")
        self.ez_subj_includeall_field = F(subj, "include-all", "ez-subjects-includeall")
        self.ez_subject_type = subj["type"]

        step = _snip("ez-cisa-context-step")
        self.ez_reviewed_field = F(step, "reviewed-controls", "ez-cisa-context-step")
        self.ez_step_statement = (step["reviewed-controls"]["control-selections"][0]
                                  ["include-controls"][0]["statement-ids"][0])

        # ---- schema ----------------------------------------------------------
        mi = self.mapping_item["fragment"]
        self.mapping_type_enum = next(b["enum"] for b in mi["properties"]["type"]["allOf"]
                                      if "enum" in b)
        self.mapping_required = mi["required"]
        self.obs_required = self.observation["fragment"]["required"]
        self.finding_required = self.finding["fragment"]["required"]
        ftp = self.finding_target["fragment"]["properties"]
        self.ft_type_enum = next(b["enum"] for b in ftp["type"]["allOf"] if "enum" in b)
        st = ftp["status"]["properties"]["state"]
        self.ft_state_enum = next((b["enum"] for b in st.get("allOf", []) if "enum" in b),
                                  st.get("enum"))

    # ---- convenience -------------------------------------------------------
    def stat(self, key: str) -> int:
        return {s["key"]: s["value"] for s in self.statsdoc["stats"]}[key]

    def cited(self, key: str):
        return self.statsdoc["cited_from_position_paper"][key]

    def cell(self, slot: str, approach: str) -> dict:
        return [c for c in self.six_questions["matrix"]
                if c["slot"] == slot and c["approach"] == approach][0]

    def slot(self, number: str) -> dict:
        return [s for s in self.six_questions["slots"] if s["number"] == number][0]

    def approach(self, key: str) -> dict:
        return [a for a in self.six_questions["approaches"] if a["key"] == key][0]

    def view(self, key: str) -> dict:
        return [v for v in self.views["views"] if v["key"] == key][0]

    def quote(self, qid: str) -> dict:
        return self.quotes[qid]


# --------------------------------------------------------------------------- #
# 2. svg primitives                                                            #
# --------------------------------------------------------------------------- #

#  The pre-read's option-letter order: A, B, C. Every three-approach loop uses
#  this list and only this list, so ordering can never become a choice made per
#  diagram.
#
#  The colour token each approach carries did not move with the order. A hue that
#  changed hands would invalidate every published figure and every association a
#  reader has already formed, for no gain: the three hues are equal-lightness and
#  carry no valence by design, so which one an approach has means nothing. The
#  assignment is recorded in site.css as what it is, a fixed mapping made once.
APPROACHES = [
    ("catalog-first",    "Catalog-first",    "A", "catalog",    "square"),
    ("component-first",  "Component-first",  "B", "component",  "triangle"),
    ("assessment-first", "Assessment-first", "C", "assessment", "circle"),
]

STATE_GEOM = {
    "filled": "sl-filled",
    "partial": "sl-partial",
    "empty-by-design": "sl-empty-design",
    "empty-not-asserted": "sl-empty-notasserted",
    "empty-absent": "sl-empty-absent",
}
STATE_WORD = {
    "filled": "filled",
    "partial": "partly filled",
    "empty-by-design": "by design",
    "empty-not-asserted": "not asserted",
    "empty-absent": "absent",
}


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def tw(text: str, kind: str = "mono", size: int = 16) -> float:
    """Rough advance width. Used to size label plates and to catch overflow."""
    return len(text) * size * {"mono": 0.60, "sans": 0.50, "sansb": 0.535}[kind]


def wrap(text: str, n: int) -> list[str]:
    out, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > n:
            out.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        out.append(cur)
    return out


def txt(x, y, s, cls="s", anchor="start") -> str:
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x}" y="{y}" class="{cls}"{a}>{esc(s)}</text>'


def rect(x, y, w, h, cls, rx=8) -> str:
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'class="{cls}"/>')


def path(d, cls, marker=None) -> str:
    m = f' marker-end="url(#{marker})"' if marker else ""
    return f'<path d="{d}" class="{cls}"{m}/>'


def plate(x, y, s, cls="m", anchor="middle", kind="mono", size=16, pad=6) -> str:
    """A label with an opaque backing, so it stays legible where it crosses a line."""
    w = tw(s, kind, size) + pad * 2
    rx = {"middle": x - w / 2, "start": x - pad, "end": x - w + pad}[anchor]
    return (rect(round(rx, 1), y - size + 2, round(w, 1), size + 6, "plate", 3)
            + txt(x, y, s, cls, anchor))


def hexagon(x, y, w, h, cls) -> str:
    """The shape vocabulary's control."""
    k = round(h / 2, 1)
    return (f'<path d="M{x + k},{y} H{x + w - k} L{x + w},{y + k} '
            f'L{x + w - k},{y + h} H{x + k} L{x},{y + k} z" class="{cls}"/>')


def socket(x, y, w, h, cls="hollow") -> str:
    """An unanswered question drawn as a receptacle: hollow, with two seating tabs."""
    ty = round(h * 0.28, 1)
    tb = round(h * 0.72, 1)
    return (rect(x, y, w, h, cls, 8)
            + f'<path d="M{x},{y + ty} h18 V{y + tb} H{x}" class="{cls}"/>'
            + f'<path d="M{x + w},{y + ty} h-18 V{y + tb} H{x + w}" class="{cls}"/>')


def cut(x, y, angle=0) -> str:
    """The 'not available' mark: two short parallel strokes across a route.

    Deliberately not a dash pattern, because dashed already means 'partly
    filled' in the shape vocabulary and must not acquire a second sense.
    """
    return (f'<g transform="translate({x},{y}) rotate({angle})">'
            f'<path d="M-4,-9 L-4,9 M4,-9 L4,9" class="cutmark"/></g>')


def marker_defs(did: str) -> str:
    out = []
    for name, cls in (("ref", "mk-ref"), ("join", "mk-join"), ("weak", "mk-weak")):
        out.append(
            f'<marker id="{did}-{name}" viewBox="0 0 10 10" refX="9.5" refY="5" '
            f'markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
            f'<path d="M0.5,0.8 L9.5,5 L0.5,9.2 z" class="{cls}"/></marker>')
    return "".join(out)


BASE_STYLE = """
  #{did} text {{ font-family: var(--font-sans); fill: var(--text); }}
  #{did} .h {{ font-size: 20px; font-weight: 650; }}
  #{did} .n {{ font-size: 17px; font-weight: 620; }}
  #{did} .s {{ font-size: 16px; }}
  #{did} .m {{ font-size: 16px; font-family: var(--font-mono); }}
  #{did} .mu {{ fill: var(--text-muted); }}
  #{did} .fa {{ fill: var(--text-faint); }}
  #{did} .tl {{ font-size: 16px; font-family: var(--font-mono); }}
  #{did} .tk {{ font-size: 16px; fill: var(--text-muted);
                font-style: italic; }}
  #{did} .band {{ fill: var(--bg-subtle); stroke: none; }}
  #{did} .plate {{ fill: var(--bg); stroke: none; }}
  #{did} .model {{ fill: var(--bg); stroke: var(--border-strong); stroke-width: 1.6; }}
  #{did} .box {{ fill: var(--bg-subtle); stroke: var(--border-strong); stroke-width: 1.6; }}
  #{did} .hollow {{ fill: none; stroke: var(--empty-line); stroke-width: 1.8; }}
  #{did} .ref {{ fill: none; stroke: var(--text); stroke-width: 1.8; }}
  #{did} .join {{ fill: none; stroke: var(--text-muted); stroke-width: 1.6; }}
  #{did} .weak {{ fill: none; stroke: var(--text-faint); stroke-width: 1.6;
                  stroke-dasharray: 2 4; }}
  #{did} .contain {{ fill: none; stroke: var(--border-strong); stroke-width: 1.4; }}
  #{did} .mk-ref {{ fill: var(--text); stroke: none; }}
  #{did} .mk-join {{ fill: var(--text-muted); stroke: none; }}
  #{did} .mk-weak {{ fill: var(--text-faint); stroke: none; }}
  #{did} .rule {{ stroke: var(--border); stroke-width: 1; fill: none; }}
  #{did} .key {{ fill: none; stroke: var(--text); stroke-width: 1.6; }}
  #{did} .cutmark {{ stroke: var(--text); stroke-width: 2.4; fill: none; }}
  #{did} .rt-l {{ fill: none; stroke: var(--text-muted); stroke-width: 1.6; }}
  #{did} .rt-f {{ fill: var(--text-muted); stroke: none; }}
  #{did} .mi {{ stroke: var(--mi-ink); color: var(--mi-ink); }}
  #{did} .mi__soft {{ stroke: var(--mi-soft); }}
  #{did} .mi__knock {{ fill: var(--mi-chip); stroke: var(--mi-soft); }}
  #{did} .mi--control {{ --mi-ink: var(--layer-control-ink);
                         --mi-soft: var(--layer-control-soft);
                         --mi-chip: var(--layer-control-bg); }}
  #{did} .mi--impl {{ --mi-ink: var(--layer-impl-ink);
                      --mi-soft: var(--layer-impl-soft);
                      --mi-chip: var(--layer-impl-bg); }}
  #{did} .mi--assess {{ --mi-ink: var(--layer-assess-ink);
                        --mi-soft: var(--layer-assess-soft);
                        --mi-chip: var(--layer-assess-bg); }}
"""

SLOT_STYLE = "".join(
    f"""
  #{{did}} .sl{n} {{{{ --sbg: var(--slot-{n}-bg); --sfg: var(--slot-{n}-fg);
                      --sbd: var(--slot-{n}-border); }}}}"""
    for n in ("1", "2", "3", "4", "5", "6", "6a", "6b")
) + """
  #{did} .sl-filled {{ fill: var(--sbg); stroke: var(--sbd); stroke-width: 2.2; }}
  #{did} .sl-partial {{ fill: var(--sbg); stroke: var(--sbd); stroke-width: 2.2;
                        stroke-dasharray: 7 5; }}
  #{did} .sl-empty-design {{ fill: none; stroke: var(--empty-line); stroke-width: 1.8; }}
  #{did} .sl-empty-notasserted {{ fill: none; stroke: var(--empty-line);
                                  stroke-width: 1.8; }}
  #{did} .sl-empty-absent {{ fill: url(#{did}-dots); stroke: var(--empty-line);
                             stroke-width: 1.8; }}
  #{did} .chip {{ fill: var(--sbg); stroke: var(--sbd); stroke-width: 1.4; }}
  #{did} .chipt {{ font-size: 16px; font-weight: 700; fill: var(--sfg); }}
  #{did} .chip-e {{ fill: none; stroke: var(--empty-line); stroke-width: 1.4; }}
  #{did} .chipt-e {{ font-size: 16px; font-weight: 700; fill: var(--text-faint); }}
  #{did} .openmark {{ fill: none; stroke: var(--empty-dot); stroke-width: 1.8; }}
  #{did} .dotfill {{ fill: var(--empty-absent-fill); }}
"""

APPROACH_STYLE = "".join(
    f"""
  #{{did}} .ap-{short} {{{{ --ac: var(--approach-{short}); }}}}"""
    for _k, _l, _o, short, _s in APPROACHES
) + """
  #{did} .ring {{ fill: none; stroke: var(--ac); stroke-width: 3; }}
  #{did} .ringmark {{ fill: var(--ac); stroke: none; }}
  #{did} .ringlab {{ font-size: 16px; font-weight: 620; fill: var(--ac); }}
  #{did} .apline {{ fill: none; stroke: var(--ac); stroke-width: 3.4; }}
  #{did} .apline-off {{ fill: none; stroke: var(--ac); stroke-width: 3.4;
                        opacity: 0.45; }}
"""


def svg(did: str, height: int, title: str, desc: str, body: str,
        slots: bool = False, approaches: bool = False) -> str:
    style = BASE_STYLE.format(did=did)
    if slots:
        style += SLOT_STYLE.format(did=did)
    if approaches:
        style += APPROACH_STYLE.format(did=did)
    defs = marker_defs(did)
    if slots:
        defs += (f'<pattern id="{did}-dots" width="5" height="5" '
                 f'patternUnits="userSpaceOnUse">'
                 f'<circle cx="1.2" cy="1.2" r="1.2" class="dotfill"/></pattern>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {W} {height}" id="{did}" class="tfg-diagram" '
        f'role="img" aria-labelledby="{did}-t {did}-d" '
        'preserveAspectRatio="xMidYMid meet">\n'
        f'  <title id="{did}-t">{esc(" ".join(title.split()))}</title>\n'
        f'  <desc id="{did}-d">{esc(" ".join(desc.split()))}</desc>\n'
        f'  <style>{style}  </style>\n'
        f'  <defs>{defs}</defs>\n'
        f'{body}\n'
        '</svg>\n'
    )


# --------------------------------------------------------------------------- #
# 3. shared components                                                         #
# --------------------------------------------------------------------------- #

# Legend glyphs. Each is a template taking {gx} and {gy}, and DID where a
# marker is needed. The glyph box is 34 wide, centred on the text baseline.
G_MODEL = ('<rect x="{gx}" y="{gy}" width="34" height="20" rx="6" class="model" '
           'transform="translate(0,-14)"/>')
G_BOX = ('<rect x="{gx}" y="{gy}" width="34" height="20" rx="6" class="box" '
         'transform="translate(0,-14)"/>')
G_HEX = ('<g transform="translate({gx},{gy})">'
         '<path d="M10,-14 H24 L34,-4 L24,6 H10 L0,-4 z" class="model"/></g>')
G_REF = '<path d="M{gx},{gy} h28" class="ref" marker-end="url(#DID-ref)"/>'
G_JOIN = '<path d="M{gx},{gy} h28" class="join" marker-end="url(#DID-join)"/>'
G_WEAK = '<path d="M{gx},{gy} h28" class="weak" marker-end="url(#DID-weak)"/>'
G_CONTAIN = ('<path d="M{gx},{gy} v9 h30" class="contain" '
             'transform="translate(0,-9)"/>')
G_KEY = ('<rect x="{gx}" y="{gy}" width="34" height="20" rx="4" class="key" '
         'transform="translate(0,-14)"/>')
G_SOCKET = ('<g transform="translate({gx},{gy})">'
            '<rect x="0" y="-14" width="34" height="20" rx="5" class="hollow"/>'
            '<path d="M0,-9 h6 V1 H0" class="hollow"/>'
            '<path d="M34,-9 h-6 V1 H34" class="hollow"/></g>')
G_CUT = ('<g transform="translate({gx},{gy})">'
         '<path d="M0,0 h28" class="join"/>'
         '<path d="M10,-8 V8 M18,-8 V8" class="cutmark"/></g>')


def g_slot(n: str, state: str) -> str:
    extra = ""
    if state == "empty-not-asserted":
        extra = ('<circle cx="27" cy="-9" r="3.5" class="openmark" '
                 'transform="translate({gx},{gy})"/>')
    return (f'<g class="sl{n}"><rect x="{{gx}}" y="{{gy}}" width="34" height="20" '
            f'rx="4" class="{STATE_GEOM[state]}" transform="translate(0,-14)"/>'
            f'{extra}</g>')


def g_ring(short: str, shape: str) -> str:
    mark = {"circle": '<circle cx="0" cy="0" r="6" class="ringmark"/>',
            "square": '<rect x="-6" y="-6" width="12" height="12" class="ringmark"/>',
            "triangle": '<path d="M0,-6.5 L6.5,5 L-6.5,5 z" class="ringmark"/>'}[shape]
    return (f'<g class="ap-{short}">'
            f'<rect x="{{gx}}" y="{{gy}}" width="34" height="20" rx="6" class="ring" '
            f'transform="translate(0,-14)"/>'
            f'<g transform="translate({{gx}},{{gy}})">'
            f'<g transform="translate(0,-14)">{mark}</g></g></g>')


#  A legend row is 456 units wide, of which the glyph takes 46. Text at 16px
#  sans averages 8.3 units a character, so 46 characters is the widest line that
#  cannot collide with the next column. LI() wraps to that width and legend()
#  refuses anything wider, so an over-long legend line is a build failure rather
#  than something a reader discovers.
LEG_MAX = 46


def LI(glyph: str, text: str):
    """One legend entry, wrapped. Returns a list of (glyph, line) rows."""
    lines = wrap(text, LEG_MAX)
    return [(glyph if i == 0 else "", ln) for i, ln in enumerate(lines)]


def _legend_split(items, cols: int) -> int:
    """Rows in the first column.

    Column-major, so a wrapped entry keeps its continuation lines directly
    under its own first line. The split is nudged forward until it lands on an
    entry's first row, so a wrapped entry is never cut in half across the
    column boundary. legend() and legend_h() both call this, which is what
    keeps the reserved height and the drawn height the same number.
    """
    per = (len(items) + cols - 1) // cols
    while per < len(items) and not items[per][0]:
        per += 1
    return per


def legend(did: str, x: int, y: int, items, width: int = W - 48, cols: int = 2) -> str:
    """items: (glyph or "", text). Laid out in `cols` columns of equal width."""
    out = ['<g class="legend">',
           f'<path d="M{x},{y} H{x + width}" class="rule"/>',
           txt(x, y + 26, "Legend", "n")]
    colw = width // cols
    per = _legend_split(items, cols)
    for i, (glyph, text) in enumerate(items):
        if len(text) > LEG_MAX:
            raise AssertionError(
                f"{did}: legend line is {len(text)} characters, over {LEG_MAX}. "
                f"Wrap it with LI(). Line: {text!r}")
        c, r = i // per, i % per
        gx, gy = x + c * colw, y + 52 + r * 26
        if glyph:
            out.append(glyph.replace("DID", did).format(gx=gx, gy=gy))
        out.append(txt(gx + 46, gy + 5, text, "s mu"))
    out.append("</g>")
    return "\n".join(out)


def legend_h(items, cols: int = 2) -> int:
    """Height a legend occupies below its rule, so callers can size the canvas."""
    return 52 + _legend_split(items, cols) * 26 + 22


def slot_chip(x, y, number: str, state: str) -> str:
    """The numbered chip that keeps question identity off the colour channel."""
    empty = state.startswith("empty")
    w = 30 if len(number) > 1 else 24
    return (f'<g class="sl{number}">'
            + rect(x - w, y, w, 20, "chip-e" if empty else "chip", 4)
            + txt(x - w / 2, y + 15.5, number, "chipt-e" if empty else "chipt",
                  "middle")
            + "</g>")


def node(x, y, w, titles, details, slot=None, state="filled") -> tuple[str, int]:
    """A containment-tree node. Returns (svg, height).

    The question chip straddles the top edge rather than sitting inside it, so a
    long field name can never run underneath the number. Field names are the
    payload of these nodes and must not be shortened to make room for chrome.
    """
    for t in titles + details:
        if tw(t) > w - 20:
            raise AssertionError(f"node text {t!r} is {tw(t):.0f} units, "
                                 f"wider than the {w - 20} available")
    h = 14 + 19 * len(titles) + 18 * len(details) + 14
    cls = f"sl{slot} {STATE_GEOM[state]}" if slot else "model"
    out = [rect(x, y, w, h, cls, 8)]
    ty = y + 29
    for t in titles:
        out.append(txt(x + 12, ty, t, "m"))
        ty += 19
    dy = ty + 3
    for d in details:
        out.append(txt(x + 12, dy, d, "m mu"))
        dy += 18
    if slot:
        out.append(slot_chip(x + w - 10, y - 11, slot, state))
        if state == "empty-not-asserted":
            out.append(f'<circle cx="{x + w - 48}" cy="{y - 1}" r="4.5" '
                       f'class="openmark"/>')
    return "".join(out), h


def elbow(x1, y1, x2, y2, cls="contain", marker=None) -> str:
    if abs(y1 - y2) < 0.75:
        d = f"M{x1},{y1} H{x2}"
    else:
        mid = x1 + (x2 - x1) / 2
        d = f"M{x1},{y1} H{mid} V{y2} H{x2}"
    return path(d, cls, marker)


#  Each layer is a band, and its name sits inside the band above the models
#  rather than in a left gutter. A gutter wide enough for the word
#  IMPLEMENTATION would have taken a sixth of the drawing away from the models.
# --------------------------------------------------------------------------- #
# 5. diagram 7.2, the six questions                                                 #
# --------------------------------------------------------------------------- #

#  Five depth columns, because the deepest path in any of the three approaches
#  is five levels. The widths are the maximum needed by any of the three, not
#  the maximum needed by each, so the three six-questions diagrams share one grid.
#  If one approach were allowed to set its own column widths it would look
#  tidier or busier than the others, and uneven visual density reads as a
#  verdict. Column 2 is the widest because "implementations[]" and
#  "target-component-" are the longest field names in the corpora.
COLW = [149, 187, 187, 178, 149]
COL = [10]
for _w in COLW[:-1]:
    COL.append(COL[-1] + _w + 16)

#  Wording for the legend rows that stand for an answer state. The row is only
#  drawn if the data still carries the state, so retiring one retires its row
#  rather than leaving the figure explaining a mark it never makes.
STATE_LEGEND = {
    "filled": "a question this approach answers",
    "partial": "one it answers in part",
    "empty-by-design": "not applicable by design",
    "empty-not-asserted": "deliberately not answered",
    "empty-absent": "unanswered, no stated position",
}


def six_questions_legend(c: Corpus):
    live = [s["key"] for s in c.six_questions["answer_states"]]
    missing = [k for k in live if k not in STATE_LEGEND]
    if missing:
        raise SystemExit(f"no legend wording for answer state(s): {missing}")
    #  Each row is drawn on a question that actually carries the state, so the
    #  mark in the legend is one the reader can go and find in the figure.
    example = {k: next((cell["slot"] for cell in c.six_questions["matrix"]
                        if cell["state"] == k), "1") for k in live}
    return (LI(G_MODEL, "a structural assembly on the path to a question")
            + LI(G_CONTAIN, "containment: the child sits inside the parent")
            + [row for k in live
               for row in LI(g_slot(example[k], k), STATE_LEGEND[k])]
            + LI(G_WEAK, "unanswered, reached by no containment path")
            + LI("", "Every one carries its number, so colour is never the "
                     "only channel.")
            )


def _six_questions(c: Corpus, key: str, nodes, links, weak, legend_y: int):
    short = [s for k, _l, _o, s, _sh in APPROACHES if k == key][0]
    did = f"dg-72-six-questions-{short}"
    geom, drawn = {}, []
    for nid, col, y, titles, details, slot in nodes:
        state = c.cell(slot, key)["state"] if slot else "filled"
        det = [STATE_WORD[state]] if (slot and state.startswith("empty")) else list(details)
        s, h = node(COL[col], y, COLW[col], titles, det, slot, state)
        geom[nid] = (COL[col], y, COLW[col], h, COL[col] + COLW[col] / 2, y + h / 2)
        drawn.append(s)
    lines = []
    for a, b in links:
        ax, _ay, aw, _ah, _acx, acy = geom[a]
        bx, _by, _bw, _bh, _bcx, bcy = geom[b]
        lines.append(elbow(ax + aw, acy, bx, bcy, "contain"))
    for a, b in weak:
        _ax, ay, _aw, ah, acx, _acy = geom[a]
        _bx, by, _bw, _bh, bcx, _bcy = geom[b]
        #  Enter the empty node from above, not from the left. The unanswered questions
        #  sit in one row, so a left-hand approach would have to cross the boxes
        #  to its left to reach the ones further along.
        lines.append(path(f"M{acx},{ay + ah} V{by - 26} H{bcx} V{by - 9}",
                          "weak", f"{did}-weak"))
    items = six_questions_legend(c)
    body = ("\n".join(lines + drawn) + "\n"
            + legend(did, 24, legend_y, items, cols=2))
    return did, body, legend_y + legend_h(items)


def diagram_72(c: Corpus) -> dict[str, str]:
    files = {}

    # ---------------------------------------------------------- assessment
    nodes = [
        ("root", 0, 190, ["assessment-", "plan"], ["document root"], None),
        ("subj", 1, 40, ["assessment-", "subjects"],
         [c.ez_subj_type_field, c.ez_subj_includeall_field], "4"),
        ("asst", 1, 158, ["assessment-", "assets"],
         ["components", "assessment-", c.ez_platforms_field[len("assessment-"):]], "5"),
        ("locd", 1, 296, ["local-definitions"], [], None),
        ("acts", 2, 268, ["activities[]"], ["title", "props/" + c.ez_method_field], "1"),
        ("relc", 3, 196, [c.ez_related_field], ["control-id"], "2"),
        ("step", 3, 300, [c.ez_steps_field + "[]"], ["title"], None),
        ("prop", 4, 300, ["props[]"], [c.ez_steptype_field], "3"),
        ("e6a", 1, 430, ["(implementation", "claim)"], [], "6a"),
        ("e6b", 2, 430, ["(result)"], [], "6b"),
    ]
    links = [("root", "subj"), ("root", "asst"), ("root", "locd"), ("locd", "acts"),
             ("acts", "relc"), ("acts", "step"), ("step", "prop")]
    did, body, H = _six_questions(c, "assessment-first", nodes, links,
                         [("root", "e6a"), ("root", "e6b")], 546)
    files["72-six-questions-assessment.svg"] = svg(
        did, H,
        "Assessment-first (Option C): where each question is answered inside an assessment plan",
        "The containment path from the document root of an assessment plan down to the "
        "field that answers each question. assessment-plan contains assessment-subjects, "
        f"which fills question 4, the subject, through {c.ez_subj_type_field} and "
        f"{c.ez_subj_includeall_field}. It contains assessment-assets, which answers question "
        f"5, the actor, through components and {c.ez_platforms_field}. It contains "
        "local-definitions, which contains activities, which fills question 1, the rule, "
        f"and carries a {c.ez_method_field} prop. An activity contains "
        f"{c.ez_related_field}, which fills question 2, the link to a control, through control-id; "
        f"and it contains {c.ez_steps_field}, whose props fill question 3, the check, "
        f"through {c.ez_steptype_field}. Two questions are reached by no containment path from "
        f"the activity, so they are drawn hollow at the foot of the figure and linked by "
        f"a dotted line. Question 6a, the implementation claim, is answered in part: the plan "
        f"makes no claim of its own and instead names the system security plan that holds "
        f"one, through import-ssp and a back-matter resource. Question 6b, the assessment "
        f"result, is answered in a second document, an assessment result, rather than "
        f"inside the plan. "
        "",
        body, slots=True)

    # ------------------------------------------------------------- catalog
    nodes = [
        ("cat", 0, 40, ["catalog"], ["document root"], None),
        ("grp", 1, 40, ["groups[]"], ["title"], None),
        ("ctl", 2, 40, ["controls[]"], ["id"], "1"),
        ("prt", 3, 40, ["parts[]"], ["name", "props"], "3"),
        ("cdf", 0, 176, ["component-", "definition"], ["document root"], None),
        ("cmp", 1, 176, ["components[]"], ["type", "title"], None),
        ("cim", 2, 176, ["control-", "implementations[]"], [c.aws_source_field], None),
        ("imr", 3, 176, ["implemented-", "requirements[]"], ["control-id"], "6a"),
        ("e2", 0, 330, ["(control", "link)"], [], "2"),
        ("e4", 1, 330, ["(subject)"], [], "4"),
        ("e5", 2, 330, ["(runner)"], [], "5"),
        ("e6b", 3, 330, ["(result)"], [], "6b"),
    ]
    links = [("cat", "grp"), ("grp", "ctl"), ("ctl", "prt"),
             ("cdf", "cmp"), ("cmp", "cim"), ("cim", "imr")]
    did, body, H = _six_questions(c, "catalog-first", nodes, links,
                         [("cdf", "e2"), ("cdf", "e4"), ("cdf", "e5"), ("cdf", "e6b")],
                         460)
    files["72-six-questions-catalog.svg"] = svg(
        did, H,
        "Catalog-first (Option A): where each question is answered inside a catalog and a "
        "component definition",
        "Two containment paths, because this approach ships two document types. First: "
        "catalog contains groups, which contain controls, which fill question 1, the rule, "
        "through id; a control contains parts, and the part named "
        f"{c.aws_part_name} fills question 3, the check, through its name and its props. "
        "Second: component-definition contains components, which contain "
        "control-implementations, which contain implemented-requirements; that assembly "
        "fills question 6a, the implementation claim, in part, through control-id. It is "
        "partial rather than filled because a component definition asserts how a "
        "component would satisfy a control, while only a system security plan asserts "
        "that a system does, and no system security plan exists in the repository. Four "
        "questions are unanswered and are drawn hollow at the foot of the figure. Question 2, the "
        "link to a control, is deliberately not asserted: the publisher stripped the "
        "associated-control props before publication pending a decision, and said so. "
        "Question 4, the subject, and question 5, the actor, are absent with no stated position, "
        "because the repository contains only catalogs and component definitions and "
        "there is nowhere for either to be expressed. Question 6b, the assessment result, "
        "is absent for the same reason.",
        body, slots=True)

    # ----------------------------------------------------------- component
    nodes = [
        ("cdf", 0, 40, ["component-", "definition"], ["document root"], None),
        ("cmp", 1, 40, ["components[]"], ["type", "uuid"], None),
        ("rul", 2, 26, ["rules[]"], [c.ibm_rule_id_field, c.ibm_rule_params_field], "1"),
        ("cim", 2, 146, ["control-", "implementations[]"], [c.ibm_cim_source], None),
        ("imr", 3, 146, ["implemented-", "requirements[]"], ["control-id"], None),
        ("irl", 4, 146, ["implementing-", "rules[]"], [c.ibm_check_rule_field], "2"),
        ("vdf", 0, 296, ["component-", "definition"], ["validation"], None),
        ("vcm", 1, 296, ["components[]"], ["type"], "5"),
        ("chk", 2, 288, ["checks[]"],
         [c.ibm_check_rule_field, "target-component-", "uuid"], "3"),
        ("ard", 0, 440, ["assessment-", "results"], ["document root"], None),
        ("obs", 1, 440, ["observations[]"],
         [c.ibm_obs_subjects_field, "type"], "4"),
        ("res", 2, 448, [c.ibm_obs_result_field], ["proposed field"], "6b"),
        ("e6a", 3, 440, ["(implementation", "claim)"], [], "6a"),
    ]
    links = [("cdf", "cmp"), ("cmp", "rul"), ("cmp", "cim"), ("cim", "imr"),
             ("imr", "irl"), ("vdf", "vcm"), ("vcm", "chk"),
             ("ard", "obs"), ("obs", "res")]
    did, body, H = _six_questions(c, "component-first", nodes, links, [("ard", "e6a")], 570)
    files["72-six-questions-component.svg"] = svg(
        did, H,
        "Component-first (Option B): where each question is answered inside a component "
        "definition, a validation component and an assessment result",
        "Three containment paths. First: component-definition contains components, "
        f"which contain rules, which fill question 1, the rule, through "
        f"{c.ibm_rule_id_field} and {c.ibm_rule_params_field}; the same component "
        "contains control-implementations, which contain implemented-requirements, "
        f"which contain {c.ibm_implementing_field}, which fill question 2, the link to a control, "
        f"through {c.ibm_check_rule_field}. Second: a validation component definition "
        "contains components of type validation, which fill question 5, the actor, and "
        "which contain checks, which fill question 3, the check, through the pair "
        f"{c.ibm_check_rule_field} and {c.ibm_check_target_field}. Third: "
        "assessment-results contains observations, which fill question 4, the subject, in "
        f"part through {c.ibm_obs_subjects_field} and type, and which carry a proposed "
        f"{c.ibm_obs_result_field} field that fills question 6b, the assessment result, in "
        "part. Both are partial: the observation subject uuids do not resolve inside "
        "the corpus, and the assessment result contains no findings, so there is no "
        "objective status and control attribution has to be inferred. One question is "
        "empty. Question 6a, the implementation claim, is absent with no stated position: "
        "the proposal extends the system security plan, but no system security plan is "
        "shipped.",
        body, slots=True)
    return files


# --------------------------------------------------------------------------- #
# 6. diagram 7.3, the join diagrams                                            #
# --------------------------------------------------------------------------- #

#  The join boxes are as wide as the canvas allows, because the longest literal
#  in the corpora is an 85-character JSON string held in a prop value and it has
#  to be printed whole. Breaking a literal across lines to make it fit would be
#  the same failure as retyping it.
JX, JW = 24, 912
NOTE_X, NOTE_MAX = 486, 54     # 960 - 486 - 20, at 8.3 units a character


#  The runtime, drawn the same way it is drawn on the page: something arrives,
#  a machine runs, something leaves. The engine is the one thing in the chain
#  that is not a document, and giving it the shape of a document was saying it
#  was one.
#  The same icon the pages draw, in a figure.
#
#  A model is a file with a face on this site: the stakeholder mapping and the
#  six questions page both draw one icon per model, coloured by the layer it
#  belongs to. The chain figure was drawing a plain rectangle with the model
#  name inside it, so a reader moving from the page to the figure below it met
#  the same seven models twice in two vocabularies.
#
#  Emitted from data/model-icons.json, the file those pages read, so the drawing
#  cannot drift from theirs. The colour is a layer class rather than a literal,
#  exactly as it is in the stylesheet.
MODEL_ICONS = _load("model-icons.json")
ICON_LAYER = {"control": "mi--control", "implementation": "mi--impl",
              "assessment": "mi--assess"}
ICON_ATTRS = ("stroke-width", "stroke-linecap", "stroke-linejoin",
              "stroke-dasharray")


def model_icon(model: str, x: float, y: float, size: float = 21) -> str:
    """One model's icon, placed with its top left corner at x, y."""
    ic = MODEL_ICONS["icons"].get(model)
    if ic is None:
        return ""
    vx, vy, vw, _vh = (float(v) for v in ic["view_box"].split())
    k = round(size / vw, 4)
    out = [f'<g class="mi {ICON_LAYER[ic["layer"]]}" transform="translate('
           f'{round(x, 2)},{round(y, 2)}) scale({k}) '
           f'translate({-vx},{-vy})">']
    for sh in ic["shapes"]:
        at = [f'{a}="{sh[a]}"' for a in ICON_ATTRS if a in sh]
        cls = ["mi__soft"] if sh.get("soft") else []
        fill = sh.get("fill")
        if fill == "ink":
            at.append('fill="currentColor"')
        elif fill == "chip":
            cls.append("mi__knock")
        else:
            at.append('fill="none"')
        if cls:
            at.insert(0, 'class="' + " ".join(cls) + '"')
        if sh["tag"] == "path":
            out.append(f'<path d="{sh["d"]}" ' + " ".join(at) + "/>")
        else:
            geom = " ".join(f'{a}="{sh[a]}"' for a in
                            ("x", "y", "width", "height", "rx", "cx", "cy", "r")
                            if a in sh)
            out.append(f'<{sh["tag"]} {geom} ' + " ".join(at) + "/>")
    out.append("</g>")
    return "".join(out)


def runtime_mark(x, y, scale=1.0) -> str:
    return (f'<g transform="translate({x},{y}) scale({scale})" class="rtm">'
            '<path d="M0,10 H11" class="rt-l"/>'
            '<path d="M15,10 L9.6,7.2 v5.6 Z" class="rt-f"/>'
            '<rect x="16.2" y="1.8" width="12" height="16.4" rx="3.2" '
            'class="rt-l"/>'
            '<path d="M20,6.3 L25.1,10 L20,13.7 Z" class="rt-f"/>'
            '<path d="M29,10 H39.5" class="rt-l"/>'
            '<path d="M43.5,10 L38.1,7.2 v5.6 Z" class="rt-f"/></g>')


G_RUNTIME = ('<g transform="translate({gx},{gy}) scale(0.66)">'
             '<path d="M0,-9 H11" class="rt-l"/>'
             '<path d="M15,-9 L9.6,-11.8 v5.6 Z" class="rt-f"/>'
             '<rect x="16.2" y="-17.2" width="12" height="16.4" rx="3.2" '
             'class="rt-l"/>'
             '<path d="M20,-12.7 L25.1,-9 L20,-5.3 Z" class="rt-f"/>'
             '<path d="M29,-9 H39.5" class="rt-l"/>'
             '<path d="M43.5,-9 L38.1,-11.8 v5.6 Z" class="rt-f"/></g>')


def join_legend(kinds):
    """Only the ways this chain joins things, plus what the boxes are."""
    items = (LI(G_BOX, "a document, or the fragment of one that holds the field")
             + LI(G_KEY, "the value, as the six questions page encodes it"))
    if "reference" in kinds:
        items += LI(G_REF, "a reference: the schema knows it is an identifier "
                           "and it resolves")
    if "composite" in kinds:
        items += LI(G_REF, "drawn twice where the key is composite and both "
                           "halves have to match")
    if "name-match" in kinds:
        items += LI(G_WEAK, "a name match: equal by convention, and no schema "
                            "can check it")
    if "containment" in kinds:
        items += LI(G_CONTAIN, "containment: nothing resolves, the child is "
                               "inside the parent")
    if "none" in kinds:
        items += LI(G_SOCKET, "no join: there is no field on the far side")
    items += LI(G_RUNTIME,
                "the runtime, which reads OSCAL, executes, and writes OSCAL")
    items += LI("", "Every value is rule 1, data at rest, as data/pattern-"
                    "examples.json encodes it for this approach. The table above "
                    "is the same chain without the values.")
    return items


#  ---- the chain -----------------------------------------------------------
#
#  This figure used to draw two joins per approach out of whichever corpus that
#  approach's proponent had published: an ACM.2 control and a Config rule on one
#  page, a COS component and an Ansible runner on the second, a STIG activity on
#  the third. Three pages, three subjects, and a reader comparing them was
#  comparing the corpora rather than the modelling.
#
#  It draws the chain now, from data/joins.json, with the values taken from the
#  same rule the six questions page walks in all three columns. What changes
#  between the three figures is only what the reader is being asked to compare:
#  how many relationships it takes to get from the rule to the check, and what
#  each one is made of.
CH_X = 24                      # left edge
CH_BW = 372                    # box width. 24 + 372 + 168 + 372 + 24 = 960.
CH_MID = 168                   # the arrow column between the two boxes
CH_GLYPH_X = 330               # where the runtime mark sits beside a heading


def chunk(text: str, width: float, kind: str = "mono") -> list[str]:
    """Break a field path to fit, at its own separators.

    wrap() splits on spaces, and a field path has none:
    parts[assessment-method].props.TechnicalControlId came out as one line and
    ran through the side of its box and into the arrow label. This breaks after
    a dot, a bracket or a hyphen, and only cuts mid-token if a single token is
    itself too wide to fit.
    """
    def split_on(seps):
        parts, cur = [], ""
        for ch in text:
            cur += ch
            if ch in seps:
                parts.append(cur)
                cur = ""
        if cur:
            parts.append(cur)
        return parts

    #  Structural breaks first: after a closing bracket or a dot, which is where
    #  a reader's eye already divides a path. Only if a single segment still
    #  will not fit does the hyphen inside a word become a break too.
    parts = split_on("].")
    if any(tw(x, kind) > width for x in parts):
        parts = split_on("].-_/")
    out, line = [], ""
    for tok in parts:
        while tw(tok, kind) > width:
            keep = max(1, int(width / (tw("x", kind))))
            if line:
                out.append(line)
                line = ""
            out.append(tok[:keep])
            tok = tok[keep:]
        if line and tw(line + tok, kind) > width:
            out.append(line)
            line = tok
        else:
            line += tok
    if line:
        out.append(line)
    return out


def _chain_side(x, y, sd) -> tuple[str, int]:
    """One end of a relationship: the model, the field, and the value."""
    model = sd["model"]
    inner = CH_BW - 30
    lines = (chunk(sd["field"], inner) if sd["field"] != "no field"
             else ["no field"])
    vlines = chunk(sd["value"], inner - 18) if sd.get("value") else []
    where = sd.get("where")
    h = (12 + 20 + (18 if where else 0) + 19 * len(lines)
         + (6 + 22 * len(vlines) if vlines else 0) + 12)
    cls = "box" if model != "nothing" else "hollow"
    o = [rect(x, y, CH_BW, h, cls, 8)]
    if model != "nothing":
        o.append(model_icon(model, x + 13, y + 10))
        o.append(txt(x + 42, y + 26, model, "s mu"))
    else:
        o.append(txt(x + 14, y + 26, "nothing in OSCAL", "s mu"))
    ly = y + 45
    #  A qualifier used to share the model's line, right aligned, and on the one
    #  box where both were long they ran into each other. It gets its own line.
    if where:
        o.append(txt(x + 14, ly, where, "tk"))
        ly += 18
    for ln in lines:
        o.append(txt(x + 14, ly, ln, "tk" if ln == "no field" else "m"))
        ly += 19
    if vlines:
        w = round(max(tw(v) for v in vlines) + 16, 1)
        o.append(rect(x + 11, ly - 12, w, 22 * len(vlines) + 6, "key", 4))
        for i, v in enumerate(vlines):
            o.append(txt(x + 19, ly + 5 + i * 22, v, "m"))
    return "".join(o), h


def _chain_hop(did, y, n, hop, stage) -> tuple[str, int]:
    """One step of the chain: a heading, then a row for each relationship."""
    label = f'{n}. {stage[hop["from"]]["label"]} to {stage[hop["to"]]["label"]}'
    o = [txt(CH_X, y, label, "n")]
    #  The mark sits at a fixed column rather than after the words, so it lands
    #  in the same place on every step that involves the runtime and never
    #  crowds a heading that happens to be long.
    if "runtime" in (hop["from"], hop["to"]):
        o.append(runtime_mark(CH_GLYPH_X, y - 14, 0.8))
    y += 18

    for pair in hop["pairs"]:
        s1, h1 = _chain_side(CH_X, y, pair["foreign"])
        s2, h2 = _chain_side(CH_X + CH_BW + CH_MID, y, pair["primary"])
        h = max(h1, h2)
        ax, ay = CH_X + CH_BW, y + h / 2
        cls = {"reference": "ref", "composite": "ref", "name-match": "weak",
               "containment": "contain", "none": "weak"}[pair["how"]]
        mk = {"ref": f"{did}-ref", "weak": f"{did}-weak",
              "contain": f"{did}-join"}[cls]
        if pair["how"] == "containment":
            o += [s1, s2, path(f"M{ax + 22},{ay} h{CH_MID - 44}", "contain", mk)]
        elif pair["how"] == "none":
            o += [s1, s2, path(f"M{ax + 22},{ay} h{CH_MID - 78}", "weak"),
                  socket(ax + CH_MID - 50, ay - 11, 28, 22)]
        else:
            o += [s1, s2, path(f"M{ax + 22},{ay} h{CH_MID - 44}", cls, mk)]
        word = {"reference": "resolves", "composite": "half of the key",
                "name-match": "by name", "containment": "inside",
                "none": "nothing to resolve"}[pair["how"]]
        o.append(plate(ax + CH_MID / 2, ay - 12, word, "s mu", "middle",
                       kind="sans"))
        y += h + 14
    return "\n".join(o), y + 10


def diagram_73(c: Corpus) -> dict[str, str]:
    jn = _load("joins.json")
    stage = {s["key"]: s for s in jn["stages"]}
    how = {h["key"]: h for h in jn["how"]}
    files = {}

    for key, short, letter in (("catalog-first", "catalog", "A"),
                               ("component-first", "component", "B"),
                               ("assessment-first", "assessment", "C")):
        a = jn["approaches"][key]
        did = f"dg-73-join-{short}"
        y = 46
        body = []
        for n, hop in enumerate(a["hops"], 1):
            piece, y = _chain_hop(did, y, n, hop, stage)
            body.append(piece)
        kinds = {p["how"] for h in a["hops"] for p in h["pairs"]}
        items = join_legend(kinds)
        body.append(legend(did, CH_X, y, items, cols=2))

        #  The description is the figure in words, for a reader who cannot see
        #  it. It is generated from the same data, so it cannot drift.
        say = []
        for n, hop in enumerate(a["hops"], 1):
            say.append(f'Step {n}, {stage[hop["from"]]["label"].lower()} to '
                       f'{stage[hop["to"]]["label"].lower()}, is made of '
                       f'{len(hop["pairs"])} '
                       f'{"relationship" if len(hop["pairs"]) == 1 else "relationships"}. '
                       + " ".join(
                           f'{p["foreign"]["field"]} in the '
                           f'{p["foreign"]["model"]}'
                           + (f', which holds {p["foreign"]["value"]},'
                              if p["foreign"].get("value") else "")
                           + f' {how[p["how"]]["label"].lower()} to '
                           f'{p["primary"]["field"]} in the '
                           f'{p["primary"]["model"]}.'
                           for p in hop["pairs"]))
        files[f"73-join-{short}.svg"] = svg(
            did, y + legend_h(items),
            f'{key.split("-")[0].title()}-first (Option {letter}): the chain '
            f'from the rule to the claim and the result',
            f'A chain of {len(a["hops"])} steps, each drawn as one row per '
            f'relationship, with the field that holds the pointer on the left '
            f'and the field it resolves to on the right. ' + " ".join(say)
            + ' Every value is rule 1, data at rest, as the six questions page '
              'encodes it for this approach.',
            "\n".join(body))
    return files

def _readers_body(did: str) -> str:
    o = ["<!-- readers:begin -->", '<g class="three-stakeholders">']
    cx, cy, cw, ch = CENTER
    o.append(rect(cx, cy, cw, ch, "model", 10))
    #  Two lines: "one recommendation" on one line is wider than the 196-unit box
    #  at this weight and spilled out of both sides.
    o.append(txt(cx + cw / 2, cy + 46, "one", "n", "middle"))
    o.append(txt(cx + cw / 2, cy + 72, "recommendation", "n", "middle"))
    for _key, label, y, first, rest in READERS:
        o.append(txt(RX[0], y - 14, label, "s mu"))
        chain = [first] + rest
        for i, lines in enumerate(chain):
            x = RX[i]
            o.append(rect(x, y, RNW, RNH, "box", 9))
            ty = y + RNH / 2 - (len(lines) - 1) * 10
            for ln in lines:
                o.append(txt(x + RNW / 2, ty + 6, ln, "s", "middle"))
                ty += 20
            if i:
                o.append(path(f"M{RX[i - 1] + RNW},{y + RNH / 2} H{x - 3}",
                              "join", f"{did}-join"))
        o.append(path(f"M{cx + cw},{cy + ch / 2} H{RX[0] - TRUNK_GAP} "
                      f"V{y + RNH / 2} H{RX[0] - 3}", "join", f"{did}-join"))
    o += ["</g>", "<!-- readers:end -->"]
    return "\n".join(o)



#  Row spacing was 192 against a 96-unit node, so more than half the drawing was
#  air and the figure stood 922 units tall on a page where nothing else passed
#  640. Rows now sit 140 apart against an 88-unit node: the same reading order,
#  in two thirds of the height.
#
#  "a requirement or recommendation" rather than "a requirement", because most of
#  the content in question is guidance. A CIS Benchmark and a Security Technical
#  Implementation Guide both recommend; neither compels. Calling the thing a
#  requirement here would have assumed the answer to the question the site exists
#  to lay out, which is what kind of thing a rule is.
READERS = [
    ("publisher", "PUBLISHER", 56,
     ["a recommendation", "written once"],
     [["a versioned,", "tailorable,", "citable publication"]]),
    ("implementer", "IMPLEMENTER", 196,
     ["desired state"],
     [["a configuration", "engine"], ["applied state"]]),
    ("assessor", "ASSESSOR", 336,
     ["a check"],
     [["execution, or", "examination"], ["evidence"], ["a finding"]]),
]
RX = [268, 442, 616, 790]
RNW, RNH = 158, 88
CENTER = (34, 184, 196, 108)
#  The trunk is the vertical the three paths branch from. It used to sit at
#  RX[0] - 40 = 228, and the centre box's right edge is at 34 + 196 = 230, so the
#  trunk ran two units INSIDE the box and read as a line crossing it. It now sits
#  at RX[0] - 28 = 240, ten clear of the box.
TRUNK_GAP = 28
HEIGHT_75 = 452

READERS_DESC = (
    "One recommendation sits on the left. Three paths lead out of "
    "it, one for each stakeholder, and the three are drawn at the same size and "
    "weight because none is ranked above another. The publisher's path runs from a "
    "recommendation written once to a versioned, tailorable, citable "
    "publication. The implementer's path runs from "
    "desired state to a configuration engine to applied state. The assessor's path "
    "runs from a check to execution or examination to evidence to a finding. This is "
    "an organizing structure, not a thesis: all three needs are real and can be true "
    "at once, and the site's question is which questions each approach answers, for which "
    "stakeholder, and what it costs to fill the rest.")

def diagram_75(c: Corpus) -> dict[str, str]:
    """Three stakeholders, three paths.

    No legend and no note beneath. The three shapes are a box and an arrow, both
    obvious in context, and the note repeated a sentence the surrounding prose
    already carries. Everything the legend said is in the <desc>, which is what a
    screen reader gets and what a caption cannot replace.
    """
    files = {}

    def build(did, title, desc, overlay=""):
        body = _readers_body(did) + "\n" + overlay
        return svg(did, HEIGHT_75, title, desc, body, approaches=bool(overlay))

    files["75-stakeholders.svg"] = build(
        "dg-75-stakeholders",
        "One recommendation, three stakeholders, three paths",
        READERS_DESC + " No approach is marked on this drawing.")

    for key, label, letter, short, shape in APPROACHES:
        reader = c.approach(key)["serves_stakeholder_first"]
        did = f"dg-75-stakeholders-{short}"
        y = [r[2] for r in READERS if r[0] == reader][0]
        n = len([r for r in READERS if r[0] == reader][0][4]) + 1
        x2 = RX[n - 1] + RNW
        mark = {"circle": '<circle cx="0" cy="0" r="6.5" class="ringmark"/>',
                "square": '<rect x="-6.5" y="-6.5" width="13" height="13" '
                          'class="ringmark"/>',
                "triangle": '<path d="M0,-7 L7,5.5 L-7,5.5 z" class="ringmark"/>'}[shape]
        overlay = (f'<g class="ap-{short}">'
                   + path(f"M{RX[0] - 12},{y - 24} H{x2 + 12} V{y + RNH + 12} "
                          f"H{RX[0] - 12} Z", "apline")
                   + f'<g transform="translate({RX[0] - 12},{y - 24})">{mark}</g>'
                   + txt(RX[0] + 16, y - 34,
                         f"{label} (Option {letter}) serves this reader first",
                         "ringlab")
                   + "</g>")
        files[f"75-stakeholders-{short}.svg"] = build(
            did,
            f"{label} (Option {letter}) and the stakeholder it serves first",
            READERS_DESC + f" Outlined on this variant is the {reader}'s path, which "
            f"{label} (Option {letter}) serves first. The pairing is recorded in "
            "data/six-questions.json, one stakeholder per approach, and each of the three "
            "variants outlines exactly one path. Serving one stakeholder first is not a "
            "claim that the approach serves the others badly, and it is not a ranking "
            "of the readers.",
            overlay=overlay)
    return files


# --------------------------------------------------------------------------- #
# 8. diagram 7.6, the satisfaction split                                       #
# --------------------------------------------------------------------------- #

SIX_DIFFERENCES = [
    ("question answered", "How is this satisfied?", "Was it satisfied, when, on what?"),
    ("who asserts it", "the system owner", "the assessor"),
    ("time", "standing design intent", "a point in time"),
    ("form", "narrative, arguable", "binary or graded, evidenced"),
    ("granularity", "per component", "per subject, of several types"),
    ("fails when", "the narrative is vague",
     "the evidence is stale, or the subject is wrong"),
]


def diagram_76(c: Corpus) -> dict[str, str]:
    did = "dg-76-satisfaction-6a-6b"
    o = []
    o.append(rect(320, 24, 320, 58, "model", 9))
    o.append(txt(480, 50, "one rule", "n", "middle"))
    o.append(txt(480, 70, "one requirement, one condition", "s mu", "middle"))
    o.append(path("M420,82 V104 H244 V134", "join", f"{did}-join"))
    o.append(path("M540,82 V104 H716 V134", "join", f"{did}-join"))

    cols = [
        (40, "6a", "Implementation claim", "how it is satisfied",
         ["implemented-requirement", "statement", "by-component"],
         "narrative  .  standing  .  per component",
         "system-security-plan"),
        (512, "6b", "Assessment result", "whether it was satisfied",
         ["observation", "finding", "objective-status"],
         "evidenced  .  point in time  .  per subject",
         "assessment-results"),
    ]
    for x, slot, name, question, chain, attrs, home in cols:
        o.append(f'<g class="sl{slot}">')
        o.append(rect(x, 134, 408, 62, "sl-filled", 9))
        o.append("</g>")
        o.append(slot_chip(x + 48, 146, slot, "filled"))
        o.append(txt(x + 60, 162, name, "n"))
        o.append(txt(x + 60, 184, f'"{question}"', "s mu"))
        o.append(txt(x + 14, 224, home, "m mu"))
        cy = 238
        for i, step in enumerate(chain):
            o.append(rect(x + 14, cy, 380, 54, "box", 8))
            o.append(txt(x + 30, cy + 33, step, "m"))
            if i < len(chain) - 1:
                o.append(path(f"M{x + 204},{cy + 54} V{cy + 70}", "ref",
                              f"{did}-ref"))
            cy += 78
        o.append(txt(x + 14, cy + 12, attrs, "s mu"))

    ty = 524
    o.append(txt(40, ty, "The six differences, from plan section 2.1", "n"))
    ty += 38
    #  The comment here used to claim the columns matched the panels above and
    #  were of equal width. Neither was true: the widths were 250 and 408, so the
    #  6b column wrapped at a measure half as wide again as 6a and the two read as
    #  ragged rather than as a pair. A table beneath two panels cannot align to
    #  them anyway, because the panels start at the drawing's left edge and the
    #  table needs a label gutter first. So the table is made internally
    #  symmetrical instead: label gutter, then two data columns of identical width
    #  with identical gaps, ending flush with the rules at x=920.
    #      40 ..240   label      200 wide
    #     260 ..580   6a         320 wide
    #     600 ..920   6b         320 wide
    colx = [40, 260, 600]
    colw = [200, 320, 320]

    #  Every line is centred between the rule above it and the rule below.
    #
    #  It was not, and that was the whole of what looked wrong with this table.
    #  A row advanced by 20n + 10 and set its first baseline at the top of the
    #  band, so the ink sat hard against the rule above with about 15 units of
    #  space below it, and six rows of that read as though every line had
    #  slipped upward out of its box. Text set at a fixed offset from one edge
    #  of a variable-height band is never centred in it; the offset has to be
    #  computed from the height.
    #
    #  LEAD is baseline to baseline inside a cell. ASC and DESC are the ink
    #  above and below a baseline at 16px, which is what .s is. PAD is the space
    #  left over, and it is applied equally at the top and the bottom.
    #
    #  A cell with fewer lines than the tallest cell in its row is centred on
    #  its own, so "fails when" lands between the two lines beside it rather
    #  than beside the first of them.
    LEAD, ASC, DESC, PAD = 20, 12, 4, 10
    o.append(path(f"M40,{ty + 8} H920", "rule"))
    for i, hd in enumerate(["", "6a. Implementation claim", "6b. Assessment result"]):
        if hd:
            o.append(txt(colx[i], ty, hd, "s mu"))
    top = ty + 8
    for row in SIX_DIFFERENCES:
        rows = [wrap(cellv, int(colw[i] / 8.3)) for i, cellv in enumerate(row)]
        n = max(len(r) for r in rows)
        band = (n - 1) * LEAD + ASC + DESC + 2 * PAD
        for i, lines in enumerate(rows):
            ink = (len(lines) - 1) * LEAD + ASC + DESC
            base = top + (band - ink) / 2 + ASC
            for j, ln in enumerate(lines):
                o.append(txt(colx[i], round(base + j * LEAD, 1), ln,
                             "s mu" if i == 0 else "s"))
        top += band
        o.append(path(f"M40,{top} H920", "rule"))
    ty = top

    #  A pull quote from the Easy Dynamics deck stood here, making the same point
    #  the table above already makes from the OSCAL schemas. It was removed. The
    #  distinction between a claim and a result is a property of the models, and it
    #  is better carried by the six differences than by one participant's slide.
    #  Sourcing a structural point to the site author's own advocacy invited a
    #  reader to discount the point along with the source.
    #
    #  A legend stood here too, naming the 6a and 6b chips, the assembly box and
    #  the resolved reference. It is gone. This drawing labels every one of those
    #  in place: the chips carry "6a" and "6b" beside the words Implementation
    #  claim and Assessment result, the boxes carry the assembly names, and the
    #  table underneath states the six differences in words. A legend that only
    #  renames what the drawing has already said in full is a second thing to
    #  read for no more meaning, and it was the longest block on the section.
    body = "\n".join(o)
    return {"76-satisfaction-6a-6b.svg": svg(
        did, ty + 24,
        "One rule, two satisfaction assertions: the implementation claim and the "
        "assessment result",
        "One rule sits at the top and two paths lead out of it, side by side and drawn "
        "at the same size. On the left is question 6a, the implementation claim, which "
        "answers how the rule is satisfied. It lives in the system security plan and "
        "runs implemented-requirement, then statement, then by-component. It is "
        "narrative, it is standing design intent, it is asserted by the system owner, "
        "it is expressed per component, and it fails when the narrative is vague. On "
        "the right is question 6b, the assessment result, which answers whether the rule "
        "was satisfied, when, and on what. It lives in assessment results and runs "
        "observation, then finding, then objective-status. It is evidenced, it is a "
        "point in time, it is asserted by the assessor, it is expressed per subject of "
        "several types, and it fails when the evidence is stale or the subject is "
        "wrong. A table beneath the figure sets out those six differences in full. A "
        "rule carrying desired state has a binary satisfaction condition, while the "
        "implementation statement expects a narrative one, and conflating the two is the "
        "modelling error the figure exists to mark. Both can be populated from "
        "one rule without contradiction, and an approach that populates only one is "
        "not wrong; it is unfinished in a nameable place.",
        body, slots=True)}


# --------------------------------------------------------------------------- #
# 9. diagram 7.7, the optional tie                                             #
# --------------------------------------------------------------------------- #

def diagram_77(c: Corpus) -> dict[str, str]:
    did = "dg-77-optional-tie"
    slot2 = c.slot("2")
    bts = {b["key"]: b for b in slot2["binding_times"]}
    constraint = ("mapping-item.type in {" + ", ".join(c.mapping_type_enum) + "}")

    # Route availability.
    #   inline    : available to all three. Both are author-time mechanisms that
    #   pointer     need only a field or a prop, which every one of the three
    #               models already has. Plan section 2.2.2, third column.
    #   late      : declared on the binding time itself, in data/six-questions.json.
    #               It used to be read from a matrix row, question 2b, which
    #               made a property of the OSCAL mapping model into a question
    #               an approach answers and scored it as one. That row is gone.
    #               The fact it carried is unchanged and is now attached to the
    #               mechanism it is a fact about.
    avail = {
        "inline": {k: True for k, *_ in APPROACHES},
        "pointer": {k: True for k, *_ in APPROACHES},
        "late": {k: bool(bts["late"]["available_to"].get(k)) for k, *_ in APPROACHES},
    }

    o = [txt(24, 34, "Three binding times, and who can use each", "h")]
    RBX = [24, 340, 656]
    RBW, RBH = 280, 152
    LINE_TOP, LINE_BOT = RBH + 60, 322       # where the nine approach lines run
    order = ["inline", "pointer", "late"]
    for i, bkey in enumerate(order):
        bt = bts[bkey]
        x = RBX[i]
        o.append(rect(x, 54, RBW, RBH, "box", 9))
        o.append(txt(x + 14, 80, bt["label"], "n"))
        ly = 106
        for ln in wrap(bt["mechanism"], 34):
            o.append(txt(x + 14, ly, ln, "s"))
            ly += 20
        ly = max(ly + 6, 172)
        for ln in wrap("authored by " + bt["authored_by"].lower(), 33):
            o.append(txt(x + 14, ly, ln, "s mu"))
            ly += 19
        for j, (akey, _al, _lt, short, shape) in enumerate(APPROACHES):
            lx = x + 58 + j * 82
            ok = avail[bkey][akey]
            mid = (LINE_TOP + LINE_BOT) / 2 + 14
            mark = {"circle": f'<circle cx="{lx}" cy="{mid}" r="7" class="ringmark"/>',
                    "square": f'<rect x="{lx - 7}" y="{mid - 7}" width="14" '
                              f'height="14" class="ringmark"/>',
                    "triangle": f'<path d="M{lx},{mid - 7} L{lx + 7.5},{mid + 6} '
                                f'L{lx - 7.5},{mid + 6} z" class="ringmark"/>'}[shape]
            o.append(f'<g class="ap-{short}">'
                     + path(f"M{lx},{LINE_TOP} V{LINE_BOT}",
                            "apline" if ok else "apline-off")
                     + mark + "</g>")
            if not ok:
                o.append(cut(lx, (LINE_TOP + LINE_BOT) / 2 - 26))
    o.append(txt(936, 344, constraint, "m", "end"))
    o.append(txt(936, 366, "and mapping-item has no uuid and no href",
                 "s mu", "end"))

    SOCK_Y, SOCK_H = 388, 140
    o.append(socket(24, SOCK_Y, 912, SOCK_H))
    o.append(slot_chip(96, SOCK_Y + 14, "2", "empty-by-design"))
    o.append(txt(110, SOCK_Y + 30, "question 2, the link to a control", "n"))
    sy = SOCK_Y + 54
    for ln in wrap("Drawn as an empty socket, because an empty socket is a legitimate "
                   "published state and not a defect.", 84):
        o.append(txt(110, sy, ln, "s"))
        sy += 22
    for ln in wrap("A rule may serve several controls, one, or none. The mechanism "
                   "has to exist and must not be mandatory.", 84):
        o.append(txt(110, sy, ln, "s mu"))
        sy += 22

    o.append(txt(24, SOCK_Y + SOCK_H + 26, "What follows from the socket", "h"))
    forks = [
        (24, "socket filled", "6", [
            ("finding", f'requires {", ".join(c.finding_required[:3])} and target'),
            ("finding-target", "type is closed to " + " or ".join(c.ft_type_enum)),
            ("a determination", "state: " + " or ".join(c.ft_state_enum)),
        ], "The tie is what converts evidence into a determination."),
        (496, "socket empty", None, [
            ("observation", "requires only " + ", ".join(c.obs_required)),
            ("no finding", "finding requires target, which is control-derived"),
            ("the path stops", "record what you saw, not whether it complied"),
        ], "Legitimate, published, complete for its own purpose."),
    ]
    FW = 440
    bottom = 0
    ARROW_TOP = SOCK_Y + SOCK_H + 40
    for x, head, slot, steps, foot in forks:
        o.append(path(f"M{x + 220},{ARROW_TOP} V{ARROW_TOP + 44}", "ref",
                      f"{did}-ref"))
        o.append(txt(x, ARROW_TOP + 78, head, "n"))
        sy = ARROW_TOP + 92
        for i, (name, note) in enumerate(steps):
            cls = "box" if slot or i == 0 else "hollow"
            lines = wrap(note, 48)
            h = 44 + 20 * len(lines)
            o.append(rect(x, sy, FW, h, cls, 8))
            o.append(txt(x + 16, sy + 28, name, "m"))
            for j, ln in enumerate(lines):
                o.append(txt(x + 16, sy + 50 + j * 20, ln, "s mu"))
            if i < len(steps) - 1:
                o.append(path(f"M{x + 220},{sy + h} V{sy + h + 18}", "ref",
                              f"{did}-ref"))
            sy += h + 20
        footlines = wrap(foot, 48)
        for j, ln in enumerate(footlines):
            o.append(txt(x, sy + 14 + j * 20, ln, "s mu"))
        bottom = max(bottom, sy + 14 + len(footlines) * 20)

    summary = slot2["cost_of_leaving_empty"]["summary"]
    o.append(txt(24, bottom + 26, summary, "n"))
    items = (LI(G_SOCKET, "an empty socket: a question that may legitimately stay unanswered")
             + LI(G_BOX, "an OSCAL assembly that is reachable")
             + LI(G_CUT, "a route this approach cannot use")
             + LI(G_REF, "a resolved reference"))
    for _k, label, letter, short, shape in APPROACHES:
        items += LI(g_ring(short, shape), f"{label} (Option {letter})")
    items += LI("", "Inline and by-pointer binding are available to all three. "
                    "Late binding is available only where the rule is already a "
                    "control. That is a gap in OSCAL, not a defect in any "
                    "approach, and it rewards whichever view of a rule the "
                    "schema already assumes.")
    LEG_Y = bottom + 50
    body = "\n".join(o) + "\n" + legend(did, 24, LEG_Y, items, cols=2)
    return {"77-optional-tie.svg": svg(
        did, LEG_Y + legend_h(items),
        "Question 2, the optional link to a control: three ways in, and what follows from "
        "leaving it empty",
        "Question 2, the link to a control, is drawn as an empty socket rather than as a filled "
        "node, and an empty socket is a legitimate published state, not a defect. A "
        "rule is finer than a control and may serve several controls, one, or none; "
        "the mechanism has to exist and must not be mandatory. Three routes lead into "
        "the socket, one per binding time. Author-time inline: the rule declares its "
        "control directly, authored by whoever wrote the rule. Author-time by pointer: "
        "a prop carries an external framework identifier that a consumer must resolve, "
        "authored by whoever wrote the rule. Late and external: a separate artifact "
        "ties rule to control after publication, and it can be authored by anyone, "
        "including a third party. Under each route, three lines run down to the socket, "
        "one per approach in option-letter order: Catalog-first, Component-first, "
        "Component-first. Every line under the inline route and under the by-pointer "
        "route is unbroken, because both are available to all three approaches. Under "
        "the late route, only the Catalog-first line is unbroken; the Assessment-first "
        "and Component-first lines are struck through, and the schema constraint that "
        f"strikes them is printed beneath: {constraint}, and mapping-item has no uuid "
        "and no href. So OSCAL's one native, optional, late, third-party-authorable "
        "mechanism reaches only rules that are already modelled as controls. That is a "
        "gap in OSCAL rather than a defect in any approach, and it rewards whichever "
        "view of a rule the schema already assumes. Below the socket the figure forks. "
        "With the socket filled, the path continues to finding, which requires a "
        "target; to finding-target, whose type is closed to "
        + " or ".join(c.ft_type_enum) + "; and on to a determination of "
        + " or ".join(c.ft_state_enum) + ". With the socket empty, the path reaches "
        "observation, which requires only " + ", ".join(c.obs_required)
        + " and carries no control reference of any kind, and then stops: there is no "
        "finding, because finding requires a target and every target type is "
        f"control-derived. {summary} That is the exact cost of optionality, and it is "
        "a schema fact rather than an opinion.",
        body, slots=True, approaches=True)}


# --------------------------------------------------------------------------- #
# 10. diagram 7.8, three views of what a rule is                               #
# --------------------------------------------------------------------------- #

def diagram_78(c: Corpus) -> dict[str, str]:
    did = "dg-78-three-views"
    o = [txt(24, 34, "One hardening rule, three readings", "h")]
    o.append(hexagon(24, 252, 236, 104, "model"))
    o.append(txt(142, 298, "one hardening", "n", "middle"))
    o.append(txt(142, 320, "rule", "n", "middle"))
    #  The example sits under the hexagon, not inside it: the sloped sides cut
    #  into the usable width exactly where a second line of text would fall.
    #  It is written generically on purpose, so that no corpus supplies the
    #  running example for a figure about whose corpus is right.
    o.append(txt(24, 386, "for example: encrypt data at rest", "s mu"))

    #  Identical geometry for all three: same x, same width, same height, same
    #  vertical spacing. The order is the order in views.json, which that file
    #  records as the order of the OSCAL layers and not a ranking.
    NX, NW2, NH2 = 392, 544, 178
    for i, v in enumerate(c.views["views"]):
        y = 40 + i * 200
        o.append(rect(NX, y, NW2, NH2, "box", 10))
        o.append(txt(NX + 20, y + 34, v["label"], "n"))
        ly = y + 60
        for ln in wrap(v["definition"], 62):
            o.append(txt(NX + 20, ly, ln, "s"))
            ly += 21
        o.append(txt(NX + 20, y + NH2 - 56,
                     "implied layer: " + v["implies_layer"], "s mu"))
        o.append(txt(NX + 20, y + NH2 - 34,
                     "implied model: " + v["implies_model"], "s mu"))
        o.append(txt(NX + 20, y + NH2 - 12, "on the record: " + v["advocate"], "s mu"))
        o.append(path(f"M260,304 H{NX - 44} V{y + NH2 / 2} H{NX - 3}", "join",
                      f"{did}-join"))

    q = c.quote("preread-requirement-level-absent")
    by = 656
    o.append(rect(24, by, 912, 96, "hollow", 9))
    o.append(txt(44, by + 30, "Criterion 3, requirement level: can shall, should "
                              "and may be represented at all?", "n"))
    o.append(txt(44, by + 56, f'"{q["text"]}"', "s"))
    o.append(txt(44, by + 78, q["source_document"], "s mu"))
    fy = by + 126
    for ln in wrap("OSCAL has no field for normativity, so location has become the "
                   "only channel for expressing it. That is why these three readings "
                   "imply three different homes, and why no option can settle the "
                   "question by construction.", 104):
        o.append(txt(24, fy, ln, "s"))
        fy += 22

    items = (LI(G_HEX, "a control, and here the rule whose kind is in dispute")
             + LI(G_BOX, "one reading of what that rule is")
             + LI(G_JOIN, "a reading, not an OSCAL reference")
             + LI(G_SOCKET, "a question OSCAL cannot express")
             + LI("", "All three nodes are the same size, at the same x, evenly "
                      "spaced. The order is the order of the OSCAL layers, from "
                      "data/views.json, and it is not a ranking. Each reading is "
                      "internally coherent, and the site declares a working "
                      "definition rather than taking a position."))
    body = "\n".join(o) + "\n" + legend(did, 24, fy + 14, items, cols=2)
    return {"78-three-views.svg": svg(
        did, fy + 14 + legend_h(items),
        "One hardening rule, and the three incompatible readings of what it is",
        "One hardening rule sits on the left, drawn as a control shape because whether "
        "it is a control is exactly what is in dispute. Three readings lead out of it, "
        "drawn at identical size, at the same horizontal position and evenly spaced, "
        "because none is ranked above another. The order is the order of the OSCAL "
        "layers, taken from data/views.json, and it is not a ranking. "
        + " ".join(
            f"Reading {i + 1}: {v['label']}. {v['definition']} Implied layer: "
            f"{v['implies_layer']}. Implied model: {v['implies_model']}. On the record: "
            f"{v['advocate']}."
            for i, v in enumerate(c.views["views"]))
        + " Beneath the three readings is a single bar carrying criterion 3 of the "
        "pre-read, requirement level: can shall, should and may be represented at all? "
        f"The pre-read answers for every option in one cell: {q['text']} OSCAL has no "
        "field for normativity, so location has become the only channel available for "
        "expressing it. Putting a rule in a catalog asserts requirement by placement, "
        "putting it in a component definition asserts capability by placement, and "
        "putting it in an assessment plan asserts procedure by placement. Nobody chose "
        "location as a proxy for normativity; it is the only channel there is. Each of "
        "the three readings is internally coherent, the site takes no position on which "
        "is correct, and it declares a working definition instead: "
        + c.views["working_definition"]["text"],
        body)}


# --------------------------------------------------------------------------- #
# 11. diagram 7.8 scale figure                                                 #
# --------------------------------------------------------------------------- #

def diagram_79(c: Corpus) -> dict[str, str]:
    did = "dg-79-scale"
    reg = c.cited("regulatory_controls")
    ben = c.cited("benchmark_requirements")
    both = c.cited("combined")
    source = c.statsdoc["cited_from_position_paper"]["source"]
    U = 0.75                                   # user units per requirement
    BAR_H = 46
    RW, BW = round(reg * U, 1), round(ben * U, 1)
    o = [txt(24, 34, "Two populations, and three places the second could go", "h")]

    #  Three sockets, one per destination, and one bar that moves between them.
    #  The sockets are positions on the page, so the choice is spatial rather
    #  than described: destination B abuts the regulatory bar on the same row,
    #  which is what "+563 controls in the SSP" means.
    SOCKETS = {
        "stay": (24, 190, "outside the SSP"),
        "controls": (24 + RW, 84, "as controls, on the SSP control row"),
        "rules": (48, 284, "as rules on SSP components"),
    }

    o.append(txt(24, 72, "the SSP control count", "n"))
    o.append(rect(24, 84, RW, BAR_H, "box", 6))
    o.append(txt(38, 114, str(reg), "m"))
    for key, (sx, sy, slabel) in SOCKETS.items():
        o.append(f'<g id="{did}-socket-{key}">')
        o.append(socket(sx, sy, BW, BAR_H))
        #  Above the socket, not inside it: the bar sits inside whichever
        #  socket is chosen, and would cover a label placed there.
        o.append(txt(sx, sy - 10, slabel, "s mu"))
        o.append("</g>")

    sx, sy, _ = SOCKETS["stay"]
    o.append(f'<g id="{did}-mover" class="mover" '
             f'data-home="{sx},{sy}" transform="translate(0,0)">')
    o.append(rect(sx, sy, BW, BAR_H, "box", 6))
    o.append(txt(sx + 14, sy + 30, f"about {ben} benchmark requirements", "m"))
    o.append("</g>")

    o.append(txt(24, 366, "resulting SSP control count:", "n"))
    o.append(f'<text x="316" y="366" class="m" id="{did}-count">{reg}</text>')
    ry = 392
    for ln in wrap("Choose a destination below. Without scripting the bar does not "
                   "move, and all three consequences are still printed.", 104):
        o.append(txt(24, ry, ln, "s mu"))
        ry += 22

    dests = [
        ("stay", "no change to SSP control count", reg,
         "The benchmark stays outside the SSP. The SSP keeps its regulatory scope, and "
         "adding or updating a benchmark does not touch it."),
        ("controls", f"+{ben} controls in the SSP", both,
         "Every benchmark requirement becomes a control the SSP must respond to. The "
         "control count is the sum of the two populations."),
        ("rules", f"+{ben} desired-state rules in SSP components", reg,
         "The benchmark enters the SSP as rules on components rather than as controls, "
         "so the control count does not change."),
    ]
    DX, DW = [24, 336, 648], 288
    dy_end = 0
    for i, (key, label, count, note) in enumerate(dests):
        x = DX[i]
        label_lines, note_lines = wrap(label, 26), wrap(note, 30)
        dh = 44 + 24 * len(label_lines) + 50 + 20 * len(note_lines)
        o.append(f'<g id="{did}-dest-{key}">')
        #  A hairline rule, not a box. A hollow box would read as one of the
        #  three empty states, and these are description panels, not questions.
        o.append(path(f"M{x},420 H{x + DW}", "rule"))
        ly = 452
        for ln in label_lines:
            o.append(txt(x + 16, ly, ln, "n"))
            ly += 24
        o.append(txt(x + 16, ly + 16, "resulting SSP control count:", "s mu"))
        o.append(txt(x + 16, ly + 38, str(count), "m"))
        ly += 62
        for ln in note_lines:
            o.append(txt(x + 16, ly, ln, "s mu"))
            ly += 20
        o.append("</g>")
        dy_end = max(dy_end, 420 + dh)

    cy = dy_end + 34
    for ln in wrap(f"The figures {reg}, {ben} and {both} are cited from {source}. "
                   f"They are not computed from the corpora, and per editorial rule "
                   f"10 they are attributed as advocacy at every appearance.", 108):
        o.append(txt(24, cy, ln, "s mu"))
        cy += 22
    items = (LI(G_BOX, "a population of requirements, drawn to scale")
             + LI(G_SOCKET, "a destination the second population could take")
             + LI("", "One requirement is 0.75 units wide in both bars, so the "
                      "two are directly comparable. The three destinations are "
                      "the three positions on the record, and the site does not "
                      "choose between them."))
    body = "\n".join(o) + "\n" + legend(did, 24, cy + 12, items, cols=2)
    return {"79-scale.svg": svg(
        did, cy + 12 + legend_h(items),
        "Regulatory controls against benchmark requirements, and the three "
        "destinations for the second population",
        f"Two bars drawn to the same scale, at 0.75 units per requirement. The first "
        f"bar is {reg} regulatory controls for one system, and it is fixed on the row "
        f"labelled the SSP control count. The second is about {ben} benchmark "
        f"requirements for that same system. It starts in the socket labelled outside "
        f"the SSP and moves between three sockets when the reader chooses one: "
        f"outside the SSP, on the SSP control row abutting the regulatory bar, or on "
        f"the SSP components row. The three "
        f"destinations are: no change to SSP control count, which leaves the resulting "
        f"count at {reg}, because the benchmark stays outside the system security plan; "
        f"plus {ben} controls in the SSP, which makes the resulting count {both}, "
        "because every benchmark requirement becomes a control the plan must respond "
        f"to; and plus {ben} desired-state rules in SSP components, which leaves the "
        f"resulting count at {reg}, because the benchmark enters as rules on components "
        f"rather than as controls. The figures {reg}, {ben} and {both} are cited from "
        f"{source}. They are not computed from the corpora, and the site attributes "
        "them as advocacy at every appearance. The figure does not choose between the "
        "three destinations.",
        body)}



# --------------------------------------------------------------------------- #
# 12. diagram 7.10, the scenario file set                                      #
# --------------------------------------------------------------------------- #

#  One tile is one file, and a tile is the same size in all three drawings. That
#  is the whole mechanism: the three figures are read side by side, so the area
#  of ink is the comparison and no number has to be believed. Everything else on
#  the figure is labelling.
#
#  A model an approach does not use is still drawn, hollow, with the word none.
#  Leaving it out would make the absence invisible, and the absence is half of
#  what separates the three.
#  A tile is wide enough for the name of the file it stands for, on two lines,
#  and tall enough for a third line naming the kind where a model holds more
#  than one kind. The names are what let a reader follow one document from the
#  figure into the list beneath it: six identical blank tiles under
#  component-definition said nothing about which three hold the thing being
#  configured and which three hold the checks.
#  16px, not smaller. A diagram is displayed at three quarters of its authoring
#  width, so 16px here is 12px on the page, which is the floor the whole site
#  holds to and tools/verify.py --diagrams enforces. The tile is sized around
#  that rather than the text being shrunk to fit the tile.
TILE_W, TILE_H, TILE_GAP = 122, 70, 10
SC_ROW = 3                       # tiles before wrapping to a second row
SC_CHARS = 10                    # characters that fit on one line of a tile
SC_BANDS = [
    ("CONTROL LAYER", ["catalog", "profile", "mapping-collection"]),
    ("IMPLEMENTATION LAYER", ["component-definition", "system-security-plan"]),
    ("ASSESSMENT LAYER", ["assessment-plan", "assessment-results"]),
]
SC_SHORT = {
    "catalog": "catalog",
    "profile": "profile",
    "mapping-collection": "mapping-collection",
    "component-definition": "component-definition",
    "system-security-plan": "system-security-plan",
    "assessment-plan": "assessment-plan",
    "assessment-results": "assessment-results",
}


def _sc_tiles(x, y, n, items, per_row=SC_ROW):
    """n file tiles from x, wrapping, each named and each with a folded corner.

    A model with no files gets a dashed rule the width of one tile, not a hollow
    tile. An outline the same shape and size as a file reads as a file at a
    glance, and the figure is meant to be counted at a glance: drawn that way,
    an approach that uses five models looked like it used seven.
    """
    if not n:
        mid = y + TILE_H // 2
        return [path(f"M{x},{mid} h{TILE_W}", "weak")], 1
    out = []
    for i in range(n):
        col, row = i % per_row, i // per_row
        tx = x + col * (TILE_W + TILE_GAP)
        ty = y + row * (TILE_H + 10)
        out.append(rect(tx, ty, TILE_W, TILE_H, "model", 3))
        #  The fold reads as a document at this size, where a plain rectangle
        #  reads as a box of something.
        out.append(path(f"M{tx + TILE_W - 9},{ty} v9 h9", "contain"))
        it = items[i] if i < len(items) else {}
        lines = wrap(it.get("name", ""), SC_CHARS)[:2]
        block = len(lines) * 21 + (21 if it.get("kind") else 0)
        top = ty + (TILE_H - block) / 2 + 16
        for j, line in enumerate(lines):
            out.append(txt(tx + TILE_W / 2, top + j * 21, line, "tl", "middle"))
        if it.get("kind"):
            out.append(txt(tx + TILE_W / 2, top + len(lines) * 21,
                           it["kind"], "tk", "middle"))
    return out, (n - 1) // per_row + 1


def _sc_group(x, y, model, entry, width):
    """One model: its name, its tiles, the count and what they are.

    Returns the drawing and the height it used, because the caption under a
    group wraps to one line or two depending on the model name, and a band sized
    for one line clips the second.
    """
    n = entry["count"]
    lines = wrap(entry["what"], max(18, width // 9))[:2]
    #  The icon, then the name, matching the chip the table and the lists above
    #  use. Not the chip itself: a bordered box the width of a short label,
    #  sitting directly above a row of bordered boxes each of which means one
    #  file, is a box a reader can count. The same reasoning that keeps an
    #  unused model as a dashed rule rather than a hollow tile. The icon alone
    #  ties the figure to the table without adding an outline to a figure whose
    #  outlines are its content.
    #  21, the same size the chain figure draws it, not the height of the label
    #  beside it. A diagram is shown at three quarters of its authoring width, so
    #  an icon matched to 16px text lands at 12px on the page, and 12px is where
    #  these icons stop being readable: the whole reason they were redrawn was
    #  that a shape inside a chip disappears at small sizes.
    o = [model_icon(model, x, y - 16, 21),
         txt(x + 29, y, SC_SHORT[model], "m")]
    #  As many tiles per row as the group is wide enough for, so a two-group
    #  band uses the room it has rather than wrapping at three out of habit.
    per_row = max(1, min(SC_ROW + 1, (width + TILE_GAP) // (TILE_W + TILE_GAP)))
    tiles, rows = _sc_tiles(x, y + 14, n, entry.get("items", []), per_row)
    o += tiles
    ty = y + 14 + rows * (TILE_H + 10)
    o.append(txt(x, ty + 10, f"{n} file" + ("" if n == 1 else "s"), "n"))
    for i, line in enumerate(lines):
        o.append(txt(x, ty + 34 + i * 20, line, "s mu"))
    return o, (ty + 34 + 20 * len(lines)) - y


def diagram_710(c: Corpus) -> dict[str, str]:
    sc = c.scenario
    files = {}
    reg = sc["framework"]["controls"]
    hard = sum(h["requirements"] for h in sc["hardening"])

    for key, short in (("catalog-first", "catalog"),
                       ("component-first", "component"),
                       ("assessment-first", "assessment")):
        a = sc["approaches"][key]
        by = {f["model"]: f for f in a["files"]}
        total = sum(f["count"] for f in a["files"])
        used = sum(1 for f in a["files"] if f["count"])
        did = f"dg-710-scenario-{short}"
        o = []

        across = ("across all seven models" if used == 7
                  else f"across {used} of the seven models")
        o.append(txt(24, 34, f"{total} files, {across}", "h"))
        o.append(txt(24, 60, a["rule"], "s mu")
                 if len(a["rule"]) < 96 else "")
        yy = 60
        if len(a["rule"]) >= 96:
            for i, line in enumerate(wrap(a["rule"], 104)):
                o.append(txt(24, 60 + i * 22, line, "s mu"))
            yy = 60 + 22 * len(wrap(a["rule"], 104))

        y = yy + 24
        for band, models in SC_BANDS:
            gw = (W - 80) // len(models)
            drawn, tallest = [], 0
            for i, m in enumerate(models):
                g, h = _sc_group(32 + i * gw, y + 52, m, by[m], gw - 20)
                drawn += g
                tallest = max(tallest, h)
            band_h = 52 + tallest + 14
            o.append(rect(16, y, W - 32, band_h, "band", 10))
            o.append(txt(32, y + 26, band, "n mu"))
            o += drawn
            y += band_h + 14

        #  The one line the figure exists to carry, stated where the plan of
        #  record is drawn rather than in the caption. Authored rather than
        #  computed: a computed line could only report whether the control count
        #  moved, and for one of the three that is true and misleading.
        note = a["plan_of_record"]
        #  Wrapped, because this line is the one the figure exists to carry and
        #  it ran off the right edge of the canvas when it did not fit.
        nlines = wrap(note, 96)
        band_h = 22 + len(nlines) * 26
        o.append(rect(16, y, W - 32, band_h, "band", 10))
        for i, line in enumerate(nlines):
            o.append(txt(32, y + 30 + i * 26, line, "n"))
        y += band_h + 14

        desc = (
            f"A count of the OSCAL files this approach needs for the scenario, "
            f"drawn as one tile per file. {total} files in total, {across}. " +
            " ".join(
                f"{by[m]['count']} {SC_SHORT[m]} "
                f"{'file' if by[m]['count'] == 1 else 'files'}"
                f"{', ' + by[m]['what'] if by[m]['what'] else ''}"
                + (", named " + ", ".join(
                    i["name"] + (f" ({i['kind']})" if i.get("kind") else "")
                    for i in by[m].get("items", []))
                   if by[m].get("items") else "")
                + "."
                for _b, ms in SC_BANDS for m in ms) +
            f" A model this approach does not use is drawn hollow and labelled "
            f"none, so the absence is as visible as the presence. The tile is the "
            f"same size in all three figures, so the area of ink is the "
            f"comparison. {note}.")
        files[f"710-scenario-{short}.svg"] = svg(
            did, y, f"{sc['title']}: the file set for the "
            f"{key.replace('-', ' ')} approach", desc, "\n".join(x for x in o if x))
    return files


# --------------------------------------------------------------------------- #
# run                                                                          #
# --------------------------------------------------------------------------- #

BUILDERS = (diagram_72, diagram_73, diagram_75,
            diagram_76, diagram_77, diagram_78, diagram_79,
            diagram_710)

#  The library builds more than the site shows. Diagrams 72, 77, 78 and 79 and
#  the three stakeholder variants were only ever on a component gallery that has
#  been removed, so they are built and dropped rather than written. Keeping the
#  builders costs nothing and keeps the drawing code for them in one place;
#  writing them would leave live files among dead ones with no way to tell which
#  is which.
#
#  The layer map went further than that and is gone entirely. It was published,
#  and then the section that showed it was replaced by the chain, and a figure
#  nothing links to is worse than one that was never written: it is still built,
#  still checked, still in the directory, and a reader never sees it. The check
#  that would have caught it is below, in tools/verify.py: a published figure
#  now has to be referenced by a page.
PUBLISHED = {
    "73-join-assessment.svg", "73-join-catalog.svg", "73-join-component.svg",
    "75-stakeholders.svg", "76-satisfaction-6a-6b.svg",
    "710-scenario-catalog.svg", "710-scenario-component.svg",
    "710-scenario-assessment.svg",
}


def run(outdir: str, quiet: bool = False) -> dict[str, str]:
    c = Corpus()
    files: dict[str, str] = {}
    for fn in BUILDERS:
        files.update(fn(c))
    os.makedirs(outdir, exist_ok=True)
    files = {k: v for k, v in files.items() if k in PUBLISHED}
    for name, content in sorted(files.items()):
        with open(os.path.join(outdir, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        if not quiet:
            print(f"  {name:34s} {len(content):>7,} bytes")
    return files


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=OUT_DEFAULT)
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args()
    files = run(a.out, a.quiet)
    if not a.quiet:
        print(f"\n{len(files)} diagrams written to {a.out}")


if __name__ == "__main__":
    main()
