# Code Plagiarism Detector

**The plagiarism tool that also rewards originality.**

Most plagiarism tools answer one question: *"who copied?"* This project answers two:

1. **Who copied?** It flags copied code even when variables are renamed, comments are added or functions are reordered.
2. **Who used unique logic?** It groups students by the *approach* they took and surfaces the ones whose logic nobody else shares.

Both questions are answered at two levels: **whole file** and **block by block** (every function/method compared separately). It works on Python, Java, C, C++ and JavaScript, and it has been tested on a labelled dataset and on batches of 65+ files.

---

## Highlights

| Feature | Why it matters |
|---|---|
| **Two modes: "Who copied" and "Who used unique logic"** | Turns the tool from pure policing into discovery. A professor can reward a student who found a different solution, not only catch the ones who copied. |
| **Whole-file + block-by-block comparison** | A whole-file score gets diluted when only one function is copied into a large file. Block-level comparison catches it and shows *exactly which* function was copied (see the demo below). |
| **The professor decides what counts as copying** | A toggle switches between *rename-proof* matching (renamed variables still count as copying) and *exact* matching (only literal copy-paste counts). |
| **Two independent signals** | Structural fingerprinting decides **COPIED**; a semantic AI model only marks **REVIEW (possible rewrite)** for a human to check. The AI never makes the accusation on its own. |
| **Multi-language** | Pygments lexers (500+ languages) for comparison; tree-sitter parsers for Java/C/C++/JS block extraction; Python's `ast` for Python. |
| **Measured, not assumed** | Evaluated on the IR-Plag dataset. The results, including where the method fails, are reported below. |
| **Built for real class sizes** | Tested on a 70-file assignment and on 467 files at once without errors. Accepts a ZIP of a whole assignment folder (e.g. a Google Classroom folder downloaded from Drive). |

### What block-level comparison catches

`demo/partial_copy/student_big.py` is a 73-line file that contains one prime-checking function copied from `student1.py` (renamed from `is_prime` to `check`, with every variable renamed), mixed with unrelated code.

```
Whole-file structural similarity   0.16   → missed
Block is_prime vs block check      1.00   → caught, and the exact function is shown side by side
```

---

## How it works

```
                        uploaded files / ZIP
                                 |
             +-------------------+-------------------+
             |                                       |
     WHOLE FILE                               BLOCKS (functions/methods)
             |                          Python: ast | Java/C/C++/JS: tree-sitter
             +-------------------+-------------------+
                                 |
        +------------------------+------------------------+
        |                                                 |
  STRUCTURAL SIGNAL                                SEMANTIC SIGNAL
  (what was typed)                                 (what the code does)
  Pygments tokens -> names become ID,              code embedding model
  literals become LIT, comments dropped            (st-codesearch-distilroberta-base)
  -> 5-token k-grams -> winnowing                  long code split into chunks,
  -> Jaccard of fingerprints                       chunk vectors averaged -> cosine
        |                                                 |
        +------------------------+------------------------+
                                 |
          Mode 1 "Who copied":   structural >= threshold          -> COPIED
                                 else semantic >= threshold       -> REVIEW (optional)
          Mode 2 "Unique logic": files with semantic >= threshold are linked into
                                 approach groups; a group of size 1 -> UNIQUE approach
```

**Structural signal (winnowing).** This is the algorithm behind Stanford's MOSS (Schleimer, Wilkerson, Aiken, 2003).
1. **Tokenize** with Pygments. Every user-chosen name becomes `ID` and every number or string becomes `LIT`; comments and whitespace are removed. Renaming variables therefore changes nothing.
   ```
   Java:   if(n%i==0) return false;   ->  if ( ID % ID == LIT ) return false ;
   Java:   if(x%d==0) return false;   ->  if ( ID % ID == LIT ) return false ;
   ```
2. **k-grams:** slide a 5-token window along the token list and hash each window (CRC32, so results are identical on every run and machine).
3. **Winnowing:** out of every 4 consecutive hashes, keep the smallest. The kept hashes are the file's fingerprints. Any copied stretch of 8+ tokens is guaranteed to share a fingerprint.
4. **Jaccard:** shared fingerprints divided by all fingerprints (0 = nothing shared, 1 = identical). Fingerprints form a set, so reordering functions does not hide copying.

In **exact** mode, step 1 keeps the real names, so only literal copy-paste matches.

**Semantic signal.** A sentence-transformer trained on code search turns each file or block into a vector; cosine similarity measures whether two pieces of code *do the same thing*. The model reads about 512 tokens at most, so longer code is split into chunks and the chunk vectors are averaged.

**Why the AI model does not decide "COPIED".** In a class assignment every correct submission does the same thing, so a semantic model finds honest students similar too. Copying shows up in shared *structure*, which is what the structural signal measures. The semantic model is used where it is actually strong: spotting rewrites that change the typing but keep the logic, and grouping approaches in Mode 2.

**Tiny blocks are ignored at block level** (fewer than 25 tokens). A three-line wrapper such as "call a function, loop, print" looks identical under every method, so it is not evidence of anything.

---

## Dataset

**IR-Plag** (Karnalim et al., 2019): https://github.com/oscarkarnalim/sourcecodeplagiarismdataset
Paper: *Informatics in Education*, 18(2), https://doi.org/10.15388/infedu.2019.15

467 Java files across 7 introductory programming tasks. Each task (case) contains:
- 1 original solution,
- 15 solutions written independently (non-plagiarized),
- about 50 plagiarized copies of the original at six disguise levels (Faidhi & Robinson, 1987):

| Level | Disguise applied |
|---|---|
| L1 | Comments and whitespace changed |
| L2 | Identifiers renamed |
| L3 | Declarations moved |
| L4 | Methods/modules restructured |
| L5 | Statements reordered |
| L6 | Control logic changed |

**Why this dataset:** it has ground-truth labels, each case is one assignment of 56 to 70 files (a realistic class size), the disguise levels let us measure *which kinds* of plagiarism are caught, and it includes independent solutions to the same task, which is exactly what produces false positives in real classrooms.

The `demo/` folder contains small hand-made test sets: a prime-number assignment (copies, a renamed copy, and three genuinely different algorithms), class-based Python files, Java files, and the partial-copy example.

---

## Results

Reproduce with `python evaluate.py path/to/IR-Plag-Dataset`. Each cell is the % of pairs (original vs. submission) that were flagged. L1 to L6 should be high; NON (independent work) should be low.

**Structural (rename-proof), 460 pairs:**

| Threshold | L1 | L2 | L3 | L4 | L5 | L6 | NON (false alarms) |
|---|---|---|---|---|---|---|---|
| 0.50 | 100% | 96% | 98% | 48% | 12% | 3% | 44% |
| 0.60 | 100% | 95% | 79% | 13% | 2% | 2% | 31% |
| **0.70 (default)** | **100%** | **95%** | **44%** | **8%** | **0%** | **0%** | **16%** |
| 0.80 | 82% | 71% | 26% | 2% | 0% | 0% | 7% |

**Exact mode, same pairs:**

| Threshold | L1 | L2 | L3 | L4 | L5 | L6 | NON |
|---|---|---|---|---|---|---|---|
| 0.70 | 83% | 9% | 14% | 0% | 0% | 0% | 1% |

**Semantic (REVIEW tier):**

Semantic results are generated by `evaluate.py` and saved, together with the tables above, in [`results/evaluation.md`](results/evaluation.md).

**What the numbers show:**
- The structural signal reliably catches copying disguised by comments, whitespace and renaming (L1, L2: 95 to 100% at the default threshold).
- **Exact mode does what it promises:** renamed copies (L2) drop from 95% to 9%, so the rename toggle gives the professor a real choice.
- Heavier disguises (L4 to L6: restructuring, reordering, changed logic) defeat token matching. This is expected and is the reason the semantic REVIEW tier exists.
- **Independent solutions to tiny tasks look alike.** These tasks are 10 to 30 lines long, and 16% of honest solutions still score at or above 0.7 (one independent solution scores 1.0). This is why the default threshold is 0.7 rather than 0.5, and why every flag comes with a side-by-side view for a human to confirm.

**Scale test:** a 70-file case (118 blocks, 2,415 file pairs, 3,637 block pairs) and the full 467-file dataset (769 blocks, 108,811 file pairs, 241,602 block pairs) both ran through the app with no errors. The structural analysis of all 467 files took about 5 seconds; embedding time depends on your CPU/GPU.

---

## Setup and run

**Requirements:** Python 3.10 or newer. The first run downloads the embedding model (a few hundred MB) from Hugging Face.

```bash
git clone https://github.com/YOUR-USERNAME/code-plagiarism-detector.git
cd code-plagiarism-detector
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

**Web app:**
```bash
streamlit run app.py
```
1. Upload code files, or a ZIP of an assignment folder.
2. Click **Analyse**.
3. Choose a mode in the sidebar and adjust the thresholds. Results update instantly; no re-analysis is needed.

**Command line:**
```bash
python detect.py demo/prime_assignment
```

**Evaluation on IR-Plag:**
```bash
# download IR-Plag-Dataset.zip from the dataset link above and unzip it
python evaluate.py IR-Plag-Dataset            # structural + semantic
python evaluate.py IR-Plag-Dataset --no-model # structural only, runs in seconds
```

**Try it on a real 65+ file assignment:** zip a single case folder (e.g. `IR-Plag-Dataset/case-02`) and upload the ZIP. Use one case at a time for "Who used unique logic", because *unique* only means something among solutions to the same problem.

**Google Classroom:** Classroom stores each assignment's submissions in a folder in the teacher's Google Drive. Download that folder from Drive as a ZIP and upload it. Files with the same name (everyone's `main.py`) are kept apart using their folder path.

---

## Screenshots

| | |
|---|---|
| Who copied: whole-file and block tables | ![Copy mode](screenshots/copy_mode.png) |
| Rename toggle off (exact matching only) | ![Exact mode](screenshots/exact_mode.png) |
| Block-level side-by-side (partial copy demo) | ![Block level](screenshots/block_level.png) |
| Who used unique logic: approach groups | ![Unique mode](screenshots/unique_mode.png) |
| 70-file heatmap (copy ring visible as a red block) | ![Heatmap](screenshots/heatmap_70.png) |


---

## How the approach evolved

This section records every major decision, the problem that caused it, and the reasoning.

**Phase 1: Embeddings only.** The first version compared functions with a code-embedding model and cosine similarity.
*Problem:* embeddings measure "does this code do the same thing?", and in an assignment every correct submission does the same thing, so honest students also score high.

**Phase 2: AST normalization + embeddings.** Variables and functions were renamed to `VAR0`, `FUNC0` before embedding, and the original and normalized scores were combined.
*Problem:* on the demo set, 6 of the 12 flagged pairs were false positives (e.g. a Fibonacci printer scored 0.98 against a prime printer). After normalization, short functions became byte-identical, so the normalized heatmap was almost entirely red. The model understands code largely through identifier names; `VAR0/FUNC0` code is unlike anything it was trained on, so it could no longer tell functions apart.
*Other bugs found:* function calls were renamed as variables; builtins like `input`, `sum`, `max` were renamed; `ast.walk` extracted nested functions twice; class methods with the same name (two `__init__`s) overwrote each other in the comparison view; code outside functions was never checked.

**Phase 3: Two signals with separate jobs.** Replaced normalization + embeddings with token fingerprinting (winnowing) as the structural signal, and kept the embedding model on the original code only, as a secondary REVIEW signal.
*Reasoning:* copying shows up as shared structure; that is what MOSS and JPlag measure. Using Pygments instead of `ast` for this step made it language-independent. Added a whole-file comparison so code outside functions and non-Python files are covered, and skipped blocks under 25 tokens because tiny wrappers match under every method.

**Phase 4: Fixing the Streamlit interface logic.** Moving a slider after detection did nothing, because thresholds were applied once at click time and the results were frozen.
*Fix:* split the work into `analyse()` (heavy: embeddings and raw scores for every pair, run once) and `classify()` (cheap: applies the current slider values on every rerun). Also cleared stale results when the uploaded files change.

**Phase 5: Two modes and the rename toggle.** Added "Who used unique logic" (approach groups via union-find over semantic similarity) and the rename-proof/exact toggle. Table columns now change with the mode and settings. Added ZIP upload as the bridge to Google Classroom.

**Phase 6: Scaling to real class sizes.** A 174-file dataset made the original heatmap unreadable.
*Fixes:* the heatmap reorders files so groups sit together (a copy ring appears as one red block), switches to numbered axes with a lookup table above 30 files, and closes each figure so memory does not grow on every slider move. Long files were silently cut off at the model's ~512-token limit, so embeddings are now computed per chunk and averaged. Python's `hash()` changes between runs, so it was replaced with CRC32 to make scores reproducible. ZIPs from macOS contain `__MACOSX/._file.py` metadata files that look like code; these are skipped. Overloaded Java methods now get unique labels (`dep`, `dep#2`).

**Phase 7: Block-by-block for every language.** Block extraction was Python-only (via `ast`). Added tree-sitter parsers so Java, C, C++ and JavaScript files are also split into methods and functions.

**Phase 8: Evaluation on a labelled dataset.** Switched to IR-Plag because it provides ground truth, realistic assignment sizes and graded disguise levels. The evaluation showed that independent solutions to tiny tasks often look alike, so the default copy threshold was raised from 0.5 to 0.7 (false alarms on independent work dropped from 44% to 16% while L1/L2 detection stayed at 95 to 100%).

---

## Limitations

- **Canonical solutions.** On very small tasks, honest students often write identical code. No method can separate those cases automatically; the tool flags them but only a human can decide.
- **Heavy rewrites (L4 to L6)** defeat structural matching. Only the semantic REVIEW tier can catch them, and it needs human confirmation.
- **The semantic model** was trained on code search data (as far as I know, Go, Java, JavaScript, PHP, Python and Ruby, with no C/C++), so semantic scores for C/C++ are less reliable.
- **"Unique" does not mean "good".** A buggy or incomplete submission is also unique. Mode 2 marks files worth a look, not the best solutions. Groups are formed by chaining (A~B and B~C put A and C together), which can merge different approaches in large batches; the threshold slider controls this.
- **Cross-language comparison** is not meaningful structurally (Python and Java produce different tokens).
- **Not extracted as blocks:** JavaScript arrow functions, and Python functions defined inside loops or `try` blocks. The whole-file comparison still covers them.
- **Starter/template code** provided by the teacher is not yet excluded, so it raises everyone's similarity.

## Future scope

- Direct Google Classroom API integration (teacher OAuth login, fetch submissions automatically).
- Exclude teacher-provided starter code before comparison.
- Highlight the exact matching lines inside the side-by-side view.
- Detect AI-generated submissions.

---

## Project structure

```
app.py            Streamlit web app (modes, tables, side-by-side view, heatmap)
detect.py         Loading, analysis pipeline, chunked embeddings, approach groups, CLI
fingerprint.py    Tokenization, winnowing, pair scoring, classification
extractors.py     Block extraction: ast (Python), tree-sitter (Java, C, C++, JS)
evaluate.py       Evaluation on IR-Plag, writes results/evaluation.md
demo/             Small hand-made test sets
results/          Evaluation output
screenshots/      Screenshots for this README
```

## References

- S. Schleimer, D. S. Wilkerson, A. Aiken. *Winnowing: Local Algorithms for Document Fingerprinting.* SIGMOD 2003.
- O. Karnalim, S. Budi, H. Toba, M. Joy. *Source Code Plagiarism Detection in Academia with Information Retrieval: Dataset and the Observation.* Informatics in Education, 18(2), 2019.
- A. Faidhi, S. Robinson. *An empirical approach for detecting program similarity and plagiarism within a university programming environment.* Computers & Education, 1987.
- Embedding model: https://huggingface.co/flax-sentence-embeddings/st-codesearch-distilroberta-base
