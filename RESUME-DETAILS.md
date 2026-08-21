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

**Stage 1 — pose-guided cropping.**
`torchvision` Keypoint R-CNN runs human pose detection on the query photo, and the
detected keypoints are used to crop the image down to the region where the item is
actually worn.

**Stage 2 — embedding.**
CLIP (ViT-B/32), PyTorch, produces a 512-dimensional embedding of the cropped
region.

**Retrieval.**
Catalog embeddings are precomputed offline. Query embedding is ranked against them
by cosine similarity, computed in Postgres.

**Serving.**
Query-time inference is isolated behind a FastAPI microservice. No model runs in
the main production serving path.

### The ablation (the important part)

Ran the two-stage pipeline against a whole-image baseline on a real query photo.

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

The production Spring Boot instance is memory-constrained at **906 MB** — nowhere
near enough to hold CLIP plus Keypoint R-CNN resident. Rather than resize the
instance, the design moved all inference off the serving path:

- catalog embeddings computed offline, ahead of time
- similarity ranking is a Postgres query, not a model call
- the only live inference is the query encode, isolated in a separate FastAPI service

Net effect: **$0 incremental hosting cost**, and the Spring Boot instance was left
untouched.

### Numbers — defensibility status

| Figure | Status |
|---|---|
| rank 3 → rank 1 | Measured, defensible |
| 0.42 → 0.72 | Measured, defensible |
| 0.014 band across top-4 | Measured, defensible, and the most interesting one |
| 906 MB instance | Measured, defensible |
| $0 incremental hosting | Defensible — precompute means no new compute was provisioned |
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
  and p99 on the FastAPI service, and is the model kept warm?
- **Failure mode when pose detection finds nothing.** If Keypoint R-CNN detects no
  person, does the system fall back to whole-image embedding — the configuration the
  ablation proved has no signal? Have an answer.
- **Single-item assumption.** The crop targets one worn region. What happens with
  two items in frame?

### Raw drafts (Aug 21, 2026) — kept verbatim for mining

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
