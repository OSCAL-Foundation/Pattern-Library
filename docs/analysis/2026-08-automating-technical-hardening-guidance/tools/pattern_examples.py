#!/usr/bin/env python3
"""
tools/pattern_examples.py: author data/pattern-examples.json.

WHAT THIS IS. The three approaches ship content for different products, so
quoting what each one published means comparing a certificate control against an
object-store rule against a Linux STIG. That is a comparison of subject matter,
not of modelling, which is the only thing this site is for.

So the examples here are ours. Two rules, chosen once, written in all three
shapes. The rules are real: both are Ubuntu 24.04 LTS STIG requirements, with
their published identifiers kept so a reader can look them up. What is authored
is the encoding, and only the encoding.

NAMESPACES ARE NOT OURS. Every prop carries the namespace of the approach whose
pattern it illustrates: AWS's own ns for the catalog shape, the STIG ns for the
assessment shape, and IBM's proposed first-class assemblies, which need no ns
because the whole point of the proposal is that they are not props. Nothing here
invents a namespace.

Run with --check to fail if the committed file is stale.
"""

import hashlib
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "pattern-examples.json")

def uid(seed: str) -> str:
    """A stable, well-formed v4-shaped uuid from a seed.

    These were hand-written literals with a suffix concatenated on, which is how
    two of them ended up 35 characters long and invalid. Deriving them from a
    seed makes that class of mistake impossible and keeps the output stable
    between runs, which --check depends on.
    """
    h = hashlib.sha256(("tfg:" + seed).encode("utf-8")).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-4{h[13:16]}-8{h[17:20]}-{h[20:32]}"


AWS_NS = "http://aws.amazon.com/ns/oscal"
STIG_NS = "https://public.cyber.mil/stigs/ns"
C0_NS = "http://comply0.com/ns/oscal"

TARGET = {
    "title": "Ubuntu 24.04 LTS",
    "why": ("One target, so the only thing that changes between the three "
            "columns is the modelling. Ubuntu because both rules are published "
            "for it, by DISA, and a reader can check them."),
}

#  The check identifier is the XCCDF Rule id, and it is the same string in all
#  three approaches. A reader following one check across the columns is
#  following one identifier, and it is the publisher's own rather than a label
#  invented here. The benchmark id is what a bulk runner executes in one go.
BENCHMARK_ID = "CAN_Ubuntu_24-04_STIG"

#  One timestamp for every block that carries one, so two encodings of the same
#  run never disagree about when it happened.
COLLECTED = "2026-08-20T12:00:00Z"

RULES = [
    {
        "key": "data-at-rest",
        "label": "Rule 1, data at rest",
        "statement": ("Ubuntu 24.04 LTS handling data requiring data-at-rest "
                      "protections must employ cryptographic mechanisms to "
                      "prevent unauthorized disclosure and modification of the "
                      "information at rest."),
        "control": "sc-28",
        "stig": {"group": "V-270747", "rule": "SV-270747r1066730_rule",
                 "id": "UBTU-24-600090", "severity": "medium", "category": "CAT II"},
        "check_id": "SV-270747r1066730_rule",
        "rule_id": "ubtu24_data_at_rest_encrypted",
        "param": None,
        "n": "1",
        "check_prose": ("Verify the block device carrying user data is encrypted. "
                        "If it is not, this is a finding."),
        "fix_prose": "Encrypt the block device carrying user data.",
        "claim": ("User data is held on an encrypted volume, and the key is held "
                  "in the organisation's key management service."),
        "why_chosen": ("A binary condition with no value to set. It is the "
                       "simple case, and it is the one all three approaches "
                       "already have an analogue for."),
    },
    {
        "key": "password-min-length",
        "label": "Rule 2, minimum password length",
        "statement": ("Ubuntu 24.04 LTS must enforce a minimum 15-character "
                      "password length."),
        "control": "ia-5.1",
        "stig": {"group": "V-270732", "rule": "SV-270732r1066685_rule",
                 "id": "UBTU-24-400320", "severity": "medium", "category": "CAT II"},
        "check_id": "SV-270732r1066685_rule",
        "rule_id": "ubtu24_password_min_length",
        "param": {"id": "password_min_length", "label": "Minimum password length",
                  "value": "15"},
        "n": "2",
        "check_prose": ("Verify the configured minimum password length is 15 or "
                        "greater. If it is not, this is a finding."),
        "fix_prose": "Set the minimum password length to 15.",
        "claim": ("Password policy is enforced centrally and sets a minimum "
                  "length of 15 characters."),
        "why_chosen": ("The same shape as the first rule but carrying a value, "
                       "so it is the rule that shows where each approach puts a "
                       "parameter. Publishers disagree on the number, which is "
                       "why the number has to live somewhere addressable."),
    },
]


# --------------------------------------------------------------------------- #
# Where each answer lives                                                      #
#                                                                              #
# Every block opens with the OSCAL model it belongs to, which is the same word #
# the MODEL row above it shows. A bare assembly is not self-identifying:       #
# {uuid, title, props, steps} could be almost anything, and a reader should    #
# not have to infer the document they are looking at. These put each answer    #
# back in the shortest real path to it.                                        #
# --------------------------------------------------------------------------- #

def _lst(x):
    return x if isinstance(x, list) else [x]


def in_catalog(controls):
    return {"catalog": {"groups": [{
        "id": "ubuntu-24-04",
        "title": TARGET["title"],
        "controls": _lst(controls),
    }]}}


def in_cdef(components):
    return {"component-definition": {"components": _lst(components)}}


def in_plan(activities):
    return {"assessment-plan":
            {"local-definitions": {"activities": _lst(activities)}}}


def in_plan_subjects(subjects):
    return {"assessment-plan": {"assessment-subjects": _lst(subjects)}}


def in_plan_assets(platforms):
    return {"assessment-plan":
            {"assessment-assets": {"assessment-platforms": _lst(platforms)}}}


def in_mapping(body):
    return {"mapping-collection": body}


def in_ssp(reqs):
    return {"system-security-plan":
            {"control-implementation": {"implemented-requirements": _lst(reqs)}}}


def in_results_findings(findings):
    return {"assessment-results": {"results": [{"findings": _lst(findings)}]}}


def in_results_finding_and_observation(pair):
    """A finding and the observation it rests on, in one result.

    The finding says whether the objective was met. The observation says what
    was examined, by what method and when. Split across two blocks a reader has
    to take the join on trust, so they are shown together.
    """
    #  One of each, or a list of each: question 6b shows the pair for one rule
    #  and question 5 shows what the run wrote for both.
    finding, observation = pair
    return {"assessment-results": {"results": [{
        "findings": _lst(finding), "observations": _lst(observation)}]}}


def in_results_observations(obs):
    return {"assessment-results": {"results": [{"observations": _lst(obs)}]}}


#  One wrapper per cell, so the model a block opens with is declared in exactly
#  one place and cannot drift from the MODEL row the page renders.
WRAP = {
    ("1", "catalog-first"): in_catalog,
    ("1", "component-first"): in_cdef,
    ("1", "assessment-first"): in_plan,
    ("2", "catalog-first"): in_mapping,
    ("2", "component-first"): in_cdef,
    ("2", "assessment-first"): lambda body: {"assessment-plan": body},
    ("3", "catalog-first"): in_cdef,
    ("3", "component-first"): in_cdef,
    ("3", "assessment-first"): in_plan,
    ("4", "catalog-first"): in_ssp,
    ("4", "component-first"): in_ssp,
    ("4", "assessment-first"): lambda body: {"assessment-plan": body},
    ("5", "catalog-first"): in_cdef,
    ("5", "component-first"): in_cdef,
    ("5", "assessment-first"): lambda body: {"assessment-plan": body},
    ("6a", "catalog-first"): in_ssp,
    ("6a", "component-first"): in_ssp,
    ("6a", "assessment-first"): lambda body: {"assessment-plan": body},
    ("6b", "catalog-first"): in_results_finding_and_observation,
    ("6b", "component-first"): in_results_observations,
    ("6b", "assessment-first"): in_results_finding_and_observation,
}


def catalog_q1(r):
    """The rule as a control: an id, a statement, and the check named on it.

    The published shape carries three more properties on the control itself,
    SeverityLabel, TriggerType and EvaluatedServices, and this encoding used to
    carry them too. They are gone, on the call recorded in the conversation.

    None of the three is doing work that question 1 asks about. The question is
    where the rule is written down and what it says must be true, and the answer
    to that is the id, the statement, and the part that names the check. The
    other three describe how one publisher's engine schedules and scopes a run:
    Periodic and Ubuntu24 are facts about a service rather than about the
    requirement, and severity is already carried on the assessment-first
    encoding of the same rule, from the publisher's own STIG properties.

    The encoding still rests on a property, so the cell is right to say so:
    TechnicalControlId, on the assessment-method part, is the whole of how a
    control reaches its check here.
    """
    parts = [
        {"name": "statement", "prose": r["statement"]},
        {"name": "assessment-method", "title": r["check_id"],
         "props": [{"name": "TechnicalControlId", "ns": AWS_NS,
                    "value": r["check_id"], "class": "config-rule"}]},
    ]
    ctl = {"id": r["stig"]["id"], "title": r["label"].split(", ", 1)[1].capitalize(),
           "parts": parts}
    if r["param"]:
        ctl["params"] = [{"id": r["param"]["id"], "label": r["param"]["label"],
                          "values": [r["param"]["value"]]}]
        #  The statement inserts the parameter rather than repeating its value.
        #  Written out as a number it read as tailorable while a profile
        #  set-parameter would have left the requirement text still saying
        #  fifteen, which is the failure the insert exists to prevent and is
        #  the thing the catalog page claims this encoding does not have.
        ctl["parts"][0] = {
            "name": "statement",
            "prose": r["statement"].replace(
                r["param"]["value"] + "-character",
                "{{ insert: param, " + r["param"]["id"] + " }}-character"),
        }
        ctl["parts"].insert(0, {"name": "overview", "prose":
            "The required length is a parameter of the control, so tailoring it "
            "is a profile edit rather than a change to the requirement."})
    return ctl


def component_q1(r):
    """The rule as a first-class rules entry on the component it applies to."""
    rule = {"id": r["rule_id"], "description": r["statement"]}
    if r["param"]:
        rule["description"] = (
            "Passwords must be at least {param: " + r["param"]["id"] + "} characters.")
        rule["params"] = [{"id": r["param"]["id"], "label": r["param"]["label"]}]
    comp = {
        "uuid": uid("component-" + r["key"]),
        "type": "operating-system",
        "title": TARGET["title"],
        "description": TARGET["title"] + " as a component of the system.",
        "rules": [rule],
    }
    #  No control implementation here, and so no value for the parameter.
    #
    #  The parameterised rule used to carry one, to show where the value is set.
    #  Setting a value means an implemented requirement, because that is what a
    #  control implementation requires, and an implemented requirement names a
    #  control and the rule that implements it. So question 1, which asks only
    #  where the rule is written down, was answering question 2 as well, and
    #  doing it one question early: a reader met control-id and
    #  implementing-rules before the question about the tie to a control had
    #  been put.
    #
    #  The declaration stays, which is question 1's whole answer for a rule
    #  carrying a value: the rule names its parameter and gives it a label. The
    #  value moves to question 2, onto the control implementation that was
    #  already there, which is the construct that scopes it.
    return comp


def assessment_q1(r):
    """The rule as an activity: an identifier, and what must be true.

    Six properties came off this: method, the three STIG identifiers, severity
    and category. Every one of them is real, and the conversion that produced
    this corpus writes all six. They are gone from the encoding because none of
    them answers question 1, and between them they were two thirds of the block:
    a reader looking for where the rule is written down was reading a namespace
    six times before reaching the requirement.

    Two of the six had a further problem. Severity is on the XCCDF rule, but
    category is not: CAT I, II and III are DISA's presentation of the same
    severity, so the block was carrying one fact twice. And method is core
    OSCAL rather than an extension, so it is the one of the six that has a home
    already.

    Where the other four should live is not settled, and pretending otherwise by
    quietly dropping them would be worse than the clutter. The open questions
    page asks it, with the field counts from both corpora behind it.
    """
    s = r["stig"]
    return ({
        "uuid": uid("activity-" + r["key"]),
        "title": s["group"] + ": " + r["statement"],
        "steps": [
            {"uuid": uid("step-check-" + r["key"]),
             "title": "Check: " + r["statement"],
             "props": [{"name": "check", "value": r["check_id"], "ns": C0_NS}]},
        ],
    })


# --------------------------------------------------------------------------- #
# Question 2: how the rule ties to a control                                   #
# --------------------------------------------------------------------------- #

def catalog_q2(rules):
    """A mapping document of its own, and the whole document, because that is
       the cost. mapping-collection requires metadata and a provenance block of
       four fields before a single map is written, and both ends of a map must
       be a control or a statement: the model cannot point at a rule."""
    return {
        "uuid": uid("00000000e001"),
        "metadata": {
            "title": ("Ubuntu 24.04 LTS product catalog mapped to "
                      "NIST SP 800-53 Revision 5"),
            "last-modified": COLLECTED,
            "version": "1.0.0",
            "oscal-version": "1.2.2",
        },
        "provenance": {
            "method": "human",
            "matching-rationale": "semantic",
            "status": "draft",
            "mapping-description": ("Each hardening control is narrower than the "
                                    "framework control it supports, so every map "
                                    "below is a subset relationship."),
        },
        "mappings": [{
            "uuid": uid("00000000e002"),
            "source-resource": {"type": "catalog",
                                "href": "#ubuntu-24-04-product-catalog"},
            "target-resource": {"type": "catalog", "href": "#nist-800-53-rev5"},
            "maps": [
                {"uuid": uid("map-" + r["key"]),
                 "relationship": "subset-of",
                 "matching-rationale": "semantic",
                 "sources": [{"type": "control", "id-ref": r["stig"]["id"]}],
                 "targets": [{"type": "control", "id-ref": r["control"]}]}
                for r in rules
            ],
        }],
        "back-matter": {"resources": [
            {"uuid": uid("00000000e003"),
             "title": "Ubuntu 24.04 LTS product catalog",
             "rlinks": [{"href": "./ubuntu-24-04-catalog.json"}]},
            {"uuid": uid("00000000e004"),
             "title": "NIST SP 800-53 Revision 5",
             "rlinks": [{"href": "./NIST_SP-800-53_rev5_catalog.json"}]},
        ]},
    }


def component_q2(rules):
    """No second document. The component that carries the rules carries the tie
       as well, and an implemented requirement names the control and the rule at
       the same time.

       The value of a rule's parameter is set here too, on the same control
       implementation. It sat on question 1 until a reader pointed out that
       question 1 was therefore showing an implemented requirement, and so
       answering the question about the control tie before it had been put.
       Here it is in its own place: setting a value is scoped to a control
       implementation, which is the construct this question is about."""
    ci = {
        "uuid": uid("00000000f001"),
        "source": "trestle://profiles/nist_800_53_rev5/profile.json",
        "description": "NIST SP 800-53 Revision 5",
    }
    params = [{"param-id": r["param"]["id"], "values": [r["param"]["value"]]}
              for r in rules if r["param"]]
    if params:
        ci["set-parameters"] = params
    ci["implemented-requirements"] = [
        {"uuid": uid("ir-" + r["key"]),
         "control-id": r["control"],
         "implementing-rules": [{"rule-id": r["rule_id"]}]}
        for r in rules
    ]
    return {
        "uuid": uid("000000000001"),
        "type": "operating-system",
        "title": TARGET["title"],
        "control-implementations": [ci],
    }


def assessment_q2(rules):
    """Two levels: the plan scopes, the activity targets within that scope.

    reviewed-controls is required on an assessment plan and says which controls
    the assessment may touch at all. related-controls on an activity names the
    ones that activity is for, and a consumer reads it against the outer scope.

    The distinction matters for what this site says about question 2. The tie
    from a rule to a control is optional here, and an activity can carry none.
    The plan's declaration of the controls under review is not optional, so an
    approach that puts rules in an assessment plan is committed to naming a
    control scope whether or not any rule is tied to anything.
    """
    return {
        "reviewed-controls": {"control-selections": [{
            "description": "The controls this assessment may touch.",
            "include-controls": [{"control-id": r["control"]} for r in rules],
        }]},
        "local-definitions": {"activities": [
            {"uuid": uid("activity-" + r["key"]),
             "title": r["stig"]["group"] + ": " + r["statement"],
             "related-controls": {"control-selections": [{
                 "description": ("NIST SP 800-53 controls associated with this "
                                 "STIG rule, derived from its CCI references."),
                 "include-controls": [{"control-id": r["control"]}],
             }]}}
            for r in rules
        ]},
    }


# --------------------------------------------------------------------------- #
# Question 3: how the rule is tested                                           #
# --------------------------------------------------------------------------- #

def catalog_q3(r):
    """The check is a software component whose title is the identifier the
       control's assessment-method part named, and whose ConfigRuleId prop
       carries the identifier the engine is actually handed.

       Both halves matter, and an earlier version of this encoding carried only
       the first, which made the construct sentence on the page promise a prop
       the encoding did not have. The publisher's own components spell the name
       twice: the title in lower kebab, matching the control's
       TechnicalControlId exactly, and ConfigRuleId in upper snake, which is
       what the runner takes. Two spellings of one name, tied by string
       equality rather than by a reference the schema can follow, which is the
       whole point question 3 is asking about here."""
    return {
        "uuid": uid("sw-component-" + r["key"]),
        "type": "software",
        "title": r["check_id"],
        "description": "Config rule that evaluates " + r["stig"]["id"] + ".",
        #  One property: the identifier the engine is handed.
        #
        #  The published component carries two more, an asset-type of
        #  automated-inspection and a ResourceType naming the CloudFormation
        #  type of the thing inspected, and this encoding carried both for a
        #  while. Neither answers question 3. The question is what the test is
        #  and how it is reached from the rule, and the answer is the title
        #  matching the control's TechnicalControlId and this value being what
        #  runs. What kind of asset it is and what resource it inspects are
        #  facts about the subject, which is question 4.
        "props": [
            {"name": "ConfigRuleId", "ns": AWS_NS,
             "value": r["check_id"].upper().replace("-", "_")},
        ],
        "control-implementations": [{
            "uuid": uid("sw-ci-" + r["key"]),
            "source": "#ubuntu-24-04-product-catalog",
            "description": "Ubuntu 24.04 LTS product catalog",
            "implemented-requirements": [{
                "uuid": uid("sw-ir-" + r["key"]),
                "control-id": r["stig"]["id"],
                "description": "This Config rule evaluates the control.",
            }],
        }],
    }


def validation_component(rules):
    """The one component of type validation, carrying the checks named.

    Question 3 asks how a rule is tested and shows it with one check; question 5
    asks what the run reads and shows it with both. Same document, two slices,
    so it is built once: two encodings of one file that disagreed on whether it
    had a description or a method prop were saying there were two files.
    """
    return {
        "uuid": uid("0000000b001"),
        "type": "validation",
        "title": "Ansible check runner",
        "description": "Runs the checks for the Ubuntu 24.04 LTS rules.",
        "props": [{"name": "method", "value": "TEST"}],
        "checks": [{
            "id": r["check_id"],
            "description": "Evaluates " + r["rule_id"] + " on the target host.",
            "rule-id": r["rule_id"],
            "target-component-uuid": uid("component-" + r["key"]),
        } for r in rules],
    }


def component_q3(r):
    """A component of type validation, one per runner engine, each naming the
       checks it runs and the component whose rule each check verifies."""
    return validation_component([r])


def assessment_q3(r):
    """The check named on a step, shown inside the activity that holds it.

    Both assemblies are in play and the approach can use either: a check prop on
    the step addresses one item, the same prop on the activity addresses
    everything beneath it. Showing the steps alone hid the activity, and with it
    the fact that there is a choice here at all.
    """
    return ({
        "uuid": uid("activity-" + r["key"]),
        "title": r["stig"]["group"] + ": " + r["statement"],
        "props": [{"name": "method", "value": "TEST"}],
        "steps": [
            {"uuid": uid("step-check-" + r["key"]),
             "title": "Check: " + r["statement"],
             "description": r["check_prose"],
             "props": [{"name": "check", "value": r["check_id"], "ns": C0_NS}]},
        ],
    })


# --------------------------------------------------------------------------- #
# Question 4: what the check runs against. Rule-independent.                   #
# --------------------------------------------------------------------------- #

#  The two implementation approaches answer this from the plan of record, and
#  they answer it the same way, because OSCAL gives them one way to answer.
#
#  A control response in a system security plan is a by-component. It names a
#  component and takes no subject of its own, so the thing a check is recorded
#  against is a component and never a host. One boundary whose machines differ
#  in configuration has one response covering all of them, and the response
#  cannot say which machine it was true of.
#
#  That is a limitation of the model rather than of either approach, which is
#  why both encodings below are the same shape and why the difference between
#  the columns shows up somewhere else: component-first can say which rule the
#  response rests on, and catalog-first cannot.

def in_ssp_by_component(rule_id=None):
    """A control response in the plan of record, which is a by-component."""
    bc = {
        "uuid": uid("ssp-subj-bc" + (rule_id or "")),
        "component-uuid": uid("000000000001"),
        #  A plain statement. The description carried the consequence, that a
        #  by-component takes no subject and is the finest thing the plan of
        #  record can name, which is the risk on the approach page and not
        #  something a response says about itself.
        "description": "The rule was implemented.",
    }
    if rule_id:
        bc["implementing-rules"] = [{"rule-id": rule_id}]
    return {
        "uuid": uid("ssp-subj-ir" + (rule_id or "")),
        "control-id": "UBTU-24-600090",
        "by-components": [bc],
    }


def catalog_q4(_):
    #  No rule named. The response points at a component and at a control, and
    #  there is nothing in a released by-component that names which rule it
    #  answers.
    return in_ssp_by_component()


def component_q4(_):
    #  The same shape, plus the proposed implementing-rules, which is the one
    #  thing this approach adds here: the response says which rule it rests on.
    return in_ssp_by_component(RULES[0]["rule_id"])


def component_q4_assessor(_):
    """The same component definition, copied into the assessor's own plan.

    An assessor who holds the component definition the system owner used can
    carry it into the assessment plan as an assessment asset, and the checks
    travel with the component that runs them. Each check names the component it
    tests through target-component-uuid, which is how a subject is named from
    the assessor's side rather than the owner's.

    This is the shape the component-first corpus already publishes: its
    assessment plan carries validation components under assessment-assets, each
    holding checks with a rule-id and a target-component-uuid.

    It matters because hardening guidance publishers and technology providers
    publish secure configuration guidance openly, so the definition an assessor
    needs can be a public document rather than one the system owner has to hand
    over. The catalog approach has no equivalent: an assessor cannot introduce a
    catalog into an assessment, so what is assessed is whatever the plan of
    record already selected.
    """
    return {
        "assessment-assets": {
            "components": [{
                "uuid": uid("0000000b001"),
                "type": "validation",
                "title": "Ansible check runner",
                "description": ("Copied from the component definition the "
                                "system owner used."),
                "status": {"state": "operational"},
                "checks": [
                    {"id": r["check_id"],
                     "description": "Evaluates " + r["rule_id"] + ".",
                     "rule-id": r["rule_id"],
                     "target-component-uuid": uid("000000000001")}
                    for r in RULES
                ],
            }],
        },
    }


def assessment_q4(_):
    """Scope, then target. The plan says which subjects are in play at all, and
    each activity is aimed at some of them.

    Both name an inventory item, which is an instance rather than a class. That
    is the whole of the difference from the two implementation approaches: a
    control response is a by-component and reaches the component a hundred
    machines share, and this reaches one of the hundred.
    """
    return {
        "assessment-subjects": [{
            "type": "inventory-item",
            "description": "The instances this assessment may touch.",
            "include-subjects": [{
                "subject-uuid": uid("00000000aa01"),
                "type": "inventory-item",
            }],
        }],
        "tasks": [{
            "uuid": uid("0000000ae01"),
            "type": "action",
            "title": "Assess Ubuntu 24.04 LTS",
            "associated-activities": [{
                "activity-uuid": uid("activity-" + RULES[0]["key"]),
                "subjects": [{
                    "type": "inventory-item",
                    "include-subjects": [{
                        "subject-uuid": uid("00000000aa01"),
                        "type": "inventory-item",
                    }],
                }],
            }],
        }],
    }


#  There was a second block here, the inventory item in the plan of record that
#  the assessment plan points at, carrying a property that made the instance
#  addressable to a runner. It is gone.
#
#  The property was named machine-context, which came off a slide rather than
#  out of a file. It does exist under that name, once, on an inventory item in
#  Pattern-Library-main/summit/system-security-plan/summit_system_ssp.json,
#  which is a body of content this site declares nowhere: not in provenance, not
#  in sources, not in any snippet. An encoding resting on a corpus the site does
#  not admit holding is worse than no encoding.
#
#  It also put a PROP badge on a cell whose visible block has no property in it,
#  because the mechanism is declared per cell and the property was in the second
#  block. That was reported from the page before the provenance was.


# --------------------------------------------------------------------------- #
# Question 5: what performs the check. Rule-independent.                       #
# --------------------------------------------------------------------------- #

def catalog_q5(_):
    """What the run reads on the implementor's path: the check components.

    The same components question 3 shows, one per rule, each carrying the
    identifier the engine is handed and the control implementation that ties it
    to what it evaluates. That identifier is where OSCAL stops: no component of
    type validation, no assessment platform and no prop naming an executor is
    published, so what runs it is never named.
    """
    return [catalog_q3(r) for r in RULES]


def catalog_q5_out(_):
    """What the run produces: a response saying the control is implemented.

    A by-component, one per rule, against the product control. It states that
    the control is met and nothing more. There is no field on it naming the
    check that produced it, so a reader of the plan of record cannot get from
    the response back to the run: the two are joined by whoever wrote them and
    by nothing a schema can follow. That is the difference this path has from
    the same path in the component approach, and it is the whole of it.
    """
    return [catalog_q6a(r) for r in RULES]


def component_q5(_):
    """What the run reads: the checks, on the component that runs them.

    The same component question 3 shows, with both checks rather than one. Each
    names the rule it tests and the component it tests it against, so what the
    engine is handed is complete.
    """
    return validation_component(RULES)


def component_q5_out(_):
    """What the run produces on the implementor's path: an assertion in the
    plan of record, carrying the rule it rests on.

    This is the same by-component the claim question shows, and it is here for
    a different reason: there it answers where the claim is written, here it is
    the output of a run. The proposed implementing-rules is what makes it that
    rather than prose about it, because a reader can get from the assertion back
    to the check that produced it without leaving OSCAL.
    """
    #  Both rules, because both checks ran. One implemented requirement each,
    #  and the tie back to the rule on each of them, which is the thing this
    #  path produces that the catalog approach cannot.
    return [component_q6a(r) for r in RULES]


def component_q5_assessor_out(_):
    """What the same run produces on the assessor's path: an observation.

    The check identifier is the join. It is the same string the validation
    component gave the check, so the observation resolves back to what ran
    without the assessor holding the plan of record. The subject is a host,
    which is what an assessor can say and a by-component cannot.
    """
    return [component_q6b(r) for r in RULES]


def assessment_q5(_):
    """What the run reads on the assessor's path: the checks, and what runs
    them, in one plan.

    The activity carries the check as its first step and the assets name the
    platform and the plugin beneath it. Both halves are in the document the
    assessor owns, which is why this path needs nothing from the party being
    assessed.
    """
    r = RULES[0]
    return {
        "local-definitions": {"activities": [{
            "uuid": uid("activity-" + r["key"]),
            "title": r["stig"]["group"] + ": " + r["statement"],
            "steps": [{
                "uuid": uid("step-check-" + r["key"]),
                "title": "Check: " + r["statement"],
                "props": [{"name": "check", "value": r["check_id"], "ns": C0_NS}],
            }],
        }]},
        "assessment-assets": {
            "components": [{
                "uuid": uid("0000000ad01"),
                "type": "validation",
                "title": "The check runner plugin",
                "description": "Runs the checks for the "
                               + TARGET["title"] + " rules.",
                "status": {"state": "operational"},
                "props": [{"name": "context", "ns": C0_NS,
                           "value": json.dumps({"plugin-path": "runner.plugin",
                                                "opa-path": "/usr/local/bin"})}],
            }],
            "assessment-platforms": [{
                "uuid": uid("0000000ap01"),
                "title": "The scanning platform",
                "uses-components": [{"component-uuid": uid("0000000ad01")}],
            }],
        },
        #  The third link. The assets say what exists; the task says which of
        #  them runs this activity, in a prop, which is the only place the
        #  binding is made.
        "tasks": [{
            "uuid": uid("0000000at01"),
            "type": "action",
            "title": "Execute the checks",
            "props": [{"name": "assessment-platform", "ns": C0_NS,
                       "value": uid("0000000ap01")}],
            "associated-activities": [{
                "activity-uuid": uid("activity-" + r["key"]),
                "subjects": [{"type": "inventory-item",
                              "include-all": {}}],
            }],
        }],
    }


def assessment_q5_out(_):
    """What the run produces: an observation naming the activity that ran.

    The subject is the activity itself, which is the tightest of the three
    ties: the thing observed is the thing planned. No plan of record has to
    exist for this to resolve.
    """
    #  Both halves, because both are what the run writes and question 6b shows
    #  the same pair. The finding aims at the control objective; the observation
    #  under it names the activity that ran.
    return ([assessment_q6b(r)[0] for r in RULES],
            [assessment_q6b(r)[1] for r in RULES])



def catalog_q6a(r):
    return {
        "uuid": uid("ssp-ir-" + r["key"]),
        "control-id": r["stig"]["id"],
        "statements": [{
            "statement-id": r["stig"]["id"] + "_smt",
            "uuid": uid("ssp-stmt-" + r["key"]),
            "by-components": [{
                "component-uuid": uid("000000000001"),
                "uuid": uid("ssp-bc-" + r["key"]),
                "description": r["claim"],
            }],
        }],
    }


def component_q6a(r):
    """The same shape, against the framework control, and carrying the tie back
       to the rule. The proposal extends by-component with implementing-rules,
       so the claim and the rule it rests on travel together."""
    d = catalog_q6a(r)
    d["control-id"] = r["control"]
    d["statements"][0]["statement-id"] = r["control"] + "_smt.a"
    d["statements"][0]["by-components"][0]["implementing-rules"] = [
        {"rule-id": r["rule_id"]}]
    return d


def assessment_q6a(_):
    """Not the claim, but where the claim lives.

    The plan writes no claim of its own. What it does is name the system
    security plan that holds one, through import-ssp resolving to a back-matter
    resource, and the published plans carry a second resource for the case where
    no OSCAL system security plan exists at all: a prose description of the
    system, so the assessment still has something to say the system is.
    """
    return {
        "import-ssp": {"href": "#" + uid("ssp-resource")},
        "back-matter": {"resources": [
            {"uuid": uid("ssp-resource"),
             "title": TARGET["title"] + " system security plan",
             "props": [{"name": "type", "value": "oscal-ssp"}],
             "rlinks": [{"href": "system-security-plan.json",
                         "media-type": "application/oscal.ssp+json"}],
             "remarks": "Use this to point to an OSCAL-based SSP."},
            {"uuid": uid("no-ssp-resource"),
             "title": "System's full name",
             "description": ("Use this resource when no OSCAL-based SSP exists. "
                             "Briefly describe the system. This appears in the "
                             "assessment result."),
             "props": [{"name": "type", "value": "no-oscal-ssp"}],
             "remarks": "Only include this resource if no OSCAL-based SSP is available."},
        ]},
    }


# --------------------------------------------------------------------------- #
# Question 6b: how an assessment records the outcome                           #
# --------------------------------------------------------------------------- #

def catalog_q6b(r):
    """A finding, and the observation it rests on.

    The finding used to be shown alone, relating to an observation uuid that
    nothing in this column wrote. A result whose related-observation resolves
    nowhere is not a result, so the observation is here too, and what it cannot
    carry is the point: there is no field on it naming the check that ran, so
    the outcome and the test are joined outside OSCAL.
    """
    return {
        "uuid": uid("finding-" + r["key"]),
        "title": "Result for " + r["stig"]["id"],
        "target": {
            "type": "statement-id",
            "target-id": r["stig"]["id"] + "_smt",
            "status": {"state": "satisfied"},
        },
        "related-observations": [{
            "observation-uuid": uid("observation-" + r["key"]),
        }],
    }, {
        "uuid": uid("observation-" + r["key"]),
        "title": "Observation for " + r["stig"]["id"],
        "description": "The configuration rule was evaluated on the component.",
        "methods": ["TEST"],
        "collected": COLLECTED,
    }


def component_q6b(r):
    return {
        "uuid": uid("observation-" + r["key"]),
        "description": r["check_id"],
        "assessment-check-id": r["check_id"],
        "result": "pass",
        "methods": ["TEST"],
        "subjects": [{
            "subject-uuid": uid("00000000aa01"),
            "type": "inventory-item",
        }],
        "collected": COLLECTED,
    }


def assessment_q6b(r):
    """A finding targeting an objective, and the observation under it.

    finding-target.type admits statement-id and objective-id and nothing else,
    and the published result uses objective-id for every one of its findings.
    Both are control-derived, which is the point: even the approach that writes
    no system security plan has to aim its finding at something the control
    layer defines. The observation is what makes the finding checkable: it names
    the activity that ran, the method, and when it was collected.
    """
    #  catalog_q6b returns the pair now, and what this reshapes is the finding.
    finding = catalog_q6b(r)[0]
    finding["target"]["type"] = "objective-id"
    finding["target"]["target-id"] = r["control"] + "_obj"
    observation = {
        "uuid": uid("observation-" + r["key"]),
        "title": "Observation: " + r["check_id"],
        "types": ["finding"],
        "methods": ["TEST"],
        "subjects": [{
            "type": "assessment-activity",
            "subject-uuid": uid("activity-" + r["key"]),
        }],
        "collected": COLLECTED,
    }
    return finding, observation




def assessment_q3_bulk(rules):
    """Both checks named once, on the activity, for a bulk runner.

    The same two checks as the per-step blocks above, moved up one level. A
    runtime that cannot address a single item takes one invocation and runs
    everything beneath it, and the placement of the prop is what records which
    kind of runner the plan was written for.
    """
    return {
        "uuid": uid("activity-bulk"),
        "title": "Assess " + TARGET["title"],
        "props": [
            {"name": "method", "value": "TEST"},
            {"name": "check", "value": BENCHMARK_ID, "ns": C0_NS},
        ],
        "steps": [
            {"uuid": uid("bulk-step-" + r["key"]),
             "title": "V-" + r["stig"]["group"][2:] + ": " + r["statement"]}
            for r in rules
        ],
    }


#  Which builder answers which question, for which approach. A cell with no
#  entry is a question the approach encodes nothing for, and the page says so.
BUILDERS = {
    "1": {"catalog-first": catalog_q1, "component-first": component_q1, "assessment-first": assessment_q1},
    "2": {"catalog-first": catalog_q2, "component-first": component_q2, "assessment-first": assessment_q2},
    "3": {"catalog-first": catalog_q3, "component-first": component_q3, "assessment-first": assessment_q3},
    "4": {"catalog-first": catalog_q4, "component-first": component_q4, "assessment-first": assessment_q4},
    "5": {"catalog-first": catalog_q5, "component-first": component_q5,
          "assessment-first": assessment_q5},
    "6a": {"catalog-first": catalog_q6a, "component-first": component_q6a, "assessment-first": assessment_q6a},
    "6b": {"catalog-first": catalog_q6b, "component-first": component_q6b, "assessment-first": assessment_q6b},
}


#  Questions 2, 4 and 5 are answered once per document rather than once per
#  rule. A mapping collection carries every map it has, a plan names its
#  subjects once, and one runner runs both checks. Splitting these per rule
#  would assert a difference that is not there.
SHARED_LABEL = {
    "2": "Both rules and their control ties",
    "4": "What the checks run against",
    "5": "What runs the checks",
}


PER_RULE = {"1", "3", "6a", "6b"}


#  Where a cell's single block is one of several paths rather than the whole
#  answer, it is keyed by the path so the page can put it under that heading.
RULE_KEY = {
    ("5", "catalog-first"): "implementor-in",
    ("5", "component-first"): "implementor-in",
    ("5", "assessment-first"): "assessor-in",
}


#  A cell inside a per-rule question can still be answered once per document.
#  Question 6a asks where the claim is. Two approaches make it once per rule.
#  The third makes no claim and instead names the document that holds one, which
#  is one pointer for the whole plan, so splitting it per rule would print the
#  same JSON twice and imply a difference that is not there.
SHARED_CELLS = {
    ("6a", "assessment-first"): "One pointer, covering both rules",
    #  Question 5 is answered once per path rather than once per rule, and the
    #  paths are the answer: one recommendation is run by an implementer to
    #  build the responses in a plan of record, and by an assessor to produce a
    #  result, and the two runs read different documents. Two approaches have
    #  one path each and the third has both, which is the finding.
    ("5", "catalog-first"): "What the run reads: the check components",
    ("5", "component-first"): "What the run reads: the checks it is handed",
    ("5", "assessment-first"): "What the run reads: the checks and the platform",
}


#  A block beyond the two rules, where an approach has a choice to make that
#  the others do not. It is labelled so a reader knows why the column is longer.
EXTRA = {
    ("4", "component-first"): [
        #  Lights the whole checks array. It was target-component-uuid, which is
        #  the field that names the subject and is the narrowest true answer,
        #  and lighting two identifiers in isolation showed the pointer without
        #  showing what was pointing. What travels with the component is the
        #  checks, each carrying an id, the rule it tests and the component it
        #  runs against, and that is the thing an assessor gains by holding the
        #  definition.
        {"rule": "assessor",
         "label": "The same component, copied into the assessor's plan",
         "shows": "The component definition carried into an assessment plan as an asset. The checks travel with the component that runs them, and each names the component it tests.",
         "focus": "checks",
         "wrap": lambda body: {"assessment-plan": body},
         "build": component_q4_assessor},
    ],
    ("5", "catalog-first"): [
        {"rule": "implementor-out",
         "label": "What the run produces: the response in the plan of record",
         "shows": ("A by-component saying the control is met. Nothing on it "
                   "names the check that produced it."),
         "focus": "by-components",
         "wrap": in_ssp,
         "build": catalog_q5_out},
    ],
    ("5", "component-first"): [
        #  The output of the implementor's run. Not a document about the rule:
        #  an assertion in the plan of record that carries the rule it rests on,
        #  which is what the proposed implementing-rules is for.
        {"rule": "implementor-out",
         "label": "What the run produces: the assertion in the plan of record",
         "shows": ("The response the run writes, carrying implementing-rules "
                   "so the assertion and its check travel together."),
         "focus": "implementing-rules",
         "wrap": in_ssp,
         "build": component_q5_out},
        #  The assessor's run reads the same checks from a document of its own.
        {"rule": "assessor-in",
         "label": "What the run reads: the same checks, in the assessor's plan",
         "shows": ("The same definition, taken into a plan the assessor owns. "
                   "The checks travel with it."),
         "focus": "checks",
         "wrap": lambda body: {"assessment-plan": body},
         "build": component_q4_assessor},
        {"rule": "assessor-out",
         "label": "What the run produces: the observation",
         "shows": ("The check identifier joins back to what ran, and the "
                   "subject is a host rather than a component."),
         "focus": ["assessment-check-id", "result"],
         "wrap": in_results_observations,
         "build": component_q5_assessor_out},
    ],
    ("5", "assessment-first"): [
        {"rule": "assessor-out",
         "label": "What the run produces: the observation",
         "shows": ("The observation names the activity that ran. No plan of "
                   "record has to exist for it to resolve."),
         "focus": ["target-id", "subject-uuid"],
         "wrap": in_results_finding_and_observation,
         "build": assessment_q5_out},
    ],
    ("3", "assessment-first"): [
        #  This block carries its own focus. The cell's is "steps", which is
        #  right for the blocks where each step holds its own check, and wrong
        #  here: the whole point of this one is that the check has moved off the
        #  steps and onto the activity above them, so lighting the steps lit
        #  everything except the thing it was drawn to show.
        {"rule": "placement",
         "label": "Multiple tests, with the check at the activity level",
         "shows": "The same two checks named on the activity instead, for a runner that executes in bulk. One invocation, every step beneath it.",
         "focus": "name=check",
         "build": assessment_q3_bulk},
    ],
}


SHOWS = {

    "1": {
        "catalog-first": "A control. The requirement is the control's statement, the check is named in an assessment-method part, and a value, where there is one, is a control parameter.",
        "component-first": "A rules entry on the component the rule applies to. The rule is first-class rather than a prop, and a value is a rule param set by the control implementation.",
        "assessment-first": "An activity. The requirement is the activity title, the work is in its steps, and the identifiers stay in the publisher's own namespace.",
    },
    "2": {
        "catalog-first": "A whole document of its own. Metadata and a four-field provenance block come before the first map, and both ends of a map must be a control or a statement.",
        "component-first": "No second document, and two ties in one place. The implemented requirement ties the component to the control, which OSCAL already does; implementing-rules ties the rule to it, which it does not.",
        "assessment-first": "Named on the activity itself. No second document and no second identifier, so nothing can fall out of step, and nothing else can reuse the tie.",
    },
    "3": {
        "catalog-first": "The check is a software component whose title is the identifier the control's assessment-method part named.",
        "component-first": "Two components, not one. The rule sits on the product; the check sits on a second component of type validation, one per engine, and reaches back by rule id and the uuid of the component the rule belongs to.",
        "assessment-first": "The steps are the check, and a check prop names it. Put that prop on the step and the plan can ask for one item; put it on the activity and one invocation covers every step beneath. The runner decides which.",
    },
    "4": {
        "catalog-first": "Every component the catalog applies to, taken together.",
        "component-first": "The components carrying the rules, named by uuid.",
        "assessment-first": "One host, named explicitly as an inventory item.",
    },
    "5": {
        "catalog-first": ("The check components the run is handed. What runs "
                          "them is never named."),
        "component-first": ("The checks the run is handed, each naming its "
                            "rule and its subject."),
        "assessment-first": ("The checks and what runs them, in one plan the "
                             "assessor owns."),
    },
    "6a": {
        "catalog-first": "A by-component response in the SSP, against the product control.",
        "component-first": "The same shape, against the framework control, and carrying implementing-rules so the claim names the rule it rests on.",
        "assessment-first": "Not the claim, but where it lives. import-ssp resolves to a back-matter resource naming the system security plan, and a second resource covers the case where no OSCAL one exists.",
    },
    "6b": {
        "catalog-first": "A finding, targeting the product control's statement.",
        "component-first": "An observation carrying the check id and its result.",
        "assessment-first": "A finding, targeting the framework control's statement.",
    },
}

#  The one thing in each encoding that answers the question.
#
#  A block is a whole document, because what is not in it is often the finding,
#  and that means the part a reader is being sent to look at arrives surrounded
#  by metadata and wrappers. Naming it here lets the page light it and leave the
#  rest as the context it is.
#
#  Declared as a key rather than a path. Every one of these resolves, most of
#  them once and a few of them twice where a block carries both rules, and every
#  match is lit: two activities each carrying a related-controls is two answers
#  to one question, not one answer and some noise. The generator fails if a key
#  matches nothing, which is what catches an encoding that has been reshaped
#  under a focus that was written for its old form.
FOCUS = {
    #  Where the rule is written down. For catalog-first that is the property
    #  naming the check, which is the only thing on the control that is not
    #  ordinary catalog furniture.
    ("1", "catalog-first"): "props",
    ("1", "component-first"): "rules",
    #  The check property, under the question about the rule, because in this
    #  approach they are not two things. The activity's title is the requirement
    #  and the step's check names the test, and no construct holds one without
    #  the other: there is no rule here that is not already a check. Lighting the
    #  title instead said the rule was the sentence, which is the half of it
    #  that is prose. The note on the cell carries the reason, because a check
    #  identifier lit under question 1 needs one.
    ("1", "assessment-first"): "props",
    #  How it reaches a control.
    ("2", "catalog-first"): "maps",
    ("2", "component-first"): "implemented-requirements",
    #  The activity-level tie. The plan-level scope above it is the
    #  other half and is named in the carrier row, not lit here:
    #  question 2 is about how a rule reaches a control, and the
    #  scope is about what the assessment may touch at all.
    ("2", "assessment-first"): "related-controls",
    #  How it reaches its test.
    ("3", "catalog-first"): "props",
    ("3", "component-first"): "checks",
    ("3", "assessment-first"): "steps",
    #  What the test runs against.
    #  The response itself, not the uuid inside it. A by-component is the
    #  whole of how a control response is made, and lighting the pointer
    #  showed which component without showing that this is the shape.
    ("4", "catalog-first"): "by-components",
    ("4", "component-first"): "by-components",
    ("4", "assessment-first"): "assessment-subjects",
    #  What performs it. Catalog-first encodes nothing here and has no block.
    ("5", "catalog-first"): "name=ConfigRuleId",
    ("5", "component-first"): "checks",
    ("5", "assessment-first"): "name=check",
    #  The claim, and the result.
    ("6a", "catalog-first"): "by-components",
    ("6a", "component-first"): "implementing-rules",
    ("6a", "assessment-first"): "import-ssp",
    ("6b", "catalog-first"): "findings",
    ("6b", "component-first"): "result",
    ("6b", "assessment-first"): "findings",
}

CLOSERS = {"{": "}", "[": "]"}


def value_end(text: str, i: int) -> int:
    """The offset just past the value starting at i.

    json.dumps with an indent is deterministic, so the text can be scanned
    rather than the object walked: balance the brackets, skip over strings so a
    brace inside one does not count, and a scalar runs to the end of its line.
    """
    while text[i] in " \n":
        i += 1
    if text[i] not in CLOSERS:
        j = text.find("\n", i)
        return len(text) if j == -1 else j
    depth, in_str = 0, False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c in CLOSERS:
            depth += 1
        elif c in ("}", "]"):
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise SystemExit("unbalanced JSON while locating a focus")


def focus_spans(text: str, key: str) -> list[list[int]]:
    """Every line span in text holding the named key and its value, 1-based.

    A key ending in ^ takes only its shallowest occurrences. An activity and the
    steps beneath it both have a title, and question 1 is about the activity:
    without this the rule's own line and the step that tests it were lit
    together, which is question 3's answer arriving one question early. Depth is
    read off the indent, which json.dumps sets deterministically, so it follows
    the document rather than being a number written here.
    """
    #  name=check addresses one object inside an array, by a value it carries
    #  rather than by a key above it. A props array holds several objects and
    #  only one of them is the answer: the bulk block's array carries method and
    #  check, and lighting the array lit a TEST that nothing was asking about.
    #  An array element has no key to name it by, so the value names it.
    #
    #  Found by indentation rather than by counting brackets, because a value
    #  can contain a brace: the catalog statement holds an insert directive
    #  written with them, and a scanner balancing braces without tracking string
    #  boundaries would close the wrong object. json.dumps lays out an indent
    #  deterministically, so the element opens on the nearest line above at two
    #  spaces less and closes on the next line at that indent.
    if "=" in key:
        kname, kval = key.split("=", 1)
        needle = f'"{kname}": "{kval}"'
        lines, out = text.split("\n"), []
        indent = lambda s: len(s) - len(s.lstrip())
        for i, line in enumerate(lines):
            if needle not in line:
                continue
            want = indent(line) - 2
            top = next(j for j in range(i, -1, -1)
                       if indent(lines[j]) == want and lines[j].rstrip().endswith("{"))
            bot = next(j for j in range(i, len(lines))
                       if indent(lines[j]) == want and lines[j].lstrip().startswith("}"))
            out.append([top + 1, bot + 1])
        return out

    shallow = key.endswith("^")
    key = key.rstrip("^")
    out, needle, i = [], f'"{key}": ', 0
    while True:
        i = text.find(needle, i)
        if i == -1:
            break
        line_start = text.rfind("\n", 0, i) + 1
        end = value_end(text, i + len(needle))
        out.append([text[:line_start].count("\n") + 1,
                    text[:end].count("\n") + 1, i - line_start])
        i = end
    if shallow and out:
        top = min(s[2] for s in out)
        out = [s for s in out if s[2] == top]
    return [s[:2] for s in out]


def add_focus(block: dict, q: str, approach: str, key: str | None = None) -> None:
    """Attach the line spans the page should light.

    The key comes from FOCUS, keyed on the question and the approach, because
    the two rules in a cell are the same shape and the same part of each answers
    the question. An extra block can override it: those exist to show a second
    arrangement of the same answer, and the part worth lighting is what moved.
    """
    key = key or FOCUS.get((q, approach))
    if not key:
        return
    #  A key can be several, where the answer is more than one field and
    #  lighting one of them tells half of it. The observation an assessor's run
    #  writes is the case: the check it ran and what came of it are two fields,
    #  and either alone is not the answer.
    keys = [key] if isinstance(key, str) else list(key)
    spans = []
    for one in keys:
        got = focus_spans(block["content"], one)
        if not got:
            raise SystemExit(
                f"q{q}/{approach}: the focus key {one!r} is not in the "
                f"encoding. The block has been reshaped under a focus written "
                f"for its old form; pick the key that answers the question now.")
        spans += got
    block["focus_key"] = key if isinstance(key, str) else ", ".join(keys)
    block["focus"] = sorted(spans)


def build():
    examples = {}
    for q, per in BUILDERS.items():
        examples[q] = {}
        for approach, fn in per.items():
            blocks = []
            wrap = WRAP.get((q, approach), lambda x: x)
            shared_label = SHARED_CELLS.get((q, approach))
            if q in PER_RULE and not shared_label:
                for r in RULES:
                    content = fn(r)
                    if content is None:
                        continue
                    blocks.append({
                        "rule": r["key"], "label": r["label"],
                        "shows": SHOWS[q][approach],
                        "content": json.dumps(wrap(content), indent=2),
                    })
                    add_focus(blocks[-1], q, approach)
            else:
                content = fn(RULES[0] if shared_label else RULES)
                if content is not None:
                    blocks.append({
                        #  Question 5 is answered once per path rather than once
                        #  per rule or once per document, and the page pairs a
                        #  block with its path by this key.
                        "rule": RULE_KEY.get((q, approach), "both"),
                        "label": shared_label or SHARED_LABEL.get(q, "Both rules"),
                        "shows": SHOWS[q][approach],
                        "content": json.dumps(wrap(content), indent=2),
                    })
                    add_focus(blocks[-1], q, approach)
            for x in EXTRA.get((q, approach), []):
                #  An extra block can name its own wrapper. The cell's wrapper
                #  is the model its main answer lives in, and an extra exists to
                #  show that answer arranged differently, which sometimes means
                #  a different document: question 4 of component-first answers
                #  from the plan of record and its extra answers from the
                #  assessor's plan.
                wrap_x = x.get("wrap") or WRAP.get((q, approach), lambda y: y)
                blocks.append({
                    "rule": x["rule"], "label": x["label"], "shows": x["shows"],
                    "content": json.dumps(wrap_x(x["build"](RULES)), indent=2),
                })
                add_focus(blocks[-1], q, approach, x.get("focus"))
            if blocks:
                examples[q][approach] = blocks
    return {
        "note": ("Our own encodings. Two rules, written in all three shapes, so the "
                 "only thing that changes between the columns is the modelling."),
        "target": TARGET,
        #  check_id is published because it is the join: the same string names
        #  the check in all three approaches, and verify.py asserts that.
        "rules": [{k: r[k] for k in ("key", "label", "statement", "control",
                                     "stig", "check_id", "why_chosen")}
                  for r in RULES],
        "benchmark_id": BENCHMARK_ID,
        "examples": examples,
    }


UUID_RE = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[45][0-9A-Fa-f]{3}"
    r"-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}$")


def check_uuids(doc) -> list:
    """Every uuid in the output, checked against the shape OSCAL requires.

    The mapping schema caught two malformed ones by hand; this catches them
    before anyone has to run a schema.
    """
    bad = []

    def walk(o, where):
        if isinstance(o, dict):
            for k, v in o.items():
                if k.endswith("uuid") and isinstance(v, str) and not UUID_RE.match(v):
                    bad.append(f"{where}/{k} = {v!r}")
                elif k.endswith("uuids") and isinstance(v, list):
                    for i, x in enumerate(v):
                        if isinstance(x, str) and not UUID_RE.match(x):
                            bad.append(f"{where}/{k}[{i}] = {x!r}")
                else:
                    walk(v, where + "/" + k)
        elif isinstance(o, list):
            for i, x in enumerate(o):
                walk(x, f"{where}[{i}]")

    for q, per in doc["examples"].items():
        for ap, blocks in per.items():
            for b in blocks:
                walk(json.loads(b["content"]), f"q{q}/{ap}/{b['rule']}")
    return bad


def main():
    doc = build()
    bad = check_uuids(doc)
    if bad:
        sys.exit("malformed uuid(s):\n  " + "\n  ".join(bad))
    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv:
        if not os.path.exists(OUT):
            sys.exit("data/pattern-examples.json is missing. Run tools/pattern_examples.py")
        if open(OUT, encoding="utf-8").read() != text:
            sys.exit("data/pattern-examples.json is stale. Run tools/pattern_examples.py")
        print("data/pattern-examples.json is current")
        return
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    n = sum(len(v) for q in doc["examples"].values() for v in q.values())
    print(f"data/pattern-examples.json  {len(doc['examples'])} question(s), {n} blocks")


if __name__ == "__main__":
    main()
