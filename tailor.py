#!/usr/bin/env python3
"""Generate a JD-tailored, one-page resume from bullets.yaml.

    python3 tailor.py WEX --jd jds/wex.txt                 # tags inferred from the JD
    python3 tailor.py Intel --jd jds/intel.txt --focus cv,ml,deployment
    python3 tailor.py Superhuman --focus fullstack,frontend --languages "JavaScript, Java, Python, SQL, C++"
    python3 tailor.py --batch jobs.yaml                     # many companies, built in parallel
    python3 tailor.py --list-tags

Writes app2026:2027/<Company>/ShayanPoigaiResume.{tex,pdf} plus selection.json
(which bullets were picked and why). The preamble, heading, education and skills
lines come from ShayanPoigaiResume1.tex, so parse fixes there flow through.

Guards:
  * one page: bullets are dropped lowest-score-first until build_resume.sh passes
  * not-actually-tailored: refuses when the selected bullets are identical to the
    general resume (a skills-line-only change is not tailoring); --allow-general overrides
  * bullets marked `verify` print a warning when selected

Needs PyYAML for this script and pypdf for build_resume.sh's parse check. Point
build_resume.sh at a Python with pypdf via PYTHON=/path/to/python (default: this
interpreter).
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
BANK = ROOT / "bullets.yaml"
MASTER = ROOT / "ShayanPoigaiResume1.tex"
BUILD = ROOT / "build_resume.sh"
OUT_ROOT = ROOT / "app2026:2027"

FOCUS_WEIGHT = 8   # an explicit --focus tag outweighs any number of JD keyword hits
KEYWORD_CAP = 8    # one tag can't dominate just because a JD repeats a word


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------
def load_bank():
    return yaml.safe_load(BANK.read_text())


def strip_comments(tex):
    return "\n".join(l for l in tex.split("\n") if not l.lstrip().startswith("%"))


def master_parts():
    """Preamble, heading+education, and skills block from the master resume."""
    src = MASTER.read_text()
    pre, body = src.split("\\begin{document}", 1)
    head = body.split("%----------EXPERIENCE----------", 1)[0]
    skills = re.search(r"\\section\{Technical Skills\}.*?\\end\{itemize\}", body, re.S)
    if not skills:
        sys.exit("master resume: Technical Skills block not found")
    return pre, strip_comments(head).strip("\n"), strip_comments(skills.group(0))


def infer_weights(jd_text, bank):
    t = jd_text.lower()
    weights = {}
    for tag, kws in bank["tag_keywords"].items():
        hits = 0
        for kw in kws:
            pat = r"(?<![a-z0-9])" + re.escape(kw.lower()) + r"(?![a-z0-9])"
            hits += len(re.findall(pat, t))
        if hits:
            weights[tag] = min(hits, KEYWORD_CAP)
    return weights


def build_weights(bank, jd_text=None, focus=()):
    weights = infer_weights(jd_text, bank) if jd_text else {}
    for tag in focus:
        if tag not in bank["tag_keywords"] and not any(
            tag in b.get("tags", []) for r in bank["roles"] for b in r["bullets"]
        ):
            print(f"  warning: focus tag '{tag}' is not used by any bullet", file=sys.stderr)
        weights[tag] = weights.get(tag, 0) + FOCUS_WEIGHT
    return weights


# ---------------------------------------------------------------------------
# selection
# ---------------------------------------------------------------------------
def score(item, weights):
    return sum(weights.get(t, 0) for t in item.get("tags", []))


def rank(items, weights):
    """Best first. Ties fall back to `prior` (the general resume's ordering)."""
    return sorted(
        enumerate(items),
        key=lambda p: (score(p[1], weights), p[1].get("prior", 0), -p[0]),
        reverse=True,
    )


def pick(items, weights, limit, minimum=0):
    chosen, groups = [], set()
    ranked = [it for _, it in rank(items, weights)]
    for it in ranked:
        if len(chosen) >= limit:
            break
        g = it.get("group")
        if g and g in groups:
            continue
        # a bullet nothing asked for (score 0) and never shown by default (prior 0) stays out
        if score(it, weights) == 0 and it.get("prior", 0) == 0:
            continue
        chosen.append(it)
        if g:
            groups.add(g)
    # never render an empty section: top up to the minimum in rank order
    for it in ranked:
        if len(chosen) >= minimum:
            break
        if it not in chosen and not (it.get("group") and it.get("group") in groups):
            chosen.append(it)
            if it.get("group"):
                groups.add(it["group"])
    return chosen


def select(bank, weights, max_projects=None):
    roles = [(r, pick(r["bullets"], weights, r["max"], r["min"])) for r in bank["roles"]]
    proj_cfg = bank["projects"]
    limit = max_projects or proj_cfg["max"]
    ranked = [p for _, p in rank(proj_cfg["items"], weights)
              if score(p, weights) > 0 or p.get("prior", 0) > 0][:limit]
    projects = [(p, pick(p["bullets"], weights, p["max"], p["min"])) for p in ranked]
    return roles, projects


def languages_line(bank, weights, override):
    if override:
        return override
    names = [l["name"] for l in bank["languages"]]
    if not weights:
        return ", ".join(bank["default_languages"])
    default_pos = {n: i for i, n in enumerate(bank["default_languages"])}
    ordered = sorted(bank["languages"],
                     key=lambda l: (-score(l, weights), default_pos.get(l["name"], len(names))))
    return ", ".join(l["name"] for l in ordered)


def drop_one(roles, projects, weights, proj_min):
    """Remove the single lowest-value removable bullet/project. False if nothing can go."""
    cands = []
    for i, (r, bs) in enumerate(roles):
        if len(bs) > r["min"]:
            b = bs[-1]
            cands.append((score(b, weights), b.get("prior", 0), "role", i))
    for i, (p, bs) in enumerate(projects):
        if len(bs) > p["min"]:
            b = bs[-1]
            cands.append((score(b, weights), b.get("prior", 0), "proj", i))
    if len(projects) > proj_min:
        p, _ = projects[-1]
        cands.append((score(p, weights) - 0.5, p.get("prior", 0), "whole", len(projects) - 1))
    if not cands:
        return False
    _, _, kind, i = min(cands)
    if kind == "role":
        roles[i][1].pop()
    elif kind == "proj":
        projects[i][1].pop()
    else:
        projects.pop(i)
    return True


# ---------------------------------------------------------------------------
# rendering + build
# ---------------------------------------------------------------------------
def render(parts, roles, projects, langs):
    pre, head, skills = parts
    out = [pre.rstrip("\n"), "\\begin{document}", "% Generated by tailor.py from bullets.yaml. Edit the bank, not this file.", head, "",
           "%----------EXPERIENCE----------", "\\section{Work Experience}", "  \\resumeSubHeadingListStart", ""]
    for r, bs in roles:
        out += ["    \\resumeSubheading",
                f"      {{{r['title']}}}{{{r['dates']}}}",
                f"      {{{r['org']}}}{{}}",
                "      \\resumeItemListStart"]
        out += [f"        \\resumeItem{{{b['text']}}}" for b in bs]
        out += ["      \\resumeItemListEnd", ""]
    out += ["  \\resumeSubHeadingListEnd", "", "%----------PROJECTS----------", "\\section{Projects}",
            "    \\resumeSubHeadingListStart", ""]
    for p, bs in projects:
        out += ["      \\resumeProjectHeading",
                f"          {{{p['heading']}}}{{{p['date']}}}",
                "          \\resumeItemListStart"]
        out += [f"            \\resumeItem{{{b['text']}}}" for b in bs]
        out += ["          \\resumeItemListEnd", ""]
    out += ["    \\resumeSubHeadingListEnd", "", "%----------TECHNICAL SKILLS----------"]
    new_skills, n = re.subn(r"\\textbf\{Languages\}\{: [^}]*\}",
                            lambda m: "\\textbf{Languages}{: " + langs + "}", skills)
    if n != 1:
        sys.exit("master resume: Languages line not found")
    out += [new_skills, "", "\\end{document}", ""]
    return "\n".join(out)


def build(tex_path, pdf_path):
    env = dict(os.environ)
    env.setdefault("PYTHON", sys.executable)
    r = subprocess.run([str(BUILD), str(tex_path), str(pdf_path)], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    m = re.search(r"pages=(\d+)", r.stdout)
    return r.returncode == 0, int(m.group(1)) if m else None, (r.stdout + r.stderr).strip()


def ids(roles, projects):
    s = {b["id"] for _, bs in roles for b in bs}
    s |= {p["id"] for p, _ in projects} | {b["id"] for _, bs in projects for b in bs}
    return s


# ---------------------------------------------------------------------------
# one company
# ---------------------------------------------------------------------------
def tailor(company, bank, parts, jd_text=None, focus=(), languages=None, max_projects=None,
           allow_general=False, dry_run=False):
    log = [f"== {company}"]
    weights = build_weights(bank, jd_text, focus)
    roles, projects = select(bank, weights, max_projects)
    g_roles, g_projects = select(bank, {}, max_projects)
    langs = languages_line(bank, weights, languages)

    if ids(roles, projects) == ids(g_roles, g_projects) and not allow_general:
        return False, log + ["  REFUSED: bullet selection is identical to the general resume - "
                             "that is not tailoring. Add --focus tags (see --list-tags) or pass --allow-general."]

    top = sorted(weights.items(), key=lambda kv: -kv[1])[:10]
    log.append("  focus weights: " + ", ".join(f"{k}={v}" for k, v in top))
    out_dir = OUT_ROOT / company
    tex_path, pdf_path = out_dir / "ShayanPoigaiResume.tex", out_dir / "ShayanPoigaiResume.pdf"
    proj_min = bank["projects"]["min"]

    for attempt in range(12):
        tex = render(parts, roles, projects, langs)
        if dry_run:
            break
        out_dir.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(tex)
        ok, pages, output = build(tex_path, pdf_path)
        if ok:
            break
        if pages and pages > 1:
            if not drop_one(roles, projects, weights, proj_min):
                return False, log + ["  FAILED: still over one page with nothing left to drop"]
            continue
        return False, log + ["  BUILD FAILED:", output]
    else:
        return False, log + ["  FAILED: could not fit one page in 12 attempts"]

    chosen = ids(roles, projects)
    general = ids(g_roles, g_projects)
    for r, bs in roles:
        log.append(f"  {r['org']}: " + ", ".join(f"{b['id']}({score(b, weights)})" for b in bs))
    log.append("  projects: " + ", ".join(f"{p['id']}[{','.join(b['id'] for b in bs)}]" for p, bs in projects))
    log.append(f"  languages: {langs}")
    log.append(f"  vs general: +{sorted(chosen - general)} -{sorted(general - chosen)}")
    for _, bs in roles + projects:
        for b in bs:
            if b.get("verify"):
                log.append(f"  VERIFY: {b['id']}: {b['verify']}")

    if dry_run:
        log.append("  (dry run: nothing written)")
        return True, log

    manifest = {
        "company": company,
        "focus": list(focus),
        "weights": weights,
        "languages": langs,
        "roles": {r["id"]: [b["id"] for b in bs] for r, bs in roles},
        "projects": {p["id"]: [b["id"] for b in bs] for p, bs in projects},
        "added_vs_general": sorted(chosen - general),
        "removed_vs_general": sorted(general - chosen),
    }
    (out_dir / "selection.json").write_text(json.dumps(manifest, indent=2) + "\n")
    log.append(f"  wrote {pdf_path.relative_to(ROOT)}")
    return True, log


def read_jd(arg):
    if not arg:
        return None
    return sys.stdin.read() if arg == "-" else Path(arg).read_text()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("company", nargs="?", help="output folder name under app2026:2027/")
    ap.add_argument("--jd", help="job description text file ('-' for stdin); tags are inferred from it")
    ap.add_argument("--focus", default="", help="comma-separated tags to force (e.g. data,ml,testing)")
    ap.add_argument("--languages", help='override the Languages line, e.g. "Python, SQL, Java, JavaScript, C++"')
    ap.add_argument("--max-projects", type=int)
    ap.add_argument("--allow-general", action="store_true", help="permit a selection identical to the general resume")
    ap.add_argument("--dry-run", action="store_true", help="show the selection without writing or building")
    ap.add_argument("--batch", help="YAML list of {company, jd, focus, languages, max_projects}")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--list-tags", action="store_true")
    a = ap.parse_args()

    bank = load_bank()
    if a.list_tags:
        used = {}
        for r in bank["roles"]:
            for b in r["bullets"]:
                for t in b.get("tags", []):
                    used.setdefault(t, []).append(b["id"])
        for p in bank["projects"]["items"]:
            for t in p.get("tags", []):
                used.setdefault(t, []).append(p["id"])
        for t in sorted(used):
            print(f"{t:16s} {', '.join(used[t])}")
        return

    parts = master_parts()
    if a.batch:
        jobs = yaml.safe_load(Path(a.batch).read_text())
        def run(job):
            return tailor(job["company"], bank, parts,
                          jd_text=read_jd(job.get("jd")),
                          focus=[t.strip() for t in str(job.get("focus", "")).split(",") if t.strip()],
                          languages=job.get("languages"), max_projects=job.get("max_projects"),
                          allow_general=job.get("allow_general", False), dry_run=a.dry_run)
        with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
            results = list(ex.map(run, jobs))
        failed = 0
        for ok, log in results:
            print("\n".join(log))
            failed += not ok
        print(f"\n{len(results) - failed}/{len(results)} built")
        sys.exit(1 if failed else 0)

    if not a.company:
        ap.error("company is required (or use --batch / --list-tags)")
    if not a.jd and not a.focus:
        ap.error("give --jd and/or --focus - a resume with neither is the general resume")
    ok, log = tailor(a.company, bank, parts, jd_text=read_jd(a.jd),
                     focus=[t.strip() for t in a.focus.split(",") if t.strip()],
                     languages=a.languages, max_projects=a.max_projects,
                     allow_general=a.allow_general, dry_run=a.dry_run)
    print("\n".join(log))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
