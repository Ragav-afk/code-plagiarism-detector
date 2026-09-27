"""
Structural similarity: language-agnostic token fingerprinting (winnowing, as in Stanford's MOSS).
"""
import zlib
from pygments.lexers import guess_lexer_for_filename, TextLexer
from pygments.token import Name, Literal, Comment, Text
from pygments.util import ClassNotFound

K = 5  # tokens per k-gram
W = 4  # winnowing window


def tokenize(code, filename, ignore_names=True):
    """
    Lex the code with Pygments (500+ languages).
    ignore_names=True : every user-chosen name -> ID (renamed copies still match)
    ignore_names=False: real names kept (only exact copies match)
    Literals -> LIT. Comments and whitespace dropped. Keywords, operators, builtins kept.
    """
    try:
        lexer = guess_lexer_for_filename(filename, code)
    except ClassNotFound:
        lexer = TextLexer()
    out = []
    for ttype, value in lexer.get_tokens(code):
        if ttype in Comment or ttype in Text or not value.strip():
            continue
        if ttype in Name.Builtin:
            out.append(value)
        elif ttype in Name:
            out.append("ID" if ignore_names else value)
        elif ttype in Literal:
            out.append("LIT")
        else:
            out.append(value)
    return out


def _stable_hash(text):
    # zlib.crc32 gives the same number in every run (Python's hash() does not),
    # so scores are reproducible across runs and machines.
    return zlib.crc32(text.encode("utf-8"))


def fingerprints(tokens, k=K, w=W):
    """Hash every k-token window; keep the smallest hash in each run of w hashes."""
    grams = [_stable_hash(" ".join(tokens[i:i + k])) for i in range(len(tokens) - k + 1)]
    if len(grams) < w:
        return set(grams)
    return {min(grams[i:i + w]) for i in range(len(grams) - w + 1)}


def jaccard(fa, fb):
    if not fa or not fb:
        return 0.0
    return len(fa & fb) / len(fa | fb)


def structural_sim(code_a, file_a, code_b, file_b, ignore_names=True):
    return jaccard(fingerprints(tokenize(code_a, file_a, ignore_names)),
                   fingerprints(tokenize(code_b, file_b, ignore_names)))


def compute_pairs(items, sem_matrix, min_tokens=25):
    """
    Score EVERY cross-file pair once (no thresholds here).
    items: list of (filename, label, source). Returns list of dicts with raw scores.
    """
    tokens = [tokenize(src, fname) for fname, _, src in items]
    fps = [fingerprints(t) for t in tokens]
    fps_exact = [fingerprints(tokenize(src, fname, ignore_names=False)) for fname, _, src in items]
    pairs = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i][0] == items[j][0]:
                continue
            if len(tokens[i]) < min_tokens or len(tokens[j]) < min_tokens:
                continue  # tiny wrappers look identical under every method; not evidence
            pairs.append({
                'i': i, 'j': j,
                'File 1': items[i][0], 'Part 1': items[i][1],
                'File 2': items[j][0], 'Part 2': items[j][1],
                'Structural': round(jaccard(fps[i], fps[j]), 4),
                'Exact': round(jaccard(fps_exact[i], fps_exact[j]), 4),
                'Semantic': round(float(sem_matrix[i][j]), 4),
            })
    return pairs


def classify(pairs, struct_key='Structural', struct_thr=0.7, sem_thr=0.90, show_review=True):
    """
    Apply the CURRENT settings to precomputed scores.
    struct_key: 'Structural' (renamed copies count) or 'Exact' (only exact copies count).
    Columns follow the settings: no Semantic/Verdict columns when REVIEW is off.
    """
    label = "Structural (rename-proof)" if struct_key == 'Structural' else "Exact match"
    out = []
    for p in pairs:
        if p[struct_key] >= struct_thr:
            verdict = "COPIED"
        elif show_review and p['Semantic'] >= sem_thr:
            verdict = "REVIEW (possible rewrite)"
        else:
            continue
        row = {'File 1': p['File 1'], 'Part 1': p['Part 1'],
               'File 2': p['File 2'], 'Part 2': p['Part 2'],
               label: p[struct_key]}
        if show_review:
            row['Semantic'] = p['Semantic']
            row['Verdict'] = verdict
        out.append(row)
    out.sort(key=lambda r: (r.get('Verdict', 'COPIED') != "COPIED", -r[label], -r.get('Semantic', 0)))
    return out
