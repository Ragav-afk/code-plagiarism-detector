import os
import zipfile
import tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st
from sentence_transformers import SentenceTransformer
from detect import (load_code_files, analyse, pairs_to_matrix, approach_groups, link_groups,
                    MODEL_NAME, CODE_EXTENSIONS)
from fingerprint import classify

MAX_PICK = 300          # side-by-side dropdown size cap
LABEL_LIMIT = 30        # above this many files, heatmap axes show numbers + a lookup table


@st.cache_resource
def load_model():
    return SentenceTransformer(MODEL_NAME)


def save_uploads(uploaded_files, tmp_dir):
    """Write uploads into tmp_dir. ZIPs (e.g. a Classroom assignment folder downloaded from Drive) are unpacked."""
    skipped = []
    for f in uploaded_files:
        if f.name.lower().endswith('.zip'):
            try:
                z = zipfile.ZipFile(f)
            except zipfile.BadZipFile:
                skipped.append(f"{f.name} (not a valid ZIP)")
                continue
            with z:
                for member in z.namelist():
                    base = member.rsplit('/', 1)[-1]
                    if (member.endswith('/') or member.startswith('__MACOSX')
                            or base.startswith('._') or not base.lower().endswith(CODE_EXTENSIONS)):
                        continue  # folders, macOS metadata files, non-code files
                    # 'Ravi/main.py' -> 'Ravi__main.py': keeps students apart when everyone names it main.py,
                    # and never writes outside tmp_dir (no path traversal via '../')
                    safe = member.replace('\\', '/').strip('/').replace('/', '__').replace('..', '_')
                    with open(os.path.join(tmp_dir, safe), 'wb') as out:
                        out.write(z.read(member))
        else:
            with open(os.path.join(tmp_dir, f.name), 'wb') as out:
                out.write(f.getvalue())
    return skipped


def draw_heatmap(names, matrix, title, order_thr):
    """Rows/columns are reordered so files in the same group sit together: copy rings show as red blocks."""
    st.subheader(title)
    order = [i for group in link_groups(matrix, order_thr) for i in group]
    m = matrix[order][:, order]
    n = len(order)
    use_numbers = n > LABEL_LIMIT
    labels = [str(k + 1) for k in range(n)] if use_numbers else [names[i][-28:] for i in order]

    side = min(14, max(5, 0.32 * n))
    fig, ax = plt.subplots(figsize=(side + 1.5, side))
    im = ax.imshow(m, cmap='RdYlGn_r', vmin=0, vmax=1, interpolation='nearest')
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    font = 7 if n <= 30 else max(3, int(220 / n))
    ax.set_xticklabels(labels, rotation=90, fontsize=font)
    ax.set_yticklabels(labels, fontsize=font)
    if n <= 15:
        for a in range(n):
            for b in range(n):
                ax.text(b, a, f"{m[a][b]:.2f}", ha='center', va='center', fontsize=6)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)  # without this, figures pile up in memory on every slider move

    if use_numbers:
        with st.expander("Heatmap index → file"):
            st.dataframe([{'#': k + 1, 'File': names[i]} for k, i in enumerate(order)],
                         hide_index=True, width="stretch")


def side_by_side(label_a, code_a, label_b, code_b):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{label_a}**")
        st.code(code_a)
    with col2:
        st.markdown(f"**{label_b}**")
        st.code(code_b)


st.set_page_config(page_title="Code Plagiarism Detector", layout="wide")
st.title("Code Plagiarism Detector")
st.caption("Who copied, and who thought differently. File-level and block-level (function/method) comparison.")

for key in ['analysis', 'codes', 'uploaded_names']:
    if key not in st.session_state:
        st.session_state[key] = None

with st.sidebar:
    st.header("Mode")
    mode = st.radio("What do you want to find?", ["Who copied", "Who used unique logic"])
    st.divider()
    st.header("Settings")
    if mode == "Who copied":
        rename_counts = st.toggle("Renamed variables still count as copying", value=True)
        struct_thr = st.slider("Copy threshold", 0.2, 1.0, 0.7, 0.05)
        show_review = st.checkbox("Also show possible rewrites (semantic)", value=False)
        sem_thr = st.slider("Rewrite threshold (semantic)", 0.5, 1.0, 0.90, 0.01) if show_review else 1.0
    else:
        group_thr = st.slider("Same-approach threshold (semantic)", 0.5, 1.0, 0.85, 0.01)
        st.caption("Files at or above this similarity share an approach group. "
                   "Use one assignment per run: 'unique' only means something among solutions to the same problem.")

uploaded_files = st.file_uploader(
    "Upload code files, or a ZIP of an assignment folder",
    type=[e.lstrip('.') for e in CODE_EXTENSIONS] + ['zip'], accept_multiple_files=True
)

current_names = sorted(f.name for f in uploaded_files) if uploaded_files else []
if st.session_state.analysis is not None and current_names != st.session_state.uploaded_names:
    st.session_state.analysis = None   # uploads changed: old results no longer apply

if uploaded_files and st.button("Analyse", type="primary"):
    st.session_state.analysis = None
    with tempfile.TemporaryDirectory() as tmp_dir:
        skipped = save_uploads(uploaded_files, tmp_dir)
        codes = load_code_files(tmp_dir)
    for s in skipped:
        st.warning(f"Skipped {s}")
    if len(codes) < 2:
        st.warning("Need at least 2 code files (a ZIP counts as all the code files inside it).")
    else:
        with st.spinner("Loading model..."):
            model = load_model()
        with st.spinner(f"Analysing {len(codes)} files..."):
            st.session_state.analysis = analyse(codes, model)
        st.session_state.codes = codes
        st.session_state.uploaded_names = current_names

if st.session_state.analysis is not None:
    res = st.session_state.analysis
    codes = st.session_state.codes
    names = res['file_names']
    all_funcs = res['all_funcs']
    n_langs = len({os.path.splitext(n)[1] for n in names})
    st.info(f"Analysed {len(codes)} files ({n_langs} language(s)), {len(all_funcs)} functions/methods")

    if mode == "Who copied":
        key = 'Structural' if rename_counts else 'Exact'
        file_rows = classify(res['file_pairs'], key, struct_thr, sem_thr, show_review)
        func_rows = classify(res['func_pairs'], key, struct_thr, sem_thr, show_review)
        file_rows = [{k: v for k, v in r.items() if k not in ('Part 1', 'Part 2')} for r in file_rows]

        flagged = {r['File 1'] for r in file_rows} | {r['File 2'] for r in file_rows}
        st.subheader(f"Whole-file comparison: {len(file_rows)} pair(s), {len(flagged)} file(s) involved")
        if file_rows:
            st.dataframe(file_rows, width="stretch", hide_index=True)
        else:
            st.success("No file pairs flagged.")

        st.subheader(f"Block-by-block comparison: {len(func_rows)} function/method pair(s)")
        st.caption("Shows WHICH part was copied, and catches partial copying that a whole-file score dilutes.")
        if func_rows:
            st.dataframe(func_rows, width="stretch", hide_index=True)
        else:
            st.write("No function/method pairs flagged.")

        pool = [dict(r, **{'Part 1': '<whole file>', 'Part 2': '<whole file>'}) for r in file_rows] + func_rows
        if pool:
            st.subheader("Side-by-side")
            if len(pool) > MAX_PICK:
                st.caption(f"Showing the top {MAX_PICK} of {len(pool)} pairs; raise the threshold to narrow down.")
            pool = pool[:MAX_PICK]
            block_src = {(f, name): src for f, name, src in all_funcs}

            def find_source(fname, part):
                return codes.get(fname, "Not found") if part == "<whole file>" else block_src.get((fname, part), "Not found")

            idx = st.selectbox("Select a pair", range(len(pool)), key='copy_pick',
                               format_func=lambda i: f"{pool[i]['File 1']}::{pool[i]['Part 1']} vs "
                                                     f"{pool[i]['File 2']}::{pool[i]['Part 2']}")
            p = pool[idx]
            side_by_side(f"{p['File 1']} :: {p['Part 1']}", find_source(p['File 1'], p['Part 1']),
                         f"{p['File 2']} :: {p['Part 2']}", find_source(p['File 2'], p['Part 2']))

        title = "Heatmap: rename-proof structural" if rename_counts else "Heatmap: exact-match structural"
        draw_heatmap(names, pairs_to_matrix(res['file_pairs'], len(names), key), title, struct_thr)

    else:
        sem = pairs_to_matrix(res['file_pairs'], len(names), 'Semantic')
        rows = approach_groups(names, sem, group_thr)
        unique = [r for r in rows if r['Group size'] == 1]
        n_groups = len({r['Approach group'] for r in rows})

        st.subheader(f"{n_groups} approach group(s), {len(unique)} unique file(s)")
        st.dataframe(rows, width="stretch", hide_index=True)

        st.subheader("Compare a file with its closest match")
        pick = st.selectbox("File", range(len(rows)), key='unique_pick',
                            format_func=lambda i: f"{rows[i]['Student file']} ({rows[i]['Label']})")
        r = rows[pick]
        side_by_side(r['Student file'], codes[r['Student file']],
                     f"Closest: {r['Closest file']} ({r['Closest similarity']})", codes[r['Closest file']])

        draw_heatmap(names, sem, "Heatmap: semantic (approach) similarity", group_thr)
else:
    st.info("Upload files (or a ZIP) and click Analyse.")
