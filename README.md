# CISC3024 AI Assignment 3 RSSPCA reproduction

AI-generated Python reproduction of **Robust sparse smooth principal component analysis
for face reconstruction and recognition**, Wang et al., PLOS ONE 20(5), e0323281 (2025).
Paper: https://doi.org/10.1371/journal.pone.0323281
Upstream MATLAB: https://github.com/yuzhounh/RSSPCA

The assignment, numerical tests, experiments, figures, and English report were produced
by Codex. The student is not required to write or execute code. These instructions are
provided for independent reproducibility.

## Recorded results

ORL author-provided 56 x 46 faces; 40 subjects; 7 training and 3 test images per
subject, independently repeated with seeds 2026, 3024, and 77. All algorithms use
the same splits, training-fitted z-scores and Euclidean 1-nearest-neighbor classifier.

| Method | Accuracy at 30 components, mean +/- sample SD | Occluded reconstruction MSE |
|---|---:|---:|
| PCA | 97.50% +/- 2.50 percentage points | 0.006925 |
| PCA-L1 | 97.22% +/- 2.93 percentage points | 0.007007 |
| RSSPCA | 97.22% +/- 2.68 percentage points | 0.006522 |

Reconstruction uses seed 2026, 20% contaminated training images and a 14 x 12
salt-and-pepper block in every test image. Clean test images remain ground truth.
No test data are used to select parameters. These are independent assignment
results, not published results copied from the paper. RSSPCA does not outperform
PCA in mean recognition accuracy here.

## Reproduce

Use Python 3.12. The actual recorded environment is in `results/environment.json`.
In a fresh checkout, create a virtual environment and install `requirements.txt`.
The following PowerShell commands are for a reviewer, not a student obligation:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B tools/fetch_resources.py
.\tools\run_experiments.ps1
.\.venv\Scripts\python.exe -B -m tools.audit_results
```

For the recorded run, an existing scientific Python installation was reused through
a dedicated D: virtual environment with system packages. Only threadpoolctl 3.6.0
was installed into that virtual environment to fix an incompatible old installation.
Temporary files and plotting/package caches were directed to the project's `tmp`.
`threadpoolctl` limits numerical libraries to one thread for timing and repeatability.

The full experiment took about 83 seconds in the recorded environment. Timings are
single observations; they include initialization/SVD but exclude data download and I/O.
Do not interpret millisecond differences as stable benchmark rankings.

## Protocol

- Recognition inner split: 5 training and 2 validation images per class, drawn only
  from each outer training partition. Each 9-point RSSPCA grid is scored at k=20.
- Classification eta1: 0.001, 0.01, 0.1; eta2: 0.1, 10, 1000.
- Final dimensions: 5, 10, 20, 30, prefix columns from one 30-component fit.
- Reconstruction has separate tuning and separate fitted models. Its eta1 grid is
  0.00001, 0.001, 0.1; eta2 is 0.1, 1, 10. It minimizes validation MSE on noisy inputs.
- Reconstruction uses mean-centering without z-score, one split, no metric clipping,
  and a pseudoinverse projector to handle nonorthogonal RSSPCA directions.
- Reconstruction test noise seeds and affected image/block positions are preserved
  locally in `results/noise_manifest.json`; split indices are in `results/splits.json`.
- Original MATLAB stopping monitor and cumulative deflation are retained. Two final
  RSSPCA recognition components on seed 3024 reach the 100-iteration cap. The scalar
  L2 monitor does not certify a stationary optimum of the L1 constrained problem.
- No MATLAB engine was run: reference verification uses an independent literal dense
  Python transcription and comparisons to the paper's algebraic equivalent formula.

## Project map

`src` contains algorithms, preprocessing, metrics and plotting. `experiments/run_all.py`
runs both experiments from `experiments/configs/main.json`. `tests` contains numerical
checks. `tools/audit_results.py` recomputes saved metrics and replays one final fit.
`results` contains CSV measurements, split indices, optimization traces, provenance,
verification and figures. `AI_Process_Log.md` records the real workflow.
`references/mathematical_validation.md` explains exact equation and code correspondence.
`submission` contains the local Word/PDF reports and submission notes.

## Data and licenses

Download the ORL resource with `tools/fetch_resources.py`. Its byte hash, shape, label
counts, source and usage metadata are checked and documented in `data/source_and_license.md`.
Raw faces, derived image-bearing arrays and report files are not distributed in this
public code package. The local report credits ORL/AT&T and the author's Figshare resource.

Derived code is GPL-3.0-only; full terms are in `LICENSE`. Original MATLAB reference
files and attribution are preserved in `references/upstream`. Read `THIRD_PARTY_NOTICES.md`.

## Report generation

`tools/build_report.py` uses python-docx from the Codex bundled workspace runtime.
`tools/render_report.py` uses the documents skill's renderer, a local portable LibreOffice
and bundled Poppler. Report dependencies are separate from the scientific environment.
Render and inspect every page before submitting. The reports are not automatically
submitted to Moodle.
