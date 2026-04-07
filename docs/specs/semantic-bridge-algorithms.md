# Semantic Bridge Enhancement Algorithms

Reference specification for three build-time-only algorithms that improve the GeometricBridge's face discrimination quality. All runtime costs are zero — these modify pre-computed artifacts only.

## Build Pipeline Order

```
load_all_glove()
    → [Alg 1] retrofit_vectors()          # modifies GloVe vectors in-place
        → build_face_centroids()           # uses retrofitted vectors
        → build_axis_directions()          # uses retrofitted vectors
            → select_runtime_vocab()
                → compute_face_sim()
                → compute_axis_proj()
                → compute_idf()
                    → [Alg 2] compute_disambiguation_table()
                    → [Alg 3] compute_ngram_embeddings()
                        → extend & save artifacts
```

## Algorithm 1: Retrofitting + Counter-fitting

### Papers
- Faruqui et al. 2015 "Retrofitting Word Vectors to Semantic Lexicons"
- Mrksic et al. 2016 "Counter-fitting Word Vectors to Linguistic Constraints"

### Constraint Sets
- S (synonyms): words in the same POLE_SYNONYMS entry. ATTRACT.
- F (face cohort): words in the same face but different poles. WEAK ATTRACT.
- A (antonyms): words in opposing poles of the same axis. REPEL.

### Update Rule (per iteration, per constrained word i)

```
v_i = (α·q_i + β_s·Σ_S v_j + β_f·Σ_F v_j + γ·Σ_A push(v_i, v_j))
      / (α + β_s·|S_i| + β_f·|F_i|)
```

Where push(v_i, v_j) = (v_i - v_j) / ||v_i - v_j|| if ||v_i - v_j|| < δ, else 0.

### Parameters
- α = 1.0 (regularization toward original)
- β_s = 1.0 (synonym attraction)
- β_f = 0.2 (face cohort attraction, weaker)
- γ = 0.3 (antonym repulsion)
- δ = 1.0 (antonym margin, Euclidean)
- T = 10 iterations
- Re-normalize to unit length after each iteration

### Scope
Only ~368 constrained words are updated. All others retain original GloVe vectors.

## Algorithm 2: Contextual Disambiguation Table

### Structure
trigger_word → list of {context_words, target_face, override_vectors, threshold}

### Lookup
For each token, check if trigger. Count matching context words from the full token set. If ≥ threshold (2), select that sense. Replace face_sim and axis_proj rows with override values.

### Override Computation
Average GloVe vectors of sense-specific seed words, then compute face_sim and axis_proj through the standard pipeline (cosine to centroids, dot to directions, calibrate).

### Known Entries
state, compelled, right, deep, forces, heaven, tragedy, action — each with 2-3 senses defined by context indicator words.

## Algorithm 3: N-gram/Phrase Embeddings

### Sources
~98 curated phrases: domain replacement bigrams, pole pair bigrams, philosophical key phrases, compositional phrases.

### Embedding
Arithmetic mean of component word vectors (post-retrofit). Processed through identical face_sim/axis_proj pipeline as individual words.

### Runtime Detection
Greedy longest-match forward scan in tokenizer. Trigrams checked before bigrams. Matched phrases consume their component words (no double-counting).

### Artifact Extension
Phrase rows appended to face_sim, axis_proj, idf arrays. Phrase keys added to vocab JSON.
