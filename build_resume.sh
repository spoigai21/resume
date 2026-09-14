#!/usr/bin/env bash
# Compile a resume .tex with pdflatex (same engine as Overleaf) and run the
# section 4 + section 28 parse checks. Fails unless the PDF is exactly one page
# and every check passes.
#
#   ./build_resume.sh variants/ShayanPoigaiResume-ml.tex  app2026:2027/Acme/ShayanPoigaiResume.pdf
#
# Needs Docker and the local image resume-tex:1. To recreate it:
#   docker run --name restex texlive/texlive:latest-medium \
#     tlmgr install preprint titlesec marvosym enumitem fancyhdr lm babel-english
#   docker commit restex resume-tex:1 && docker rm restex
# Needs pypdf: PYTHON=/path/to/venv/bin/python ./build_resume.sh ...
set -euo pipefail

TEX="$1"; OUT="$2"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cp "$TEX" "$WORK/resume.tex"
if ! docker run --rm -v "$WORK":/w -w /w resume-tex:1 \
     pdflatex -interaction=nonstopmode -halt-on-error resume.tex > "$WORK/log.txt" 2>&1; then
  grep -E '^!' -A3 "$WORK/log.txt" || tail -20 "$WORK/log.txt"
  exit 1
fi

"$PY" - "$WORK/resume.pdf" <<'EOF'
import re, sys
from pypdf import PdfReader
r = PdfReader(sys.argv[1])
t = ''.join(p.extract_text() for p in r.pages)
known = {'PyTorch','FastAPI','CloudFront','PostgreSQL','MySQL','SQLite','JavaScript','BERTopic',
         'DynamoDB','ChromaDB','OpenWebUI','GitHub','LinkedIn','NumPy','HerbsPro','FastMCP',
         'NoSQL','ChatGPT','YouTube','ViT','iCIMS','PayPal','httpOnly','SmartRecruiters'}
baseline = set()  # section 28 glue fixed by \pdfinterwordspaceon, Sept 12 2026
kern  = [s for s in ['A WS', 'Co-F ', 'F ramew', 'T ools', 'T rack', 'F undam'] if s in t]
glue  = sorted(w for w in set(re.findall(r'\b[A-Za-z]*[a-z][A-Z][A-Za-z]*\b', t)) if w not in known)
month = re.findall(r'[a-z](?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)\b', t)
digit = re.findall(r'[A-Za-z]{2,}(?:19|20)\d\d', t)
print(f"pages={len(r.pages)} kern={kern} glue={glue} month_fusion={month} digit_fusion={digit}")
ok = len(r.pages) == 1 and not kern and not (set(glue) - baseline) and not month and not digit
print("PARSE CHECK:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
EOF

mkdir -p "$(dirname "$OUT")"
cp "$WORK/resume.pdf" "$OUT"
echo "wrote $OUT"
