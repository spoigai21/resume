# Resumes
general = resumes with everything

app2026 = resumes modified based on certain role requirements

## Tailoring a resume in one command

`bullets.yaml` is the bank of verified bullets, each tagged (`data`, `ml`, `backend`,
`security`, ...). `tailor.py` scores every bullet against a job description, picks the best
ones per role, orders the Languages line, builds the PDF, and drops the weakest bullets until
it fits one page.

```bash
# paste the JD into a text file, then:
python3 tailor.py WEX --jd jds/wex.txt
python3 tailor.py Intel --jd jds/intel.txt --focus cv,deployment      # force extra emphasis
python3 tailor.py Superhuman --focus fullstack,frontend --languages "JavaScript, Java, Python, SQL, C++"
python3 tailor.py --batch jobs.yaml                                   # many at once, in parallel
python3 tailor.py Acme --focus security --dry-run                     # preview the picks only
python3 tailor.py --list-tags                                         # which tags hit which bullets
```

Output: `app2026:2027/<Company>/ShayanPoigaiResume.{tex,pdf}` + `selection.json` (what was
picked, and what changed vs the general resume).

- It **refuses** when the picks are identical to the general resume (a languages-line-only
  change is not tailoring). Add `--focus` tags or pass `--allow-general`.
- Bullets marked `verify:` in the bank print a warning when selected.
- To add work: add a bullet to `bullets.yaml` with facts already in `RESUME-DETAILS.md`.
  Preamble, heading, education and the other skills lines still come from
  `ShayanPoigaiResume1.tex`.
- Needs PyYAML (`python3 -m pip install pyyaml`) and pypdf for the parse check; point the
  build at a Python that has pypdf with `PYTHON=/path/to/python`. Builds use Docker
  (`resume-tex:1`, see `build_resume.sh`).
