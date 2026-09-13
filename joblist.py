#!/usr/bin/env python3
"""Filter the Simplify/Pitt-CSC Summer 2027 listings into a ranked worklist.

    python3 joblist.py            # use cache if fresh, else download
    python3 joblist.py --refresh  # force re-download
    python3 joblist.py --term "Winter 2027"

Source: github.com/SimplifyJobs/Summer2027-Internships (updated daily).
"""
import json, os, sys, time, urllib.request, argparse, re

URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".listings-cache.json")
MAX_AGE_H = 12

# Bay Area / no-relocation, from RESUME-STRATEGY section 7 + section 12
LOCAL = re.compile(r"(San Jose|Santa Clara|Sunnyvale|Mountain View|Palo Alto|Menlo Park|"
                   r"Cupertino|Fremont|Milpitas|San Francisco|Redwood|Foster City|"
                   r"South San Francisco|Bay Area|Remote)", re.I)
# section 7 tier-2 target list + still-live tier-1
TARGETS = ["nvidia","cisco","intuit","workday","servicenow","adobe","palantir","roblox",
           "databricks","doordash","amazon","uber","netflix","google","figma","tiktok",
           "stripe","airbnb","linkedin","salesforce","apple","meta","microsoft","tesla",
           "snowflake","confluent","hashicorp","cloudflare","datadog","mongodb","redis"]

# section 27 role archetypes -> which prebuilt variant to attach
ROLE_RULES = [
    ("ml",      r"machine learning|\bml\b|\bai\b|deep learning|computer vision|"
                r"\bnlp\b|data scien|research scien|llm|perception|model"),
    ("infra",   r"infrastructur|platform|cloud|devops|\bsre\b|site reliab|distributed|"
                r"systems|kernel|network|storage|compute|reliability|observab"),
    ("security",r"security|identity|cryptograph|appsec|trust & safety|privacy"),
    ("backend", r"backend|back-end|server|api|database|\bdata\b|fullstack|full-stack|"
                r"full stack|web|services|application"),
]

def pick_variant(title, category):
    t = (title or "").lower()
    for name, pat in ROLE_RULES:
        if re.search(pat, t):
            return name
    if category in ("AI/ML/Data", "Data Science, AI & Machine Learning"):
        return "ml"
    return "general"


def load(refresh=False):
    if not refresh and os.path.exists(CACHE):
        age = (time.time() - os.path.getmtime(CACHE)) / 3600
        if age < MAX_AGE_H:
            print(f"cache {age:.1f}h old", file=sys.stderr)
            return json.load(open(CACHE))
    print("downloading (~12 MB)...", file=sys.stderr)
    with urllib.request.urlopen(URL, timeout=300) as r:
        data = json.loads(r.read().decode())
    json.dump(data, open(CACHE, "w"))
    return data

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--term", default="Summer 2027")
    ap.add_argument("--days", type=int, default=45, help="only postings newer than this")
    ap.add_argument("--out", default="JOB-WORKLIST.md")
    a = ap.parse_args()

    rows = load(a.refresh)
    now = time.time()
    hits = []
    for x in rows:
        if not (x.get("active") and x.get("is_visible")): continue
        if a.term not in (x.get("terms") or []): continue
        if x.get("category") not in ("Software", "Software Engineering", "AI/ML/Data",
                                     "Data Science, AI & Machine Learning"): continue
        degs = x.get("degrees") or []
        if degs and "Bachelor's" not in degs: continue
        age_d = (now - x.get("date_posted", 0)) / 86400 if x.get("date_posted") else 999
        if age_d > a.days: continue
        locs = ", ".join(x.get("locations") or [])
        co = (x.get("company_name") or "").lower()
        hits.append({
            "company": x.get("company_name",""), "title": x.get("title",""),
            "loc": locs, "url": x.get("url",""), "age": age_d,
            "local": bool(LOCAL.search(locs)),
            "target": any(t in co for t in TARGETS),
            "cat": x.get("category",""),
            "variant": pick_variant(x.get("title",""), x.get("category","")),
        })

    # rank: named target first, then local, then freshest
    hits.sort(key=lambda h: (not h["target"], not h["local"], h["age"]))

    L = [f"# Job Worklist — {a.term}", "",
         f"{len(hits)} open postings, Bachelor's-eligible, SWE/AI, posted in the last {a.days} days.",
         f"Source: SimplifyJobs/Summer2027-Internships, pulled {time.strftime('%Y-%m-%d %H:%M')}.",
         "", "Ranked: named targets first, then Bay Area, then freshest.",
         "The **Resume** column names the prebuilt variant to submit "
         "(`variants/ShayanPoigaiResume-<name>.tex`, see section 27).",
         "Regenerate with `python3 joblist.py --refresh`.", "", "---", ""]

    def section(title, items):
        if not items: return
        L.append(f"## {title} ({len(items)})"); L.append("")
        L.append("| | Company | Role | Location | Age | Resume | Link |")
        L.append("|---|---|---|---|---|---|---|")
        for h in items:
            flag = "★" if h["target"] else ("•" if h["local"] else "")
            t = h["title"][:52]
            loc = h["loc"][:30]
            L.append(f"| {flag} | {h['company']} | {t} | {loc} | {h['age']:.0f}d | `{h['variant']}` | [apply]({h['url']}) |")
        L.append("")

    section("Named targets", [h for h in hits if h["target"]])
    section("Bay Area — no relocation", [h for h in hits if not h["target"] and h["local"]])
    section("Everything else", [h for h in hits if not h["target"] and not h["local"]])

    open(a.out, "w").write("\n".join(L) + "\n")
    print(f"{len(hits)} matches -> {a.out}")
    print(f"  named targets : {sum(h['target'] for h in hits)}")
    print(f"  bay area      : {sum(h['local'] and not h['target'] for h in hits)}")
    import collections
    for k, v in collections.Counter(h["variant"] for h in hits).most_common():
        print(f"  resume/{k:9s}: {v}")

if __name__ == "__main__":
    main()
