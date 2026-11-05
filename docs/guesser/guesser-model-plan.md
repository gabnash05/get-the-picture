# Guesser model and data plan

Decisions agreed on 4 November 2026 (Asia/Manila). Delivery horizon: next week; the seven workdays below are a relative work plan, not an agreed calendar deadline.

**Scope:** Guesser only. All 345 Quick, Draw! categories. Direct depictions first. No new human drawing collection. A transformer is required. This document specifies work to implement and validate; it does not report a trained model or measured recognition performance.

## 1. The agreed result

Build a locally hosted image classifier that repeatedly recognizes the currently visible drawing and produces a ranked distribution over the 345 category IDs. Use a pretrained **ViT-Tiny**, adapted with complete and incomplete Quick, Draw! examples.

Per-point timestamps determine which points exist in each training/evaluation view. The first model receives an image, not coordinates, timestamps, the target word, or future strokes.

| Decision | Agreed plan |
| --- | --- |
| Training and recognition data | Quick, Draw! only |
| Vocabulary | All 345 official categories; the game prompt registry must use this vocabulary |
| Recognition task | One intended category for the whole evolving canvas |
| Backbone | timm ViT-Tiny, ImageNet pretrained, then fine-tuned on Quick, Draw! |
| Color | Shape recognition; color is usable for preprocessing but is not an intended semantic cue |
| Fill/background | Keep the UI tools; explicitly test and select background-aware preprocessing |
| Data volume | Target 5,000 distinct usable original drawings per class |
| Split | 4,000 train / 500 validation / 500 test per class, before making prefixes |
| New player dataset | Excluded at the user's request |
| Updates | Approximately one recognition update per second when the visible state changes |
| Counted guesses | Scheduled game opportunities, separate from recognition updates |
| Passing | Allowed for blank or uncertain input; no replacement opportunity |
| Demo | One inference laptop, one match, up to three teams |
| Demo timing | Configurable example: 60 seconds; six opportunities at 10, 20, 30, 40, 50, 58 seconds |
| Game hints | Retain the existing design: the same official word length and revealed letters as humans |
| Evaluation | Complete-only training versus partial-training adaptation; no prescribed accuracy percentage |
| Latency target | Provisional p95 snapshot-to-result <= 1 second at three teams; measure it |
| Additional class constraints | None reported beyond the transformer requirement |

The one-second cadence, six demo opportunities, training hyperparameters and latency target are working configurations. They are not measured capacity or universally correct thresholds. Keep them versioned and adjustable.

This Guesser scope supersedes the earlier Qwen candidate for this plan. It does not rewrite the game repository or change the separate Referee work. Indirect visual references and private codes may remain legal game strategies, but recognizing them is outside this first model's claimed capability.

## 2. Three people, three concrete responsibilities

The user owns **Data**. The other two group members own **Model** and **Validation & Inference**. Use member names in your project tracker when assigned.

| Role | Owns | Required handoff | Does not independently change |
| --- | --- | --- | --- |
| Data — you | Source inventory and attribution; category registry; full-file sampling; structural cleaning; duplicate handling; original-drawing splits; timestamp cuts; Quick, Draw! renderer; indexed records/manifests; quality report; shared preprocessing fixtures | Versioned data package, train/validation manifests, test package for the validation owner, preprocessing specification and examples | Class ID order, held-out test membership, or preprocessing without a version change and coordination |
| Model | Load and adapt the pretrained transformer; data loader; complete-only baseline; partial-training experiment; equal training budget; checkpoints; training logs; model packaging | Weights, model configuration, label mapping hash, preprocessing version, training recipe, checkpoint-selection record | Data splits or final test-based tuning |
| Validation & Inference | Independently audit splits and inputs; validation reports and calibration; hold final test for the frozen candidate; background/fill and renderer checks; FastAPI inference worker; checkpoint integration; latency/load tests | Evaluation report, inference contract/service, latency traces, final test report and demo run instructions | Training labels, the split, or scoring/game rules inside the inference service |

**Shared ownership:** Data and Validation & Inference agree on the renderer/preprocessor and golden image fixtures. Model uses that exact version. The validation owner can help inspect data-quality grids while the data owner prepares downloads.

**Why these boundaries:** the data role produces reusable original drawings and deterministic views, rather than millions of unrelated PNGs. The model role can begin on a small package while data preparation continues. The inference owner can build the API against a dummy 345-class predictor while training runs.

### The first shared contract

Freeze these on Day 1:

- `labels.json`: ordered list of 345 class IDs and exact source names.
- `dataset_version` and sampling/cleaning version, with seed `198173`.
- `preprocess_version`, including color/background handling and stroke rendering.
- Input tensor: float32 `[B, 3, 224, 224]`; grayscale shape image repeated into RGB channels.
- Output: logits `[B, 345]`; labels resolved only through the matching registry.
- Validation prefix grid: 10%, 20%, ..., 100% of each recording's drawing duration.
- Same original drawing and every derived view stay in exactly one split.

## 3. Which data files to use

Use the official **raw .ndjson** files as the master source. Do not mix independently sampled raw, simplified and bitmap variants as if they were different drawings.

| Quick, Draw! representation | Shape / contents | Timing | Use here |
| --- | --- | --- | --- |
| Raw NDJSON | One JSON object per line. A drawing is a ragged list of strokes; stroke s is `[x_s, y_s, t_s]` with equal-length coordinate/time arrays | Per-point milliseconds | **Master source** for timestamp-cut incomplete drawings |
| Simplified NDJSON | Ragged strokes `[x_s, y_s]`, coordinates normalized into a 256-square region | Point timing removed | Optional parser/visual reference; not the temporal master |
| Binary .bin | Packed simplified drawings and metadata | No original per-point times | Avoid for this pipeline |
| Bitmap .npy | Flattened 28x28 images. A probed cat file is uint8 `[123202, 784]`; N varies by category | None | Complete-image baseline data only; cannot recover actual drawing progress |
| Sketch-RNN .npz | Preprocessed variable-length stroke sequences in train/valid/test arrays | Not the raw timestamp arrays | Not needed for the selected image-model pipeline |

Source: [official format documentation](https://github.com/googlecreativelab/quickdraw-dataset). The raw format was also directly checked using the first 64 KiB of cat, bicycle and alarm clock files. This was a schema probe, not a dataset-wide audit.

The raw fields include `key_id`, `word`, `drawing`, `recognized`, `timestamp` and `countrycode`. Keep IDs as strings. The top-level creation timestamp is different from point times. The old game's `recognized` flag is neither a human quality label nor your model's confidence: retain it for auditing and do not use it as an input feature.

The original attachment also showed AtyPict. The user clarified that this plan uses Quick, Draw! only. AtyPict is therefore outside this Guesser pipeline.

### One original record

~~~json
{
  "key_id": "example-id-as-string",
  "word": "cat",
  "recognized": true,
  "drawing": [
    [[100, 110, 120], [80, 85, 90], [0, 30, 60]],
    [[130, 140], [90, 100], [120, 160]]
  ]
}
~~~

This example has two strokes, with three and two points. Real S and N_s vary; do not turn the raw dataset into a fixed `[S,3,N]` tensor by assuming all drawings have the same lengths.

## 4. Download and local environment: exact operating procedure

### 4.1 Create a separate Python workspace

Keep this work independent of the frontend Node installation. Use the same Python minor version on all three laptops; Python 3.11–3.13 is a reasonable supported starting range for the pinned setup below.

PowerShell, from a directory chosen for the Guesser work:

~~~powershell
New-Item -ItemType Directory -Force guesser-work
Set-Location guesser-work
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu118
.\.venv\Scripts\python.exe -m pip install timm pillow numpy pandas pyarrow scikit-learn opencv-python-headless fastapi uvicorn pydantic safetensors
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
.\.venv\Scripts\python.exe -m pip freeze > requirements.lock.txt
~~~

The pinned torch/torchvision pair and CUDA 11.8 wheel source are listed by [PyTorch](https://pytorch.org/get-started/previous-versions/). They are a conservative Windows/NVIDIA starting point, not a claim that this environment was installed here. Verify the NVIDIA driver and CUDA availability on each training/inference laptop. A CUDA toolkit installation is not the first troubleshooting step for a wheel that already bundles its runtime.

The local machine queried during planning reported a GTX 1650 Ti with 4 GiB VRAM. Start at physical batch 8, lower it if needed, and use accumulation for a larger effective batch. Other group machines may support larger batches. Record the actual device and measured throughput.

After a successful smoke run, use the same lock file on the group machines. Record model checkpoint revision/hash as well as package versions.

Suggested directories:

~~~text
guesser-work/
  configs/                 # versioned data, training, inference settings
  data/
    source-inventory/      # category registry, object metadata, receipts
    staging/               # sampled raw records, temporary reserve candidates
    records/               # indexed original drawings, one class file or shards
    manifests/             # train / validation / test drawing membership
    qa/                    # cleaning counts and reviewed contact sheets
  src/                     # preparation, rendering, loading, training, serving
  runs/                    # training configurations and logs
  models/                  # frozen model package
  reports/                 # validation, final test, latency
~~~

Add data, model weights, caches, virtual environments and large run artifacts to the appropriate local ignore rules before working in Git. Track code, recipes, registry, small fixtures and report summaries. Arrange a shared transfer location for the selected package rather than having every teammate repeat the 181 GiB source scan.

### 4.2 Freeze the source inventory

Download the exact official category file:

~~~powershell
New-Item -ItemType Directory -Force data\source-inventory
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/googlecreativelab/quickdraw-dataset/master/categories.txt' -OutFile 'data\source-inventory\categories.txt'
(Get-Content -LiteralPath 'data\source-inventory\categories.txt').Count
Get-FileHash -Algorithm SHA256 -LiteralPath 'data\source-inventory\categories.txt'
~~~

Expected category count: **345**. Preserve this file's line order as class IDs 0–344. Do not sort names differently in the API or reconstruct IDs from directory enumeration. Preserve exact source spelling and capitalization; display names may have separate formatting.

Public raw object pattern:

~~~text
https://storage.googleapis.com/quickdraw_dataset/full/raw/<URL-encoded category>.ndjson
~~~

Example: [alarm clock raw file](https://storage.googleapis.com/quickdraw_dataset/full/raw/alarm%20clock.ndjson). Spaces must be URL encoded.

Get object metadata from the public [Cloud Storage listing API](https://storage.googleapis.com/storage/v1/b/quickdraw_dataset/o?prefix=full%2Fraw%2F&maxResults=1000). Save size, generation, MD5/CRC32C metadata and update time for each object. Check pagination and require a one-to-one match with the 345 registered names.

A listing checked on 4 November 2026 contained 345 raw category objects, totaling **194,810,597,157 bytes = 181.43 GiB**. Recheck before the real scan. This is transfer volume, not a requirement to store every source file.

Ideal transfer-only lower bounds are approximately 21.6 hours at 20 Mbps, 8.7 hours at 50 Mbps, or 4.3 hours at 100 Mbps. Parsing, cleaning, retries and shared bandwidth add time.

### 4.3 Stream complete files; retain a balanced sample

**Agreed method:** read each category file to its end once, retaining the best deterministic random priorities. Do not stop at the first 5,000 records.

- Final target: 5,000 structurally valid, distinct drawings per class.
- Initially retain 5,500 candidates per class, using 500 as a duplicate-removal reserve.
- Priority: SHA-256 of `"select-v1|198173|" + key_id`, interpreted as an integer.
- Keep the 5,500 smallest priorities with a bounded max-heap.
- Structural cleaning precedes eligibility for the retained sample.
- Include valid examples regardless of `recognized=true/false`. Report that flag's distribution; it is not a rejection rule.
- Read at most 2–3 category streams concurrently to begin. Measure CPU, RAM, network and thermal behavior before increasing concurrency.
- Keep source hashes/counts while streaming and verify source size and hash before declaring a class complete.
- Write a sampled class and a completion receipt atomically only after a successful full scan.
- Resume by skipping only classes with matching source generation, recipe and completed receipt. If a stream fails, retry that class from the beginning unless a fully tested sampler-state/byte-offset resume mechanism exists.
- Do not use random HTTP byte offsets as if they were uniform random drawings; line lengths differ.
- You may start model work with the first completed class packages, but final training/evaluation must include all 345 classes.

One full raw category can be downloaded for debugging with the following real command. It is an alternative inspection operation, not the storage strategy for all classes:

~~~powershell
New-Item -ItemType Directory -Force data\raw-debug
curl.exe --fail --location --retry 5 --continue-at - --output "data\raw-debug\cat.ndjson" "https://storage.googleapis.com/quickdraw_dataset/full/raw/cat.ndjson"
~~~

The data owner implements the streaming preparer from the algorithms in Sections 5–7. The file/module names in this plan are proposed deliverables; no preparation CLI or full data download has been created by this planning session. The reference functions in Section 15 can be copied into that implementation.

Start by scanning one whole class and record bytes/second, valid records/second, peak RAM and retained-file size. Extrapolate from measured values. Reserve space for staging, final indexed records, manifests, model/environment caches and a temporary export copy. Avoid storing every prefix PNG: its uncompressed volume would be roughly 864 GB for all ten views of the 1.725M-drawing target, even before metadata.

## 5. Cleaning: keep the original meaning and chronology

Produce a rejection/repair log by class and reason. Retain the immutable selected raw record or an audit reference so every cleaning decision can be traced.

| Check | Action |
| --- | --- |
| JSON invalid, missing ID/word/drawing | Reject and count reason |
| Word does not match the requested category | Quarantine; do not silently relabel |
| Empty drawing or no visible geometric extent | Reject as unusable for this task |
| Stroke does not have three arrays, or lengths differ | Reject; do not guess missing times |
| Non-numeric/non-finite coordinates or invalid point times | Reject |
| Negative or decreasing point times, including across strokes | Quarantine/reject; do not sort points to repair chronology |
| First point time is nonzero | Preserve raw times; subtract the first valid point time when calculating relative duration |
| Consecutive identical x/y/t triples | May remove the exact duplicates and log the repair |
| Same x/y at different times | Keep: it can encode a pause |
| Single-point stroke within an otherwise valid drawing | Keep and render as a dot |
| Empty strokes | Remove with a recorded repair; reject the drawing if none remain |
| Zero total duration | Quarantine from the timestamp-prefix experiment; do not invent timing |
| Very long or unusual drawings | Flag and inspect. Set documented resource limits only after measuring; do not discard complex classes just to make metrics look better |
| `recognized=false` | Keep when structurally valid; not an “incorrect” training class |
| Country and wall-clock creation time | Audit metadata only; never model features |
| Very simple category such as line, circle or square | Keep; simplicity is not corruption |

A prompt label describes the intended concept. It does not certify that a particular partial view is already recognizable. Do not discard difficult early prefixes simply because the model gets them wrong.

### Duplicate handling before the split

1. Deduplicate retained candidates by `key_id`. If the same ID has inconsistent contents, quarantine the conflict.
2. Compute an exact full-trajectory hash over the cleaned stroke arrays, with a documented canonical serialization. At minimum include the complete x/y/t values and stroke boundaries.
3. Collapse same-class exact trajectory duplicates deterministically.
4. Quarantine cross-label exact-trajectory conflicts for review rather than assigning an arbitrary label.
5. Fill each class back to 5,000 from its ranked reserve. If the reserve is insufficient, enlarge it and rescan that class; fail visibly instead of silently shrinking or dropping the class.
6. Record final counts and check global ID/trajectory uniqueness again.

This guarantees exact-duplicate separation among the selected package, not a proof that all visually similar drawings or drawings by the same person have been removed. Quick, Draw!'s documented fields do not provide an artist ID; call the split **drawing-disjoint**, not drawer-disjoint.

Use visual QA on a deterministic contact sheet for every class: for example 8 complete views and 4 corresponding 50% views per class, plus all flagged exceptions. Divide checking between Data and Validation & Inference. Log obvious label mismatches or written-word-only drawings using a fixed review rule. Do not relabel an ambiguous image based on the candidate model's prediction. After any removal, refill from the reserve before freezing the split.

## 6. Split original drawings, then generate views

After cleaning and duplicate handling:

1. For each category, independently rank its 5,000 retained IDs using SHA-256 of `"split-v1|198173|" + key_id`.
2. First 4,000 IDs: training; next 500: validation; last 500: final test.
3. Freeze membership in manifests and record the manifest hashes.
4. Derive every partial view, full view, color/fill transformation and augmentation from that assigned original. All versions inherit its split.
5. Give the model owner training and validation packages. The validation owner keeps the final test evaluation separate until the model, preprocessor and decision policy are frozen.
6. Make a small tuning subset from validation by deterministic ID ranking, never by moving test drawings into validation.

| Partition | Per category | All 345 categories |
| --- | ---: | ---: |
| Training originals | 4,000 | 1,380,000 |
| Validation originals | 500 | 172,500 |
| Final-test originals | 500 | 172,500 |
| Total originals | 5,000 | 1,725,000 |

These are planned final counts, contingent on the cleaning/refill checks. They are not counts already downloaded.

A complete view of drawing A in training and a 30% view of drawing A in testing is leakage. Renaming its file or rerendering it does not make it a new independent example.

### Store originals efficiently

Use per-class indexed JSONL files or equivalently documented record shards. Do not load the whole raw corpus into pandas or a single Python list.

A practical representation is:

- `records/c000.jsonl` through `records/c344.jsonl` containing original cleaned strokes.
- Manifests in Parquet or CSV with at least: `drawing_id`, `group_id`, `class_id`, `record_file`, `byte_offset`, `byte_length`, `split`, `recognized`, `stroke_count`, `point_count`, `duration_ms`, `trajectory_hash`.
- `labels.json` with `class_id` and `source_name`.
- `dataset-receipt.json` with source-object versions, recipes, actual counts, source/manifest checksums and attribution.

Byte offsets require uncompressed seekable JSONL. A gzip file can be a transfer archive; decompress it before using ordinary byte-offset random access. Each loader worker needs its own file handles. Cache a few open shards/records per worker; do not duplicate the entire Python object graph in every Windows DataLoader worker.

Data loader labels come from the manifest. Only the rendered image tensor enters the neural network.

## 7. Turn timestamps into incomplete training examples

For a drawing with point times t, let t0 be its first point time, t1 its final point time, and D = t1 - t0.

At completion fraction f:

`cutoff = t0 + f * D`

Keep only points already recorded at or before cutoff, preserving stroke boundaries and chronological order. An ongoing stroke is truncated to its observed points. Do not connect it to a later point, interpolate toward a future coordinate, join separate strokes, or reveal later erasures.

### Training view sampling

At each epoch, each sampled training original supplies one view:

- 20% probability: complete drawing, f = 1.
- 80% probability: f sampled uniformly from 0.10 to 0.90.
- Seed view sampling by run seed, drawing ID and epoch so runs can be reproduced.
- Sample originals uniformly; do not let a 20-stroke drawing contribute 20 times the weight of a one-stroke drawing.
- If a sampled cut has no visible ink, resample that training cut or skip it and report it. Do not train a blank image as a confidently identifiable word.
- In evaluation, keep blank stages in the denominator and let the policy pass. Do not hide them by silently discarding them.

### Validation and final-test views

Use the fixed grid `f = [0.1, 0.2, ..., 1.0]` for every held-out original. Empty/unchanged prefixes are valid observations. Mark identical consecutive views so they can be cached without being counted as independent drawings.

Timing fractions are defined using the recorded completed drawing for **offline evaluation only**. The live model is never told the final duration, percent completion, final number of points or final bounding box. A Quick, Draw! recording's 50% stage is not the 30-second mark of a 60-second game round.

Here “100%” means the end of the recorded trajectory. It is not an annotation certifying that the intended picture is semantically finished. Report fractions as recorded drawing-time progress, and do not claim that an inherently ambiguous first mark should already identify its target.

### Prevent spatial leakage as well as split leakage

Crop/scale each partial input using only its current visible geometry. Never normalize an early prefix with the complete drawing's later bounding box. The image preprocessor must not use unseen points to choose its center, scale or mask.

Use elapsed drawing-time prefixes as the main experiment because timing is available. A point-count or stroke-count prefix grid can be an optional sensitivity check. Do not claim that timestamps are neural input features in the selected image model.

## 8. Rendering, color, fill and the background question

**Ignoring color meaning is not the same operation as blindly making every non-white pixel black.**

If a player fills the background blue, a “non-white = foreground” rule would label nearly the entire canvas as ink. Grayscale conversion alone can also hide a boundary between colors of similar brightness. This is an explicit preprocessing requirement.

### Canonical visible state comes first

For real gameplay, replay the accepted brush, fill, eraser, undo/redo and clear operations to create the exact visible canvas for the chosen version. Never render every historical stroke as if erased/undone content were still visible.

The current frontend contract is 1024x768 and includes colored brush/eraser strokes, region fill, undo/redo and clear. Its fill implementation composites transparency over white before flood fill. There is no separate semantic label saying “this fill is only the background.”

Therefore do not strip all fill operations, assume the clicked region is background, or restore erased shapes for the Guesser. Use only boundaries and content that humans can currently see.

For a deterministic Quick, Draw! replay, take the current timestamp prefix, compute its current point bounds, and fit the longer side into 448 pixels on a 512x512 white working canvas. Draw each stroke separately with round caps/joins, using a 6-pixel line for validation/test and a seeded 3–12-pixel width variation for training. Draw a single-point stroke as a disk of radius half the line width. Render at twice that working resolution and downsample for antialiasing. Then apply the chosen shared shape preprocessor and 224-pixel fit/pad step. Do not connect strokes. A degenerate one-axis span uses the other axis for scaling; an entirely blank prefix is passed through as blank.

This is a documented rendering convention, not a reconstruction of Quick, Draw!'s original screen or brush settings, which the raw record does not specify. Live rendering still uses the actual canonical game operations and their actual tool sizes. Include line-width mismatch in synthetic checks.

### Select one shared preprocessor on validation

Data and Validation & Inference own a short validation pilot between these two **shape-based** candidates:

| Candidate | Concrete procedure | Strength | Failure case to inspect |
| --- | --- | --- | --- |
| P1: background-aware ink | Estimate a dominant border color from the current visible image; when it is sufficiently uniform, compute color distance from that background, map visible non-background shapes to dark ink, crop and pad | Similar to line-drawing training images; handles uniform colored backgrounds | Objects at the border, several background regions, fills that merge with the background, dense silhouettes |
| P2: color-boundary outlines | Compute spatial edges separately in the RGB channels, combine the edges, suppress the canvas-frame border, crop current visible boundaries and render them as dark lines on white | Retains visible boundaries despite background fill or equal-luminance colors | Double outlines on thick brush strokes; texture/noise; very thin or low-contrast shapes |

Implement P1 with a documented border sampling rule, quantization/tolerance, uniformity criterion and blank/dense-mask handling. An initial pilot setting is a 16-pixel border, 16-level/channel color quantization, >=70% dominant border-bin support and color-distance threshold 24/255. These are tunable starting values, not verified settings.

Apply those pixel measurements at a fixed max-side working resolution of 512, preserving aspect ratio. If P1 cannot identify a sufficiently uniform border background, mark the input as preprocessing-uncertain and pass. Do not quietly switch that individual image to an unvalidated P2 path. If a dispatch/fallback combination is later chosen, train and validate that exact combination as a new preprocessing version.

Implement P2 with a fixed max-side working image (for example 512), per-channel gradients/Canny, union of visible edges, then the same crop/pad/resize. Begin with Canny thresholds 50/150 and no more than a one-pixel canvas-frame suppression. Check thin strokes before locking thresholds. All choices must be causal and versioned.

For fair model comparisons, apply the chosen preprocessor to **both** synthetic Quick, Draw! canvases and live canvas snapshots. Do not train on plain strokes and change to edge outlines only in the API.

Choose P1 or P2 before the final complete-only versus partial-training runs. Use a small all-class validation subset and synthetic fill tests to choose. If a candidate fails, correct it and rerun the affected pilot, not the final test. Once chosen, package the exact code and fixture hashes as `preprocess_version`.

### Synthetic fill checks using existing drawings only

Start with training originals for augmentations and validation originals for preprocessing selection. Never transform a test drawing into training data.

Test at least:

- White background with dark strokes.
- Blue/purple/dark background with contrasting strokes.
- Yellow/red strokes on a white background.
- Two different colors with similar grayscale brightness.
- Fill inside an enclosed contour; preserve its external shape.
- Fill of a large background region.
- Erasure of visible content, undo/redo of a fill, and clear-to-blank.
- Very thick strokes, drawing touching a border, dense fill and low contrast.

For controlled synthetic recoloring/background changes, keep a known shape mask and compare normalized outputs against the white-background reference. This checks preprocessing invariance. Synthetic interior fills, erasures or overlays can change visible evidence: report them as separate stress cases, not automatic label-preserving copies.

Quick, Draw! lacks the game's actual fill/undo/eraser histories. Use deterministic renderer fixtures to test operation semantics and synthetic images to test color handling. This does **not** establish accuracy on real game drawings. If a fill removes the visible boundary by matching adjacent colors, the lost shape cannot be recovered from the screenshot. Passing is an acceptable model outcome.

### Final image and tensor contract

After the selected shape extraction:

1. Detect blank input and return a blank/pass result without neural guessing.
2. Use the current visible foreground/boundaries to find the bounding box.
3. Preserve aspect ratio; fit the longer side to 192 pixels and center in a 224x224 white image, leaving 16 pixels of margin on the longer side.
4. Use anti-aliased rendering/resizing. Do not stretch a 4:3 canvas directly into a square.
5. Repeat the grayscale shape image into three channels; values initially 0–1.
6. Normalize using the selected checkpoint's configuration.

For the recommended timm checkpoint, the inspected config is `input_size=[3,224,224]`, `mean=[0.5,0.5,0.5]` and `std=[0.5,0.5,0.5]`. This produces approximately -1 for black and +1 for white. Do not substitute the commonly used ImageNet mean/std without checking this checkpoint.

The checkpoint's generic inference pipeline includes a center crop. Use the explicit sketch fit/pad transform above instead, identically in training and serving; do not let an additional default crop cut off drawing boundaries. For training, add modest line-width variation, translation/scale and rotations up to about +/-10 degrees. Avoid flips for directional classes, random crops that remove the object, and unrelated image mixing that creates ambiguous targets.

## 9. Model choice and training work

### Recommended starting checkpoint

`timm/vit_tiny_patch16_224.augreg_in21k_ft_in1k`

Its [model card](https://huggingface.co/timm/vit_tiny_patch16_224.augreg_in21k_ft_in1k) describes a 224x224 ViT with about 5.7M parameters, pretrained on ImageNet-21k and fine-tuned on ImageNet-1k. It is **not already a Quick, Draw! classifier**. Your group supplies the 345-category head and sketch adaptation.

The recommendation is based on the fixed-vocabulary task, transformer requirement, local GPU constraints and one-week horizon. It is not an experimentally established “best model” for your game.

~~~python
import timm
import torch

torch.manual_seed(198173)
model = timm.create_model(
    "vit_tiny_patch16_224.augreg_in21k_ft_in1k",
    pretrained=True,
    num_classes=345,
)
model.eval()
with torch.inference_mode():
    assert model(torch.zeros(2, 3, 224, 224)).shape == (2, 345)
~~~

The [timm API](https://huggingface.co/docs/timm/quickstart) supports replacing the classifier with `num_classes`. Save the initial head state or identical initialization seed for the controlled training comparison.

### Alternatives considered

| Option | Why it is not the primary one-week plan |
| --- | --- |
| Object detection model | Requires localization targets the Guesser does not need; your supervision is an intended category for the whole canvas |
| [Sketchformer](https://github.com/leosampaio/sketchformer) | A relevant pretrained stroke transformer, but its documented setup is older TensorFlow and Quick, Draw! stroke preprocessing; pretrained-data overlap must be checked, and edit/fill state requires extra handling |
| [Community BEiT sketch classifier](https://huggingface.co/kmewhort/beit-sketch-classifier) | Already sketch-adapted, but documented Quick, Draw! pretraining makes unseen-test provenance important; a new random split from the same corpus cannot automatically be called unseen |
| [Qwen3-VL-2B](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct) | Fits broader language/visual reasoning questions, but is more complex than this fixed 345-label classifier requires; no local sketch latency advantage was measured |
| [DeiT-Tiny](https://huggingface.co/facebook/deit-tiny-patch16-224) | Sensible transformer fallback if the chosen timm checkpoint has loading problems; do not spend the week training many backbones |

Sketch-RNN is mainly a sketch-generation representation/model family, not a ready answer-word classifier to adopt without additional classification work. A separate stroke/timing transformer is future experimentation, not required simply because raw timestamps exist.

### Two controlled runs

- **A — complete-only baseline:** fine-tune the pretrained ViT on complete drawings only.
- **B — partial-trained adaptation:** same backbone, originals, initialization, optimizer budget and image preprocessing; use the 20% full / 80% timestamp-prefix view recipe.

Train independently from the same pretrained initialization. Do not give B extra training updates and attribute the entire improvement to partial examples. If you later do A -> B continued adaptation, add a continued-complete control with the same additional updates.

Starting configuration for both:

| Setting | Working value |
| --- | --- |
| Loss | Cross-entropy over 345 intended labels |
| Optimizer | AdamW |
| Head LR | 1e-3 |
| Backbone LR | 1e-4; reduce if unstable |
| Weight decay | 0.01 |
| Warmup | First 5% of the agreed update budget |
| Effective batch | 32; e.g. physical 8 x accumulation 4 |
| Epoch ceiling | 6, with best-validation checkpoint and patience 2 |
| Schedule | Warmup then cosine decay, identical across A/B |
| Precision | Begin with a successful FP32 run; use tested FP16 autocast/scaling if stable on the actual GPU |
| Loader | Start with 0 workers for debugging; then 2–4 workers after measuring Windows RAM/CPU use |
| Seed | 198173, including samplers and augmentation |

Run a small overfit check and an all-345-class smoke set before the full experiment. Check loss decreases, label mapping is correct, gradients are finite and padded blank images do not become confident release candidates.

Time a representative training interval, including rendering/loading, before committing to six epochs. If the ceiling exceeds the available time, fix an equal step budget for A and B in advance, keep balanced sampling across **all 345** classes, and report the actual budget. Do not quietly remove difficult categories.

Data can produce the smoke package while the full source scan runs. The baseline and adapted run can use separate laptops; final serving uses one frozen model, not a three-laptop distributed inference requirement.

## 10. Validation and final testing

### Keep tuning and testing distinct

Use validation for architecture/preprocessor pilots, epoch selection, temperature calibration and pass thresholds. Once these are frozen, run the chosen model and the fixed baseline on the final test. Do not retune after seeing test errors and still describe that same test as untouched.

For fast epoch selection, use a deterministic validation subset such as 50 originals/class. Use the full 500/class validation set for final validation/calibration and the full held-out 500/class test set once. Generate views on demand or cache a bounded number of shards, rather than writing millions of small image files.

### Detailed model-validation procedure

The Validation & Inference owner leads this procedure with the model owner's frozen checkpoints. Validation is an offline recognition-quality task; the latency/load protocol below is a separate runtime task.

1. **Audit inputs before scoring.** Confirm train/validation/test ID and trajectory-hash disjointness, all 345 labels, and exactly 500 validation originals per class. Validate timestamp cuts and current-prefix-only crop bounds. A manifest/parser failure must be fixed and counted, not silently omitted from the denominator.
2. **Build identical held-out views.** Each original produces ten fixed time prefixes: 10% through 100%. Full validation therefore has 172,500 originals and 1,725,000 views per model pass. A fixed 50-per-class subset has 17,250 originals and 172,500 views for fast epoch checks. Preserve this same subset, view recipe and image hashes across A and B.
3. **Run evaluation mode.** Use `model.eval()` and `torch.inference_mode()`, with no optimizer step, stochastic training augmentation or training-time dropout. Run A and B against the same inputs, output registry and scoring code.
4. **Write one offline result row per view.** Include drawing ID, true class ID, time fraction/cutoff, input hash, checkpoint identity, preprocessor version, raw top-k logits/IDs, blank status and any passing-policy result. The true label is available only to the offline evaluator; it never enters the live inference request.
5. **Inspect learning after each epoch.** Record training loss, validation cross-entropy on nonblank evaluable images, and the early-recognition score. Keep blank stages visible in end-to-end recognition metrics. If training improves while validation quality declines, inspect overfitting and use the best validation checkpoint rather than the latest weights. Keep the same checkpoint-selection rule and patience for A and B.
6. **Evaluate full validation before final selection.** Report all ten stage accuracies, mean early accuracy, complete-image top-1/top-3, per-class support/confusions and uncertainty grouped by original drawing. Compare candidates with the equal-budget rule from Section 9.
7. **Calibrate passing on validation only.** Fit any scalar temperature using validation logits and intended labels with model weights fixed. Sweep candidate confidence thresholds, for example 0.00–0.95 in 0.05 increments, and record the resulting accuracy/coverage tradeoff. A finer sweep is allowed on validation, never on test. Keep blank/preprocessing-uncertain passes deterministic.
8. **Freeze and record the decision.** Save weights/hash, labels/hash, preprocessor, calibration, pass threshold, public-hint policy and selection rationale. If hint filtering is used, assess it separately; a hint-normalized score must not be presented as visual confidence.
9. **Run final testing on different originals.** Only after freezing, evaluate A and the chosen candidate on the 172,500 final-test originals and the fixed ten-stage grid. Report the fixed protocol even if the results are disappointing. Changing a candidate after studying test errors means the original untouched-test claim no longer applies.

#### Metric definitions and denominators

- **Stage top-1:** correct unthresholded top-ranked classifications at that stage divided by the number of original drawings. In the end-to-end recognition curve, a blank stage has no valid recognition and counts as unsuccessful. This curve is separate from the passing policy.
- **Mean early top-1:** the arithmetic mean of the nine stage accuracies from 10% through 90%, with macro class averaging. Because the planned class counts are equal, class-balanced and overall stage averaging coincide until any missing/invalid examples are accounted for.
- **Complete top-1/top-3:** use the final recorded view. Top-3 membership is a ranking diagnostic; it does not authorize extra counted game guesses.
- **Policy coverage:** number of emitted guesses divided by all evaluated opportunities, including passes.
- **Accuracy among emitted guesses:** correct emitted guesses divided by emitted guesses. If no guesses are emitted, report undefined/null, not 100%.
- **Overall policy correctness:** correct emitted guesses divided by all evaluated opportunities. Report this with coverage and conditional accuracy so a high pass rate cannot conceal an ineffective Guesser.
- **Validation loss:** a diagnostic for learning/calibration on valid nonblank model inputs. Report its denominator; do not replace the early-recognition objective with loss alone.
- **Uncertainty:** resample whole original drawings within class, keeping all their stages together. Report paired A/B differences on the same drawings, not uncertainty as if every prefix were an unrelated sample.

The illustrative +5-point early-accuracy goal and <=2-point complete-image-loss guard are comparison goals. They do not replace the full score report, constitute a promised accuracy, or justify test-based tuning.

#### Validation owner's concrete handoff

| Deliverable | Minimum contents |
| --- | --- |
| Stage-level metrics | A/B top-1 at every fraction, early mean, complete top-3, original/view counts and blank counts |
| Error analysis | All-class support/accuracy, major confusions and reproducible drawing/view IDs |
| Prediction records | Offline per-view rows or a documented reproducible equivalent |
| Policy evaluation | Calibration, pass thresholds, coverage, conditional accuracy and overall correctness |
| Candidate-freeze record | Model, registry, manifest and preprocessing hashes; chosen checkpoint and selection rule |
| Final-test report | Same fixed metrics on the untouched original-drawing test split, with grouped uncertainty |

Generate recognition-versus-progress plots from actual evaluation outputs. Before experiments run, report the result fields as not run/null; do not insert made-up scores into the planning visualization.

### Recognition measures

Report the following on **sketch-only** input first:

- Top-1 accuracy at every fraction 10%–100%.
- Mean early top-1 accuracy across 10%–90%, with macro class averaging.
- Complete-drawing top-1 and top-3 accuracy.
- Per-class support/accuracy and major confusion pairs; all 345 classes remain in the report.
- Blank-stage/pass rate and uncertain-pass rate.
- Accuracy among emitted guesses together with coverage, so passing cannot inflate an isolated accuracy number.
- Recognition trajectory: first correct stage and, separately, first stage followed by correct predictions at the next observed stage. Report failures/censoring rather than dropping unsolved drawings.

Top-3 accuracy is a diagnostic. Returning three labels in an internal response is not permission to count three game guesses.

A reasonable provisional adaptation goal is +5 percentage points in mean early top-1 over A, while losing no more than 2 points on complete-drawing accuracy. This is a project goal for comparison, not a required class rule or a known achievable result. If it is missed, report the result and select the better validated candidate; do not manufacture a positive finding.

Compute uncertainty by resampling whole drawings within class (e.g. a stratified bootstrap). Keep all ten views together in each resample. Do not treat 1.725M correlated prefix images as that many independent test drawings.

### Hints and game behavior

Report a second, explicitly **hint-assisted** evaluation if a reproducible hint schedule is simulated. Filter label candidates using only the same public word length/letter pattern humans receive. Keep the sketch-only result separate.

The vision network remains image-only. Log raw image scores separately from hint-filtered ranking. Softmax renormalization over a one-label hint set is not evidence of strong visual confidence. Choose and freeze the passing policy on validation, and report hint candidate-set sizes and pass coverage.

This is a closed-vocabulary classifier. Low-confidence passing is not a guaranteed detector of unsupported concepts or meaningless marks; those can still produce confident errors. Keep all playable prompts mapped to the frozen 345-label registry.

### Latency and capacity

On the intended inference laptop, with weights already loaded:

- Warm up before timing steady-state inference; report cold startup separately.
- Time canonical capture/render, preprocessing, queue wait, GPU inference, postprocessing and result receipt.
- Report p50/p95 and failures under one, two and three simultaneous team streams at the proposed cadence.
- Include scheduled jobs during the frequent-update traffic; verify they are not starved.
- Target p95 snapshot-to-result <= 1 second for three teams.
- Use one host clock for each measured interval or calibrated cross-host tracing. Do not subtract unrelated laptop clocks.
- Confirm that lowering precision, changing batching, exporting or quantizing does not silently change rankings beyond the documented tolerance. Export/quantization is optional for this deadline.

No new player data will be collected. Consequently the evaluation establishes Quick, Draw! held-out performance and synthetic robustness checks. It does not establish accuracy, fairness or human-beatable difficulty on actual player sketches.

## 11. Live inference and counted attempts

### Runtime flow

1. The existing Next.js canvas sends operations to the authoritative NestJS game backend.
2. NestJS freezes a current canonical canvas version and public hint version.
3. Respect the existing observation barrier: active human guessers must have rendered the permitted versions before their release to the AI.
4. A worker creates the visible snapshot; FastAPI applies the versioned shape preprocessor.
5. A resident ViT produces 345 logits.
6. Postprocessing applies public hint constraints and the frozen pass/guess policy.
7. Return version-tagged recognition information.
8. NestJS alone decides whether this is a scheduled attempt, validates it, checks the hidden target and updates game state.
9. Save input identity, model/policy versions and timing for replay/evaluation.

The model service must not receive the secret answer, human guess text, opposing canvases or a database connection that exposes those labels. Training labels belong outside live model-visible input. Official hints are permitted; the target is not.

### Frequent recognition is not a counted guess

- At most one frequent-update request per active team per second; skip unchanged snapshots.
- Bound pending work; replace/coalesce obsolete unstarted recognition jobs.
- Scheduled attempts have priority over background recognition updates.
- Use only the checkpoint's frozen canvas/hint versions for its counted decision.
- Reuse a cached result only for the exact permitted image/input versions, hash, model and preprocessing/policy revision. Do not use a newer snapshot or future hint, or smooth a checkpoint prediction with later observations.
- The initial model is stateless across images. Temporal smoothing is deferred.
- Hidden recognition updates must be tagged separately from official attempts in logs and replay.
- AI guess text stays hidden from players until the existing reveal/replay stage; progress indicators can update.

### Pass, failure and cancellation are different

At each scheduled opportunity, emit either one canonical word or a pass. A blank or low-confidence pass consumes that opportunity and creates no replacement checkpoint. It is a normal policy outcome, not an inference outage.

A real timeout/service error is a failed required attempt and follows the existing backend outage/bonus rules. A human solve, forfeit, timeout, voided round, generation change or prior AI solve cancels further relevant work. A late response cannot score retrospectively.

Keep round duration, opportunity times, deadlines and pass thresholds in configuration. The example six-opportunity schedule leaves the last two seconds for a response before the round deadline; the backend must still reject results that actually arrive too late.

### Proposed service contract

This is a contract to implement, not an existing endpoint.

~~~json
{
  "job_id": "unique-job",
  "match_id": "match",
  "round_id": "round",
  "round_generation": 1,
  "team_id": "team",
  "kind": "recognition_update",
  "checkpoint_id": null,
  "canvas_version": 123,
  "hint_version": 2,
  "snapshot_sha256": "hash",
  "image": "canonical image bytes or an agreed internal binary upload",
  "public_hint": {"pattern": "_ a _", "word_length": 3},
  "deadline": "backend-defined deadline",
  "preprocess_version": "shape-v1"
}
~~~

For a counted attempt, `kind` is `scheduled_attempt` and a checkpoint identity is required. Retain the server-instance identity required by the existing game design as well.

Return `job_id` and the same generation/team/input versions, `model_version`, `preprocess_version`, `policy_version`, candidate class IDs/scores, `decision=guess|pass`, the chosen canonical class ID when applicable, pass reason and stage timing. A top-k list is for diagnostics; only the chosen word is one game answer.

Load weights once on service startup; call `model.eval()` and use `torch.inference_mode()`. Start with a single bounded GPU worker. Microbatch up to three compatible jobs only if the load test confirms deadlines. FastAPI handles validation/admission; it must not block the game event loop or award points.

## 12. Parallel seven-day work plan

Day numbers mean work sessions from the agreed start. Fix the actual submission date in your group calendar.

| Day | Data — you | Model | Validation & Inference |
| --- | --- | --- | --- |
| 1 | Freeze 345-label registry, source inventory, cleaning/split recipe; full-class throughput probe; begin source scan | Verify CUDA and checkpoint; build 345-head model and loader against smoke records | Build input/output schemas and dummy API; prepare split-audit and render/fill fixtures |
| 2 | Continue scan; deliver indexed smoke subset across all 345 classes; preprocessing pilot inputs | Overfit/smoke checks; measure training throughput and agree equal A/B budget | Audit labels/splits; compare P1/P2 on validation pilot and synthetic fills; freeze shared preprocessor with Data |
| 3 | Complete scan, duplicate/refill checks and QA; freeze manifests; hand off packages | Start complete-only baseline A and partial-trained B from same initialization | Build resident model worker, pass policy harness, checkpoint/version handling |
| 4 | Resolve preparation defects without touching test-based decisions; finalize data receipt | Continue runs; choose checkpoints using validation only | Generate stage-wise validation metrics; integrate public hint filtering; first three-team load run |
| 5 | Help inspect training/validation failures and package reproducible data recipe | Finish/freeze candidate; deliver complete model package | Calibrate/select passing policy on validation; rerun fill/renderer and end-to-end checks |
| 6 | Verify artifact hashes and data reproducibility | Support inference parity; no test-driven retraining | Run final held-out evaluation for frozen A/B, synthetic stress report and timed three-team demo |
| 7 | Final data documentation and attribution | Final training/ablation write-up | Demo rehearsal, failure handling, final results and limitations; buffer for integration fixes |

If source scanning takes longer, Model and Validation & Inference continue with the all-class smoke package and dummy/service fixtures. All-345 coverage, frozen split integrity and honest reporting remain required. Reduce equal training steps or optional export work before removing categories or using test data for tuning.

## 13. Release package and completion checks

The model owner hands the inference owner:

~~~text
guesser-model/
  weights.safetensors
  model-config.json
  labels.json
  preprocess-config.json
  policy-config.json
  training-config.json
  dataset-receipt.json
  requirements.lock.txt
  validation-report.json
  model-card.md
~~~

These are intended training/inference deliverables for the group, distinct from the two planning documents delivered in this chat.

Completion checklist:

- [ ] Registry has all 345 source categories, unique IDs and a recorded checksum.
- [ ] Full-file sampling receipts and actual sample counts are recorded.
- [ ] Cleaning and exact-duplicate rules are applied and counted.
- [ ] Every class has 4,000/500/500 original drawings, or preparation visibly fails for refill.
- [ ] No original/trajectory group crosses train/validation/test.
- [ ] Prefixes use only available points; crop/scale never use future bounds.
- [ ] One preprocessor is frozen for both training and serving; background-fill fixtures are checked.
- [ ] Input tensor and 345-output registry agree on all three machines.
- [ ] A/B runs have a comparable update budget and validation-only checkpoint selection.
- [ ] Final-test report covers all 345 classes and keeps views grouped statistically.
- [ ] Passing reports both accuracy and coverage.
- [ ] Scheduled decisions use permitted frozen input and cannot score after a deadline/cancellation.
- [ ] One/two/three-team latency and failure tests are recorded.
- [ ] Quick, Draw! attribution and actual experiment limitations are included.
- [ ] Model/version hashes, recipes and final demo instructions are packaged.

## 14. Evidence, decisions and remaining empirical work

### Verified during this planning session

- Read the current game design, glossary, frontend drawing contract and fill behavior.
- Verified the raw source shape using small cat/bicycle/alarm-clock ranges.
- Verified that the bitmap cat file header is uint8 [123202, 784].
- Queried the raw source object inventory and total byte size.
- Read the recommended model card and inspected its actual preprocessing config.
- Read official PyTorch/timm setup guidance.
- Completed the decision interview reflected in Section 1.
- Checked syntax of the included Python snippets and exercised the reference cleaner, seeded sampler/checksum logic, deterministic 4,000/500/500 split and timestamp cuts with local fixtures. The full-source preparation and PyTorch training snippets were not executed end to end.
- Browser-checked the companion visualization at 1440-pixel desktop and 390-pixel narrow widths, in light and dark desktop appearances; verified replay controls, same-color blank handling and diagram text fit. The review page uses the game's Lemon Crayon design source.

### To be implemented/measured by the group

Full data preparation, the P1/P2 preprocessing pilot, actual model training, A/B comparison, calibration, final test and three-team inference benchmarking. In particular, background-aware processing is a required experiment, not an already proven fix. No accuracy percentage or completed training claim is made here.

### Primary references

- [Quick, Draw! data and formats](https://github.com/googlecreativelab/quickdraw-dataset)
- [Official 345 category registry](https://raw.githubusercontent.com/googlecreativelab/quickdraw-dataset/master/categories.txt)
- [Public raw-object inventory](https://storage.googleapis.com/storage/v1/b/quickdraw_dataset/o?prefix=full%2Fraw%2F&maxResults=1000)
- [Quick, Draw! CC BY 4.0 attribution](https://github.com/googlecreativelab/quickdraw-dataset#license)
- [ViT-Tiny checkpoint card](https://huggingface.co/timm/vit_tiny_patch16_224.augreg_in21k_ft_in1k)
- [Checkpoint configuration](https://huggingface.co/timm/vit_tiny_patch16_224.augreg_in21k_ft_in1k/blob/main/config.json)
- [timm loading and classifier adaptation](https://huggingface.co/docs/timm/quickstart)
- [Official PyTorch version/install pairs](https://pytorch.org/get-started/previous-versions/)
- [Sketchformer official implementation](https://github.com/leosampaio/sketchformer)

Use an attribution such as: “Drawings sourced from the Google Quick, Draw! Dataset, Google Creative Lab, CC BY 4.0; sampled, cleaned and rendered into partial views by the project team.” Link the [license](https://creativecommons.org/licenses/by/4.0/) and record the transformations in the dataset/model card.

Local owning design sources inspected: `E:\BSCS 4th Year\CSC173\group-project\SYSTEM-DESIGN.md`, `CONTEXT.md`, `apps\web\src\contracts\drawing.ts`, `apps\web\src\features\canvas\DrawingCanvas.tsx` and `fill.worker.ts`. The output artifact uses that project's Lemon Crayon design system. The game repository was read for context; this planning work does not modify it.

## 15. Reference functions for the data owner

These standard-library functions make the sampling, cleaning, splitting and timestamp rules concrete. Copy them into the preparation implementation, then add the orchestration, atomic class receipts, on-disk duplicate index and indexed-record writer described above. They are not a complete multi-class command-line application.

The sampler reads **a whole source object**. Do not call it in an exploratory notebook unless you intend that download. Fetch the category's metadata from the saved source inventory and pass it as `source_meta`.

~~~python
import base64
import hashlib
import heapq
import json
import math
import urllib.parse
import urllib.request
from collections import Counter

SEED = 198173

def priority(namespace, drawing_id):
    text = f"{namespace}|{SEED}|{drawing_id}"
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest(), "big")

def clean_record(record, expected_word):
    if not isinstance(record, dict):
        raise ValueError("not_object")
    drawing_id = record.get("key_id")
    if not isinstance(drawing_id, str) or not drawing_id:
        raise ValueError("invalid_id")
    if record.get("word") != expected_word:
        raise ValueError("word_mismatch")
    drawing = record.get("drawing")
    if not isinstance(drawing, list) or not drawing:
        raise ValueError("empty_drawing")

    cleaned = []
    repairs = Counter()
    last_time = -1
    first_xy = None
    has_extent = False
    first_time = None
    for stroke in drawing:
        if not isinstance(stroke, list) or len(stroke) != 3:
            raise ValueError("stroke_axes")
        xs, ys, ts = stroke
        if not all(isinstance(axis, list) for axis in (xs, ys, ts)):
            raise ValueError("axis_not_list")
        if not (len(xs) == len(ys) == len(ts)):
            raise ValueError("axis_lengths")
        if not xs:
            repairs["empty_stroke_removed"] += 1
            continue
        out_x, out_y, out_t = [], [], []
        previous_triple = None
        for x, y, t in zip(xs, ys, ts):
            if any(isinstance(v, bool) or not isinstance(v, (int, float))
                   for v in (x, y)):
                raise ValueError("coordinate_type")
            x, y = float(x), float(y)
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValueError("nonfinite_coordinate")
            if isinstance(t, bool) or not isinstance(t, int) or t < 0:
                raise ValueError("time_type_or_negative")
            if t < last_time:
                raise ValueError("time_decreased")
            last_time = t
            if first_time is None:
                first_time = t
            if first_xy is None:
                first_xy = (x, y)
            has_extent = has_extent or (x, y) != first_xy
            triple = (x, y, t)
            if triple == previous_triple:
                repairs["exact_point_duplicate_removed"] += 1
                continue
            out_x.append(x)
            out_y.append(y)
            out_t.append(t)
            previous_triple = triple
        if out_x:
            cleaned.append([out_x, out_y, out_t])

    if not cleaned or not has_extent:
        raise ValueError("no_geometric_extent")
    if first_time is None or last_time <= first_time:
        raise ValueError("zero_duration")
    result = dict(record)
    result["drawing"] = cleaned
    return result, repairs

def trajectory_hash(record):
    # Coordinates have been canonicalized to finite floats; times remain ints.
    packed = json.dumps(record["drawing"], separators=(",", ":"),
                        allow_nan=False).encode("utf-8")
    return hashlib.sha256(packed).hexdigest()

def sample_full_category(word, source_meta, keep=5500):
    url = ("https://storage.googleapis.com/quickdraw_dataset/full/raw/"
           + urllib.parse.quote(word, safe="") + ".ndjson")
    heap = []  # negative priority -> worst retained priority at heap[0]
    retained_ids = {}
    stats = Counter()
    source_md5 = hashlib.md5()
    source_sha256 = hashlib.sha256()
    received = 0

    with urllib.request.urlopen(url, timeout=60) as response:
        expected_generation = str(source_meta.get("generation", ""))
        actual_generation = response.headers.get("x-goog-generation", "")
        if expected_generation and actual_generation != expected_generation:
            raise RuntimeError("Source generation changed; refresh inventory")
        for line in response:
            source_md5.update(line)
            source_sha256.update(line)
            received += len(line)
            stats["source_lines"] += 1
            try:
                record, repairs = clean_record(json.loads(line), word)
            except (ValueError, TypeError, OverflowError, RecursionError) as exc:
                stats["rejected:" + str(exc)] += 1
                continue
            stats["structurally_valid"] += 1
            stats.update(repairs)
            drawing_id = record["key_id"]
            score = priority("select-v1", drawing_id)
            if drawing_id in retained_ids:
                geom = trajectory_hash(record)
                if retained_ids[drawing_id] != geom:
                    raise RuntimeError("Conflicting retained drawing ID")
                stats["retained_id_duplicate"] += 1
                continue
            # Hash/sample membership is independent of file order.
            if len(heap) == keep and score >= -heap[0][0]:
                continue
            geom = trajectory_hash(record)
            encoded = json.dumps(record, separators=(",", ":"),
                                 allow_nan=False)
            item = (-score, drawing_id, geom, encoded)
            if len(heap) < keep:
                heapq.heappush(heap, item)
            else:
                removed = heapq.heapreplace(heap, item)
                retained_ids.pop(removed[1], None)
            retained_ids[drawing_id] = geom

    if received != int(source_meta["size"]):
        raise RuntimeError("Source size mismatch or interrupted download")
    actual_md5 = base64.b64encode(source_md5.digest()).decode("ascii")
    if source_meta.get("md5Hash") and actual_md5 != source_meta["md5Hash"]:
        raise RuntimeError("Source MD5 mismatch")
    if len(heap) < keep:
        raise RuntimeError("Too few eligible candidates; inspect category")

    ordered = sorted(heap, key=lambda item: (-item[0], item[1]))
    candidates = [
        {"priority_hex": format(-neg_score, "064x"), "drawing_id": drawing_id,
         "trajectory_hash": geom, "record": json.loads(encoded)}
        for neg_score, drawing_id, geom, encoded in ordered
    ]
    receipt = {
        "word": word, "source_bytes": received,
        "source_generation": source_meta.get("generation"),
        "source_sha256": source_sha256.hexdigest(),
        "source_md5": actual_md5, "seed": SEED,
        "retained_candidates": len(candidates), "counts": dict(stats),
    }
    return candidates, receipt

def split_one_class(records):
    # Call ONLY after global ID/trajectory conflict checks and reserve refill.
    if len(records) != 5000:
        raise ValueError("Expected exactly 5000 deduplicated originals")
    ids = [r["key_id"] for r in records]
    hashes = [trajectory_hash(r) for r in records]
    if len(set(ids)) != 5000 or len(set(hashes)) != 5000:
        raise ValueError("Duplicate originals remain in this class")
    ordered = sorted(records,
                     key=lambda r: (priority("split-v1", r["key_id"]),
                                    r["key_id"]))
    return {"train": ordered[:4000],
            "validation": ordered[4000:4500],
            "test": ordered[4500:]}

def time_prefix(record, fraction):
    if not 0 <= fraction <= 1:
        raise ValueError("fraction outside [0,1]")
    strokes = record["drawing"]
    t0 = strokes[0][2][0]
    t1 = strokes[-1][2][-1]
    cutoff = t0 + fraction * (t1 - t0)
    output = []
    for xs, ys, ts in strokes:
        n = 0
        while n < len(ts) and ts[n] <= cutoff:
            n += 1
        if n:
            output.append([xs[:n], ys[:n], ts[:n]])
    return output
~~~

The cross-class duplicate index must be persistent, such as SQLite, rather than a giant list of all decoded drawings:

1. Write each class's 5,500 candidates to staging in priority order.
2. Scan staged hashes into a table keyed by trajectory hash and record the class ID; mark a conflict when that exact hash occurs under different labels. Maintain a second ID index for inconsistent/cross-class IDs.
3. For each class, walk its ranked candidates, reject globally conflicting IDs/hashes, and keep the first 5,000 unique eligible trajectories.
4. Call `split_one_class`; write the records and manifest rows, tracking actual byte offsets in binary write mode.
5. Check all manifest IDs and hashes for disjointness, and write the immutable receipt.
6. Only then expose the package for complete experiments.

A minimal record-offset writer uses `offset = output.tell()` before `output.write(json_bytes + b"\n")` and records the exact byte length including the newline. Always serialize with UTF-8 explicitly. Validate random-access reads against a sample of manifest rows.

When implementing the sampler's orchestrator, retry a failed class without keeping a misleading success receipt. Do not rerun completed classes with changed source inventory or seed and combine their records under the same dataset version.


