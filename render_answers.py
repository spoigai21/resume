#!/usr/bin/env python3
"""Render APPLICATION-ANSWERS.md from application-answers.json.

The JSON is the source of truth. Never hand-edit the markdown - regenerate it,
so the two can't drift.
"""
import json, datetime

d = json.load(open("application-answers.json"))
L = []
w = L.append

w("# Application Answer Bank")
w("")
w("**Generated** from `application-answers.json` by `render_answers.py` — "
  "do not hand-edit. Edit the JSON and re-run.")
w("")
w(f"*Last generated: {datetime.date.today().isoformat()}*")
w("")
w("> Contains PII. Gitignored. Never commit, never paste into a public tool.")
w("")
w("---")
w("")

def table(rows):
    w("| Field | Answer |")
    w("|---|---|")
    for k, v in rows:
        w(f"| {k} | {v} |")
    w("")

i = d["identity"]
w("## Identity")
w("")
table([
    ("Legal first name", i["legal_first_name"]),
    ("Legal middle name", i["legal_middle_name"]),
    ("Legal last name", i["legal_last_name"]),
    ("Preferred name", i["preferred_name"]),
    ("Email", i["email"]),
    ("Phone", i["phone"]),
    ("Phone (E.164)", i["phone_e164"]),
    ("Street address", f'{i["street_address"]}  *(only if required)*'),
    ("City", i["city"]),
    ("State", i["state"]),
    ("ZIP", i["zip"]),
    ("Country", i["country"]),
])
w(f'> **Street address:** {i["_street_address_rule"]}')
w("")
w(f'*{i["_middle_name_note"]}*')
w("")

w("## Links")
w("")
table(list(d["links"].items()))

wa = d["work_authorization"]
w("## Work authorization — the knockout block")
w("")
w(f"> {wa['_note']}")
w("")
table([
    ("Legally authorized to work in the US?", f"**{wa['authorized_to_work_us']}**"),
    ("Will you now or in the future require sponsorship?", f"**{wa['require_sponsorship_now_or_future']}**"),
    ("US citizen or national?", wa["us_citizen_or_national"]),
    ("US person under ITAR/EAR?", wa["itar_us_person"]),
    ("Visa status", wa["visa_status"]),
    ("Age 18 or over?", wa["age_18_or_over"]),
])
w(f"*{wa['_itar_note']}*")
w("")

e = d["eeo_voluntary"]
w("## EEO — voluntary self-identification")
w("")
w(f"> {e['_note']}")
w("")
table([
    ("Gender", e["gender"]),
    ("Race / ethnicity", e["race_ethnicity"]),
    (f"Disability status ({e['disability_form']})", e["disability_status"]),
    ("Veteran status", e["veteran_status"]),
])
w(f"*{e['_veteran_variants']}*")
w("")

ed = d["education"]
w("## Education")
w("")
table([
    ("School", ed["school"]), ("Location", ed["school_location"]),
    ("Degree", ed["degree"]), ("Major", ed["major"]),
    ("GPA", f"{ed['gpa']} / {ed['gpa_scale']}"),
    ("Expected graduation", ed["expected_graduation"]),
    ("As MM/YYYY", ed["expected_graduation_month_year"]),
    ("If asked as a TERM", ed["expected_graduation_alt_term"]),
    ("Currently enrolled", ed["currently_enrolled"]),
    ("Education level", ed["education_level"]),
])
w(f"> **Warning:** {ed['_grad_date_warning']}")
w("")

av = d["availability"]
w("## Availability")
w("")
for term in ("summer_2027", "winter_2027"):
    t = av[term]
    w(f"**{term.replace('_',' ').title()}** — {t['start']} to {t['end']}  ")
    w(f"*{t['_note']}*")
    w("")
table([
    ("Willing to relocate", av["willing_to_relocate"]),
    ("Willing to work on-site", av["willing_to_work_onsite"]),
    ("Hours per week", av["hours_per_week"]),
])

w("## Experience — newest first")
w("")
w("| Employer | Title | Start | End | Location |")
w("|---|---|---|---|---|")
for x in d["experience"]:
    w(f"| {x['employer']} | {x['title']} | {x['start']} | {x['end']} | {x['location']} |")
w("")

ps = d["pre_submit_audit"]
qb = d["ats_question_bank"]
w("## ATS QUESTION BANK — check here first")
w("")
w(f"> {qb['_purpose']}  \n> Seen on: {', '.join(qb['_seen_on'])}")
w("")
for sec, body in qb.items():
    if sec.startswith("_"): continue
    w(f"### {sec.replace('_',' ').title()}")
    w("")
    if isinstance(body, list):
        for x in body: w(f"- {x}")
        w("")
        continue
    for k, v in body.items():
        if k.startswith("_"):
            w(f"> **Note:** {v}")
            w("")
        else:
            w(f"- **{k}** → {v}")
    w("")

w("## PRE-SUBMIT AUDIT — run every time")
w("")
w(f"> {ps['_why']}")
w("")
w(f"**Root cause:** {ps['_root_cause']}")
w("")
for c in ps["checks"]:
    w(f"- [ ] {c}")
w("")

w("## Role descriptions — paste when the parser drops them")
w("")
for x in d["experience"]:
    if not x.get("role_description"): continue
    w(f"**{x['employer']} — {x['title']}**")
    w("")
    w("```")
    w(x["role_description"])
    w("```")
    w("")

w("## Skills (single-line paste)")
w("")
w("```")
w(d["skills_line"])
w("```")
w("")

c = d["common_questions"]
w("## Common form questions")
w("")
table([(k.replace("_", " ").capitalize(), v)
       for k, v in c.items() if not k.startswith("_")])
for k, v in c.items():
    if k.startswith("_"):
        w(f"*{v}*")
        w("")

sp = d["salary_policy"]
rp = d["resume_policy"]
w("## Resume file policy")
w("")
w(f"> **{rp['_rule']}**")
w("")
w(f"**Submit:** `{rp['submit_this']}`")
w("")
w("**Never submit:**")
for f in rp["never_submit"]:
    w(f"- `{f}`")
w("")
w(f"**Workday:** {rp['workday_upload']}")
w("")
w(f"*{rp['_parse_dependency']}*")
w("")

w("## Salary — decision tree")
w("")
w(f"> {sp['_note']}")
w("")
w("| Situation | Answer |")
w("|---|---|")
w(f"| An 'Open' / 'Negotiable' option exists | **{sp['1_if_open_option_exists']}** |")
w(f"| Required, range is posted | **{sp['2_if_required_and_range_posted']}** |")
w(f"| Required, no range posted | **${sp['3_if_required_and_no_range'].split()[0]}/hour** |")
w(f"| Not required | {sp['4_if_not_required']} |")
w("")
for k, v in sp["_examples"].items():
    w(f"- `{k}` — {v}")
w("")
w(f"*{sp['_tradeoff']}*")
w("")

w("## Active applications")
w("")
w("| Company | Req / Job ID | Role | Notes |")
w("|---|---|---|---|")
for name, a in d["active_applications"].items():
    extra = a.get("status") or a.get("season") or a.get("term") or ""
    if a.get("referral"): extra += " · referral"
    w(f"| {name.title()} | {a.get('req','—')} | {a['role']} | {extra} |")
w("")

w("## Still needed from you")
w("")
for n in d["needs_input"]:
    w(f"- [ ] {n}")
w("")

open("APPLICATION-ANSWERS.md", "w").write("\n".join(L) + "\n")
print(f"wrote APPLICATION-ANSWERS.md ({len(L)} lines)")
