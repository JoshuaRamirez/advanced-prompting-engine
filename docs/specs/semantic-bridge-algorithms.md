# Semantic Bridge Enhancement Algorithms

Reference specification for build-time-only algorithms that produce the GeometricBridge's pre-computed artifacts. All runtime costs are zero — artifacts are loaded as numpy arrays at runtime.

## Vector Source (ADR-013)

`BAAI/bge-large-en-v1.5` via `sentence-transformers`, at native **1024 dimensions**, no reduction. GloVe and Model2Vec paths are retired. Frequency ordering comes from `wordfreq`.

## Build Pipeline Order

```
load_bge()
    → build_target_vocab()                # wordfreq top-K ∪ pole/question/phrase words
        → encode(vocab)                    # BGE → (N, 1024) unit-normalized
            → build_face_centroids()        # authored-layer weighted means
            → build_axis_directions()       # high_pole − low_pole, calibration
                → compute_face_sim()         # cos(word, centroid) − mean
                → compute_axis_proj()        # calibrated to [0,1]
                → compute_idf()              # from wordfreq Zipf
                    → compute_disambiguation_table()   # BGE-encoded senses
                    → compute_phrase_embeddings()      # BGE-encoded phrases
                        → build_phase_centroids()
                        → compute_word_phase_sim()
                        → compute_question_position_maps()  # BGE-encoded 1728 questions
                            → extend & save artifacts
```

Counter-fitting / retrofitting is **disabled** in the current build to isolate the BGE variable; may be revisited once benchmark evidence is in.

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
