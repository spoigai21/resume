# Resume Detail Store — full-fidelity source material

Companion to `general/ShayanPoigaiResume (AllDetails).pdf`, which is a PDF with no
editable source in this repo and therefore cannot be appended to. New detail goes
here instead. Purpose is identical: keep every fact at full fidelity so resume
bullets can be re-cut for a specific JD without re-deriving anything.

**This file is never submitted anywhere.** It is source material only.

---

## Adorus — Visual similarity search (built August 2026)

### What it is

Content-based image retrieval over the product catalog. A user submits a photo;
the system returns the closest catalog items. Two-stage neural pipeline.

### Architecture

**Stage 1 — pose-guided cropping.** *(model updated per the Sept 13 2026 build record)*
A **YOLO11-pose** model exported to **ONNX** locates the wearer in the query photo, and
the detected keypoints are used to crop the image to the jewelry region, so the vector
describes the product rather than the person. (Earlier notes said torchvision Keypoint
R-CNN — retired.)

**Stage 2 — embedding.**
CLIP (ViT-B/32), PyTorch, produces a 512-dimensional embedding of the cropped
region.

**Retrieval.**
Catalog embeddings are precomputed offline. Query embedding is ranked against them
by cosine similarity, computed in Postgres.

**Serving.** *(confirmed Sept 13 2026)*
The embedder runs in **AWS Lambda as a container image with the weights baked in**. No
model runs on the always-on EC2 instance. The old FastAPI query service is no longer in
the path — stop mentioning it for search. (The competitive-intelligence system has its
own localhost-only FastAPI service; that one is real.)

**Lambda deployment — answered and still-open items:**

- **Container image or zip?** ANSWERED: container image, weights baked in. (The model
  stack is far past Lambda's 250 MB unzipped zip limit; images allow 10 GB.)
- **Model baked in or pulled from S3 at init?** ANSWERED: baked into the image.
- **Cold start cost.** Still open — loading weights in a fresh container is seconds. Have
  a number before an infrastructure interview.
- **Provisioned concurrency — yes or no, and why?** Still open. Declining it is defensible
  for bursty, low-volume traffic; say that deliberately.

**Why Lambda at all.** The model needs **~1.3 GB resident** against **~258 MB free** on
the EC2 box. A failed allocation there would let the OOM killer take the JVM — and the
storefront with it. Lambda keeps the model off that box entirely. ("$0 incremental
hosting" is retired: it predates the Lambda move and is not in the build record.)

### The ablation (the important part)

Ran the two-stage pipeline against a whole-image baseline on a real query photo.
(The crop stage is the pose model described above — YOLO11-pose per the build record.)

| Configuration | Correct item rank | Similarity score | Notes |
|---|---|---|---|
| Whole-image embedding (baseline) | **3** | **0.42** | Top-4 results all fell inside a **0.014** similarity band |
| Pose-cropped, then embedded | **1** | **0.72** | Clear separation from the rest of the field |

**Why the 0.014 band is the real finding.** It is a quantified null result: with
the whole image encoded, the top four candidates were statistically
indistinguishable, so the ranking carried no discriminative signal at all. The
crop did not merely improve the ordering — it created signal where there was none.
This is the strongest single piece of evaluation methodology anywhere in the
portfolio.

**Scope caveat, state it if asked:** this ablation was run on one hero image, not a
labelled evaluation set. Say "on a real query photo," never "on our test set." If
this is ever run over a proper labelled set with recall@k, the number replaces this
one and becomes considerably stronger.

### The architectural constraint

The embedder needs **~1.3 GB resident**; the production EC2 box has **~258 MB free**.
Loading it there risks a failed allocation that lets the OOM killer take the JVM and the
storefront with it. So no model runs on that box:

- catalog embeddings computed ahead of time (512-d CLIP vectors per product)
- similarity ranking is a Postgres query, not a model call
- the only live inference is the query encode, in AWS Lambda (container image, weights baked in)

### Numbers — defensibility status

| Figure | Status |
|---|---|
| rank 3 → rank 1 | Measured, defensible |
| 0.42 → 0.72 | Measured, defensible |
| 0.014 band across top-4 | Measured, defensible, and the most interesting one |
| ~1.3 GB model vs ~258 MB free on EC2 | From the build record, defensible |
| ~~906 MB instance~~, ~~$0 incremental hosting~~ | **RETIRED Sept 13 2026** — superseded by the build record. Do not use. |
| **"+72%"** | **DO NOT USE.** Appeared in an early draft. It reads as if derived from the 0.72 value itself, and a cosine similarity delta is not a percentage improvement. This is exactly the class of number §5 of the strategy doc says takes every other metric on the page down with it. |

### Interview prep — "what breaks at 1000x?"

Pre-compute these, per the Sixtyfour instruction in §7 of the strategy doc.

- **Linear scan ceiling.** Cosine similarity in Postgres over the full catalog is
  O(n) per query. Fine at current catalog size; needs an ANN index (pgvector with
  HNSW or IVFFlat) past roughly the tens-of-thousands mark. Naming this ceiling
  yourself reads senior.
- **Embedding staleness.** Catalog embeddings are precomputed, so adding or
  re-photographing a product requires a re-encode. This is the same cache-invalidation
  problem as the Redis layer at HerbsPro and the CloudFront invalidation on delete —
  it belongs in the same through-line (§10).
- **Cold start / latency.** Query-time inference still loads a model. What is p50
  and p99 on the Lambda embedder, and is it kept warm?
- **Failure mode when pose detection finds nothing.** If YOLO11-pose detects no
  person, does the system fall back to whole-image embedding — the configuration the
  ablation proved has no signal? Have an answer.
- **Single-item assumption.** The crop targets one worn region. What happens with
  two items in frame?

### Raw drafts (Aug 21, 2026) — kept verbatim for mining

> **SUPERSEDED Sept 13 2026.** These drafts name Keypoint R-CNN, a FastAPI service, a
> 906 MB instance and $0 hosting — all retired by the build record. Mine the phrasing only;
> never reuse those facts.

> Engineered a two-stage neural inference pipeline in PyTorch — torchvision Keypoint
> R-CNN for human pose detection, then CLIP (ViT-B/32) for 512-d image embeddings —
> cropping query photos to the worn-jewelry region before encoding; ablation showed
> the crop was decisive, lifting the correct match from rank 3 (0.42) to rank 1 (0.72).

> Architected the system so no model runs in production: catalog embeddings are
> precomputed offline and ranked by cosine similarity in Postgres, with query-time
> inference isolated behind a FastAPI microservice — keeping a memory-constrained
> (906 MB) Spring Boot instance untouched and hosting cost at $0.

> Built visual product search for a DTC e-commerce store using CLIP (ViT-B/32)
> embeddings in PyTorch — precomputing 512-dimensional vectors for the catalog offline
> and serving cosine-similarity retrieval from Postgres, with a torchvision Keypoint
> R-CNN pose-detection stage that crops query photos to the jewelry region. The crop
> raised the correct product from rank 3 to rank 1 and its similarity score from 0.42
> to 0.72 (+72%). Precomputing embeddings kept model inference off the 906 MB
> production instance, adding zero incremental hosting cost.

---

## Adorus — Virtual try-on: accuracy correction (Aug 21, 2026)

**Shipped on Google Gemini, used reference-conditioned.** That is the only
image-generation service actually in the product.

**Rejected candidates, evaluated but never shipped:** AWS Bedrock Nova Canvas,
Stability, Rekognition. Evaluation axes were identity preservation, fidelity,
latency, and cost.

**Why the resume no longer names them.** Listing all four together without saying
which won implied hands-on experience with four managed services when the truth is
one. The benchmark framing was dropped entirely rather than de-named, because
"benchmarked 5 approaches" with the alternatives stripped out is the unverifiable
form — naming what you rejected is the only thing that makes a benchmark credible,
so an unnamed benchmark is weaker than no claim at all.

**Still true and still worth saying out loud in an interview:** you evaluated
several image-generation approaches on four named axes before selecting a
reference-conditioned model. That is a real process. It just needs a voice, not a
resume line.

### On the page now

Measurement-driven prompting — parses per-product dimensions (chain length,
pendant size) into true-to-life scale and physically accurate drape, with
per-product overrides. Entirely your own code, zero third-party risk, and §5 of the
strategy doc already called it "the actually-hard part of the try-on."

### Not on the page, available as interview material

- 3-generation free-credit quota that resets on purchase
- React widget: photo upload, live camera capture via `getUserMedia`, image download, feedback
- **Stores zero customer photos** — a real privacy decision, worth raising unprompted
- Auth-gated Spring Boot endpoints fronting the whole try-on stack

### OPEN ITEM — verify before submitting

Confirm `~$0.05/image` is **Gemini's actual per-image cost**, not the cost range
observed across all benchmarked candidates. The AllDetails PDF is ambiguous on
this. If it is the range, drop the figure rather than approximating it.

---

## Adorus — complete build record (supplied by Shayan, Sept 12 2026)

Full inventory of the Adorus work, recorded as supplied. **Not for direct use on the
resume** — this is the pool to cut tailored bullets from for specific JDs. Wording is
his; only chat timestamps and two run-together typos ("schemafrom", "signed-inand")
were cleaned. The analytics section uses his **revised** bullets, which supersede the
first version (the first version said "~23% who accept cookies"; the measured figure is
20%, 26 of 133 — never use 23%).

### Platform architecture

- Designed and built a full-stack production e-commerce platform from scratch — Java 21 / Spring Boot, PostgreSQL, React + Vite, deployed on AWS — rather than assembling on Shopify, owning every layer from schema to CDN
- Domain-driven backend of 24 bounded modules (catalog, cart, checkout, orders, returns, reviews, promotions, preorders, shipping, marketing, insights) across 185 classes and 19,562 lines of Java
- Authored and maintained 80 versioned Flyway migrations against a live database holding real customer orders, including widening changes applied with zero downtime and no data loss
- Built a 92-module React storefront across 41 indexable routes, with client-side routing, a guest cart backed by a 30-day httpOnly cookie, and static metadata for crawlers and social scrapers that never execute JavaScript
- Architected the AWS topology for cost and blast radius — CloudFront fronting an S3 storefront with /api/* proxied to EC2, an origin security group admitting only CloudFront, RDS, Cognito for auth, and a CloudFront Function performing host canonicalisation at the edge
- Built two deployment pipelines: GitHub Actions building and cache-invalidating the frontend on merge, and a checksum-verified backend deploy that restarts the service and validates health through the CDN before reporting success
- 530 commits since May 2026, solo

### Payments & commerce

- Integrated four payment rails — card, PayPal, Apple Pay and Google Pay — each with its own order-reconciliation path resolving to a single order record
- Implemented Stripe Checkout with webhook-driven order creation, so orders are produced by checkout.session.completed rather than a client redirect; a closed tab never loses a paid order
- Configured Stripe Tax for California sales-tax registration and collection
- Built per-product and per-variant inventory management across a 23-product catalogue in 4 categories and 2 curated collections, with stock decremented on paid orders
- Implemented a preorder mode permitting sale at zero stock against a customer-visible ship date — used to validate demand for unpurchased inventory
- Built server-side promotion codes and a welcome offer, validated against the same Stripe mode as the publishable key to eliminate an environment-mismatch class of bug
- Implemented customer returns with prepaid shipping labels via Shippo, emailed to the customer, with refund and return state tracked against the order
- Built transactional email on a verified domain (Resend) including RFC 8058 one-click List-Unsubscribe and CAN-SPAM-compliant footers

### Machine learning in production

- Shipped visual and semantic product search using CLIP embeddings — 512-dimension vectors per product with query-side encoding, letting shoppers search by uploading a photo instead of guessing a search term
- Built pose-aware jewelry cropping using a YOLO11-pose model exported to ONNX, locating the wearer and cropping to the jewelry region before embedding, so the vector describes the product rather than the person
- Deployed the embedder to AWS Lambda as a container image with weights baked in — chosen deliberately because the model needs ~1.3 GB resident against ~258 MB free on the EC2 box, where a failed allocation would have let the OOM killer take the JVM and the storefront with it
- Shipped an AI try-on feature generating a preview of a piece worn by the customer from an uploaded photo, with asynchronous job handling, a credit system, and a guarantee that no photo is ever persisted to disk or object storage
- Extended try-on to signed-out visitors with a device-level identity from a salted one-way hash plus a 6-per-address daily cap. Verified under attack: 40 requests from distinct IPv6 addresses inside one /64, and 25 concurrent requests from one address, each yielded exactly 6 allowances rather than 40 and 21

### Security engineering

- Authored a written set of security invariants enforced in code and tests rather than asserted in a document, including a fail-closed default applied across authentication, payment verification and rate limiting
- Identified and closed a decompression-bomb vulnerability in image upload — a 102 KB PNG allocated 134 MB on a 192 MB heap. Rewrote decoding to read headers first and subsample the raster, reducing it to 40 MB. Proved the fix by mutation rather than by assertion
- Implemented content-type sniffing by magic bytes, rejecting the client's declared MIME type and file extension
- Configured layered rate limiting at nginx with separate zones for the API, visual search and review-photo uploads, keyed on the true client address resolved from CloudFront's published origin ranges
- Fixed trusted-proxy header handling — reading the client address from the end of X-Forwarded-For that nginx appends, closing a spoofing path that would have allowed unlimited allowances against a billable third-party API
- Implemented IPv6-aware abuse controls, truncating addresses to their /64 prefix before hashing, since a single host can otherwise bind 2^64 addresses and defeat any per-address limit
- Replaced a check-then-act path with PostgreSQL advisory locks after establishing that a concurrent burst exceeded the configured ceiling by roughly 3.5×
- Designed least-privilege database grants isolating the analytics/scraper schema from the orders tables
- Authored a strict Content-Security-Policy enumerating every permitted script, connect and image origin, as e-skimming defence on a payment page

### Testing & continuous integration

- Built a suite of 590 automated tests — 445 backend across 44 suites, 145 frontend across 25 — covering money paths, auth boundaries, tax, returns, structured data and rendering
- Added PIT mutation testing as a CI job with a score threshold, measuring tests on whether they can actually fail rather than on line coverage
- Wrote three custom CI gates that no off-the-shelf tool provides:
  - a migration gate rejecting data statements and unflagged destructive DDL, and blocking edits to already-merged migrations — the failure mode that corrupts a live database
  - a secret scanner over added lines only, so credentials cannot enter through a diff
  - an API-contract checker comparing every /api/… call in the frontend against the backend's actual request mappings, catching route drift at review time
- Implemented a lint ratchet failing the build when the problem count rises, permitting legacy debt without permitting new debt
- Adopted mutation-verified regression tests as standard practice — each guard proven to fail when the bug it describes is reintroduced, not merely to pass today

### Analytics & privacy engineering (revised bullets — use these)

- Built cookieless first-party analytics measuring 133 unique visitors and 725 page views (5.5 per person) over 30 days, using a daily-rotating salted SHA-256 of address and user agent — storing nothing on the visitor's device and never persisting the raw address
- Captured 5× more visitors than the consent-gated stack: only 20% of visitors (26 of 133) accept cookies, so GA4 and session recording see roughly a fifth of reality. The first-party layer requires no banner and therefore counts everyone
- Quantified the measurement gap explicitly — 110 of 133 visitors never answered the consent banner at all, which is the number that makes third-party analytics unreliable at this scale and justified building the first-party layer

Retained from the first version (not replaced by the revision):

- Designed deliberate un-trackability as a property: the salt rotates daily, so the same identifier cannot be followed across days — the property that makes it privacy-respecting is the same one that makes it useless for tracking
- Built a funnel view grouping homepage, category, product and collection views, after establishing that a top-ten list of raw paths rendered 23 product pages statistically invisible
- Implemented consent-gated third-party analytics (GA4, Contentsquare session recording), loading only after an explicit choice, with consent state captured at the moment of decision
- Excluded admin traffic from its own metrics at both client and server, so operator sessions cannot inflate the numbers
- Built billable-usage reporting surfacing AI try-on generations split by signed-in and anonymous, giving a running view of third-party API cost

### Search engine optimisation

- Implemented structured data across the catalogue — Product, Offer, BreadcrumbList, Organization, WebSite, FAQPage, ItemList — generated from the same data the page renders so markup and content cannot drift
- Diagnosed a robots.txt rule silently removing all product structured data: Google's renderer will not fetch a resource robots.txt forbids, so blocking /api/ left every product page with no data to build markup from. The Rich Results Test reported "no items detected" on pages that rendered perfectly in a browser. Result: 0 → 3 valid rich-result types
- Diagnosed a soft-404 caused by the same class of failure on API-served content pages, and replaced the hand-written allowlist with a test deriving every indexable page's data dependencies from source
- Removed a canonical tag making every page a duplicate of the homepage — a single-file SPA served from S3 cannot carry a static canonical, and Google's first pass believed it
- Built build-time sitemap generation producing 41 URLs from the live catalogue, never staler than the last deploy
- Built a Google Shopping product feed of 23 items in RSS 2.0 with the g: namespace — consumable by Pinterest, Merchant Center and Meta — with per-row validation so rejected rows fail loudly rather than silently

### Competitive intelligence system (separate codebase)

- Built a local-only competitive intelligence platform answering two sourcing questions: is this price good, and if I make this piece, is there potential
- Wrote a catalogue collector across 21 competitor brands (Mejuri, Missoma, Gorjana, Ana Luisa, Astrid & Miyu and others), reading the public unauthenticated /products.json endpoint Shopify serves by design, with robots.txt compliance enforced in code
- Designed a nine-table time-series schema over 11 migrations and 2,736 lines of Python, capturing price movement, product survival, collection membership and discontinuations — a dataset that cannot be backfilled and exists only because collection started early
- Built CLIP embeddings over competitor imagery powering design comparables: given a sketch or photo of a proposed piece, return the closest products on the market and what they charge
- Added LLM enrichment tagging market tier, material, style and value propositions, plus a RAG retrieval index over product text for internal research
- Stood up Metabase for numeric analysis and a localhost-bound FastAPI service for image-driven views, deliberately never exposed to the internet
- Reasoned the legal and ethical boundaries explicitly — distinguishing a public machine-readable endpoint from defeating anti-bot systems, and holding review data back as a separate, riskier decision rather than collecting it by default

### Production operations

- Diagnosed and resolved a checkout outage affecting an entire hostname: a CORS allowlist containing only the apex domain caused every POST from the www host to return 403, which CloudFront then rewrote into a 200 carrying HTML, surfacing to customers as a generic network error under Add to Cart. Traced from a single screenshot through nginx access logs to root cause; quantified the impact at 97 failed requests across 7 days and 19 visitors, including 8 add-to-cart attempts
- Fixed it in two layers — a 301 at the CDN so the affected hostname never originates an API call, plus a derived CORS entry as a safety net, with the sibling host computed rather than configured so it cannot drift from the domain
- Built zero-downtime backend deploys with checksum verification, service restart and end-to-end health validation through the CDN
- Performed incident forensics from nginx access logs, isolating failure signatures by referer, method and status to separate genuine customer impact from operator testing
- Wrote 78,512 words of design documentation across 8 build phases, 9 feature specifications and 27 documents, each recording not just what was built but which alternatives were rejected and why

### Tailoring routing — which sections to pull from

| JD emphasis | Pull from |
|---|---|
| Backend / distributed systems | 24 bounded modules, 80 Flyway migrations with zero downtime, webhook-driven order creation, advisory locks (3.5× burst) |
| Infrastructure / cloud / DevOps / SRE | AWS topology (origin SG, CloudFront Function), checksum-verified deploys via CDN health check, CORS outage forensics, Lambda-vs-OOM decision |
| Security | Decompression bomb (134 MB → 40 MB), X-Forwarded-For spoofing fix, IPv6 /64 abuse controls, magic-byte sniffing, CSP, least-privilege grants, fail-closed invariants |
| Testing / quality / platform tooling | 590 tests, PIT mutation testing in CI, 3 custom CI gates (migration, diff secret scan, API contract), lint ratchet |
| ML / applied AI | CLIP 512-d search, YOLO11-pose → ONNX crop, Lambda container deploy, try-on async jobs + credits + no photo persistence |
| Data / analytics / privacy | Cookieless analytics (133 visitors, 20% consent, 5× coverage), funnel view, competitive-intel time-series (9 tables, 21 brands), Metabase |
| Full-stack / product | 92-module React storefront, 41 routes, 4 payment rails, preorders, returns via Shippo, structured data 0 → 3 rich-result types |
| Payments / fintech | Stripe Checkout webhooks, Stripe Tax, 4 rails reconciling to one order, Stripe-mode mismatch guard |

### Conflicts — RESOLVED Sept 13 2026

He confirmed this build record is accurate and up to date and **overrides anything older in
the repo**. Applied everywhere (master resume + all variants, Palantir copy, this file,
APPLICATION-RESPONSES.md, application-answers.json, RESUME-STRATEGY.md):

1. **Crop model:** YOLO11-pose exported to ONNX. Keypoint R-CNN retired.
2. **Memory:** ~1.3 GB model resident vs ~258 MB free on EC2 (OOM-killer risk to the JVM). "906 MB instance" retired.
3. **Hosting cost:** "$0 incremental hosting" retired (predates the Lambda container deploy; not in the record).
4. **Scope bullet:** "35 RESTful endpoints across 5 AWS services at ~$40/month" retired; the bullet now uses 24 bounded modules and 80 Flyway migrations applied live with zero downtime. AWS services in use: CloudFront, S3, EC2, RDS, Cognito, Lambda.
5. **Migrations:** 80 versioned Flyway migrations (supersedes the old 9 vs 33).
6. **Orders:** created by Stripe's checkout.session.completed webhook; Shippo carries return labels. The dormant state-machine bullet was rewritten to match.
7. **Try-on:** unchanged — the ~$0.05/image Gemini figure is still an open verification item.

**Kept, not contradicted:** the rank 3 → rank 1, 0.42 → 0.72 and 0.014-band ablation, now attributed to the pose-crop stage.
