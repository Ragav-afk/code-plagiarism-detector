import os
import sys
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def load_code_files(folder):
    codes = {}
    for filename in os.listdir(folder):
        if filename.endswith(('.py', '.c', '.cpp', '.java')):
            with open(os.path.join(folder, filename), 'r') as f:
                codes[filename] = f.read()
    return codes

def find_suspicious_pairs(folder, threshold=0.75):
    model = SentenceTransformer("flax-sentence-embeddings/st-codesearch-distilroberta-base")
    
    codes = load_code_files(folder)
    if len(codes) < 2:
        print(f"Need at least 2 files in {folder}, found {len(codes)}")
        return []
    
    filenames = list(codes.keys())
    code_list = list(codes.values())
    
    print(f"Loaded {len(filenames)} files. Computing embeddings...")
    embeddings = model.encode(code_list)
    
    sim_matrix = cosine_similarity(embeddings)
    
    suspicious = []
    for i in range(len(filenames)):
        for j in range(i + 1, len(filenames)):
            score = sim_matrix[i][j]
            if score >= threshold:
                suspicious.append((filenames[i], filenames[j], score))
    
    suspicious.sort(key=lambda x: -x[2])
    return suspicious

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "submissions/"
    
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a directory")
        sys.exit(1)
    
    results = find_suspicious_pairs(folder)
    
    print(f"\n{'='*60}")
    print(f"CODE PLAGIARISM DETECTION REPORT")
    print(f"{'='*60}")
    print(f"Folder: {folder}")
    print(f"Threshold: 0.75\n")
    
    if not results:
        print("No suspicious pairs found.")
    else:
        print(f"Found {len(results)} suspicious pair(s):\n")
        for f1, f2, score in results:
            verdict = "HIGH RISK" if score >= 0.85 else "SUSPICIOUS"
            print(f"  [{verdict}] {f1} <-> {f2}: {score:.4f}")