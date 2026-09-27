import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from extractors import extract_functions
from fingerprint import compute_pairs, classify

MODEL_NAME = "flax-sentence-embeddings/st-codesearch-distilroberta-base"
CODE_EXTENSIONS = ('.py', '.java', '.c', '.h', '.cpp', '.cc', '.hpp', '.js')


def load_code_files(folder):
    """Read every code file directly inside folder. Bad bytes are replaced, never crash."""
    codes = {}
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith(CODE_EXTENSIONS):
            with open(os.path.join(folder, filename), 'r', encoding='utf-8', errors='replace') as f:
                codes[filename] = f.read()
    return codes


def get_all_functions(codes):
    """Return list of (filename, block_name, source). Duplicate names in one file get #2, #3..."""
    all_funcs = []
    for filename, code in codes.items():
        seen = {}
        for name, source in extract_functions(code, filename):
            seen[name] = seen.get(name, 0) + 1
            label = name if seen[name] == 1 else f"{name}#{seen[name]}"   # e.g. overloaded Java methods
            all_funcs.append((filename, label, source))
    return all_funcs


def encode_long(model, texts, max_chars=1200):
    """
    The model reads at most ~512 tokens; anything longer is silently cut off.
    So split each text into ~1200-character chunks on line boundaries, embed every chunk,
    and average the chunk vectors per text.
    """
    chunks, owner = [], []
    for idx, text in enumerate(texts):
        cur = ""
        for line in (text.splitlines() or [""]):
            if cur and len(cur) + len(line) + 1 > max_chars:
                chunks.append(cur)
                owner.append(idx)
                cur = ""
            cur += line + "\n"
        chunks.append(cur)
        owner.append(idx)
    emb = np.asarray(model.encode(chunks, batch_size=32, show_progress_bar=False), dtype=float)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12
    out = np.zeros((len(texts), emb.shape[1]))
    for vec, idx in zip(emb, owner):
        out[idx] += vec
    return out


def pairs_to_matrix(pairs, n, key):
    """Turn a pair list into an n x n matrix for the heatmap (diagonal = 1)."""
    m = np.eye(n)
    for p in pairs:
        m[p['i']][p['j']] = m[p['j']][p['i']] = p[key]
    return m


def link_groups(matrix, thr):
    """Union-find: i and j share a group if matrix[i][j] >= thr (chained). Largest groups first."""
    n = len(matrix)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if matrix[i][j] >= thr:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


def approach_groups(names, sem, group_thr):
    """Unique-logic mode: a group of size 1 = a file whose approach nobody else shares."""
    n = len(names)
    rows = []
    for gid, members in enumerate(link_groups(sem, group_thr), 1):
        for i in members:
            j = max((k for k in range(n) if k != i), key=lambda k: sem[i][k])
            rows.append({
                'Student file': names[i],
                'Approach group': gid,
                'Group size': len(members),
                'Label': "UNIQUE approach" if len(members) == 1 else f"Shared approach ({len(members)} files)",
                'Closest file': names[j],
                'Closest similarity': round(float(sem[i][j]), 4),
            })
    rows.sort(key=lambda r: (r['Group size'], r['Closest similarity']))
    return rows


def analyse(codes, model):
    """Heavy work, done ONCE per upload: embeddings + raw scores for every pair. No thresholds."""
    result = {'file_names': list(codes), 'file_pairs': [], 'func_pairs': [], 'all_funcs': []}
    if len(codes) < 2:
        return result
    file_items = [(name, "<whole file>", src) for name, src in codes.items()]
    file_sem = cosine_similarity(encode_long(model, [i[2] for i in file_items]))
    result['file_pairs'] = compute_pairs(file_items, file_sem, min_tokens=0)

    all_funcs = get_all_functions(codes)
    result['all_funcs'] = all_funcs
    if len(all_funcs) >= 2:
        func_sem = cosine_similarity(encode_long(model, [f[2] for f in all_funcs]))
        result['func_pairs'] = compute_pairs(all_funcs, func_sem)
    return result


def print_report(title, rows):
    print("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)
    if not rows:
        print("Nothing flagged.")
        return
    for r in rows:
        score = r.get('Structural (rename-proof)', r.get('Exact match'))
        print(f"[{r.get('Verdict', 'COPIED')}] structural {score:.2f}  semantic {r.get('Semantic', 0):.2f}")
        print(f"    {r['File 1']} :: {r['Part 1']}\n    {r['File 2']} :: {r['Part 2']}\n")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "demo/prime_assignment/"
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a directory")
        sys.exit(1)
    codes = load_code_files(folder)
    print(f"Loaded {len(codes)} files")
    res = analyse(codes, SentenceTransformer(MODEL_NAME))
    print_report("FILE-LEVEL VERDICT", classify(res['file_pairs']))
    print_report("BLOCK-LEVEL EVIDENCE", classify(res['func_pairs']))
    names = res['file_names']
    sem = pairs_to_matrix(res['file_pairs'], len(names), 'Semantic')
    print("\n" + "=" * 70 + "\nAPPROACH GROUPS (semantic >= 0.85)\n" + "=" * 70)
    for r in approach_groups(names, sem, 0.85):
        print(f"  {r['Student file']:30} group {r['Approach group']:<3} {r['Label']:28} "
              f"closest: {r['Closest file']} ({r['Closest similarity']:.2f})")
