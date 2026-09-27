"""
Evaluate the detector on the IR-Plag dataset (Karnalim et al., 2019).

    python evaluate.py path/to/IR-Plag-Dataset            # structural + semantic
    python evaluate.py path/to/IR-Plag-Dataset --no-model # structural only (fast, no download)

Each case = one assignment: 1 original, 15 independent (non-plagiarized) solutions,
and plagiarized copies of the original at levels L1-L6 (Faidhi & Robinson, 1987):
  L1 comments/whitespace   L2 identifiers renamed    L3 declarations moved
  L4 methods restructured  L5 statements reordered   L6 control logic changed
We compare the original against every other file and measure what gets flagged.
Results are printed and written to results/evaluation.md.
"""
import os
import sys
import glob
import time
import numpy as np
from fingerprint import tokenize, fingerprints, jaccard

LEVELS = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'NON']
STRUCT_THRS = [0.5, 0.6, 0.7, 0.8]
SEM_THRS = [0.85, 0.90, 0.95]


def label_of(path):
    p = path.replace('\\', '/')
    if '/plagiarized/' in p:
        return p.split('/plagiarized/')[1].split('/')[0]
    return 'NON' if '/non-plagiarized/' in p else 'ORIG'


def auc(pos, neg):
    """Probability that a random plagiarized pair scores higher than a random independent pair."""
    if not pos or not neg:
        return float('nan')
    pos, neg = np.array(pos), np.array(neg)
    return float(((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum())
                 / (len(pos) * len(neg)))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    root, use_model = sys.argv[1], '--no-model' not in sys.argv
    model = None
    if use_model:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        from detect import encode_long, MODEL_NAME
        model = SentenceTransformer(MODEL_NAME)

    scores = {'Structural': [], 'Exact': [], 'Semantic': []}   # lists of (level, score)
    t0 = time.time()
    for case in sorted(os.listdir(root)):
        files = sorted(glob.glob(os.path.join(root, case, '**', '*.java'), recursive=True))
        if not files:
            continue
        codes = [open(f, encoding='utf-8', errors='replace').read() for f in files]
        labels = [label_of(f) for f in files]
        o = labels.index('ORIG')
        fp = [fingerprints(tokenize(c, f)) for c, f in zip(codes, files)]
        fe = [fingerprints(tokenize(c, f, ignore_names=False)) for c, f in zip(codes, files)]
        sem = cosine_similarity(encode_long(model, codes)) if model else None
        for i, lab in enumerate(labels):
            if i == o:
                continue
            scores['Structural'].append((lab, jaccard(fp[o], fp[i])))
            scores['Exact'].append((lab, jaccard(fe[o], fe[i])))
            if model:
                scores['Semantic'].append((lab, float(sem[o][i])))
        print(f"{case}: {len(files)} files")
    elapsed = time.time() - t0

    out = ["# Evaluation on IR-Plag", "",
           f"Pairs compared: {len(scores['Structural'])} (original vs every other file, per case). "
           f"Time: {elapsed:.1f}s.", "",
           "Cells = % of pairs flagged. L1-L6 should be high (plagiarized); NON should be low (independent work).", ""]

    def table(name, thrs):
        rows = scores[name]
        if not rows:
            return
        out.append(f"## {name}")
        out.append("")
        out.append("| Threshold | " + " | ".join(LEVELS) + " |")
        out.append("|---|" + "---|" * len(LEVELS))
        for t in thrs:
            cells = []
            for lv in LEVELS:
                v = [s for l, s in rows if l == lv]
                cells.append(f"{100 * sum(s >= t for s in v) / len(v):.0f}%" if v else "-")
            out.append(f"| {t:.2f} | " + " | ".join(cells) + " |")
        neg = [s for l, s in rows if l == 'NON']
        out.append("")
        out.append("AUC per level (1.0 = perfect separation from independent work, 0.5 = coin flip): " +
                   ", ".join(f"{lv} {auc([s for l, s in rows if l == lv], neg):.2f}" for lv in LEVELS[:-1]))
        out.append("")

    table('Structural', STRUCT_THRS)
    table('Exact', STRUCT_THRS)
    table('Semantic', SEM_THRS)

    os.makedirs('results', exist_ok=True)
    with open('results/evaluation.md', 'w') as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    print("Saved to results/evaluation.md")


if __name__ == "__main__":
    main()
