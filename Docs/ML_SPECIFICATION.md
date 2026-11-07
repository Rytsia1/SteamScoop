# SteamScoop --- ML Specification

**Document:** `ML_SPECIFICATION.md`\
**Version:** 1.0\
**Status:** Proposed baseline for MVP\
**Product:** SteamScoop --- *Understand Games Through Data.*

------------------------------------------------------------------------

## 1. Purpose

This document specifies the machine-learning and NLP design for
SteamScoop. It defines the analytical tasks, preprocessing pipeline,
model selection criteria, evaluation methodology, inference workflow,
output contracts, and model versioning strategy.

SteamScoop analyzes public Steam user reviews to help users understand
patterns in player feedback. Its outputs are analytical estimates, not
objective measures of game quality and not replacements for human
interpretation.

The ML system has three primary analytical capabilities:

1.  **Sentiment Analysis:** estimate the overall expressed sentiment of
    a review.
2.  **Aspect-Based Sentiment Analysis (ABSA):** identify which game
    aspects are discussed and the sentiment expressed toward each
    aspect.
3.  **Topic Modeling:** discover recurring themes in a collection of
    reviews.

Supporting capabilities include language identification, text
normalization, confidence handling, evaluation, drift monitoring, and
reproducibility.

### 1.1 Scope

In scope: - English-first NLP pipeline, with multilingual support
introduced only after language-specific evaluation. - Review-level
sentiment classification. - Aspect extraction/classification and
aspect-level polarity. - Unsupervised or weakly supervised topic
discovery. - Offline training/evaluation and controlled production
inference. - Versioned predictions and reproducible aggregate analytics.

Out of scope for the initial MVP: - Predicting commercial success,
sales, player retention, or review helpfulness. - Generating synthetic
reviews or using generated text as ground truth. - Treating Steam's
positive/negative recommendation as the model's sentiment label. -
Claiming causal relationships between updates and sentiment changes. -
Automatically generating game ratings or a single definitive
game-quality score. - LLM-based inference as a required dependency.

------------------------------------------------------------------------

## 2. ML principles and analytical definitions

### 2.1 Separate source signals from model interpretations

Steam provides a recommendation field (`voted_up`). SteamScoop's model
independently predicts sentiment from the review text.

These signals are related but not interchangeable:

-   `voted_up = true` means the reviewer recommended the game on Steam.
-   `sentiment = positive` means the model estimates that the review
    text expresses positive sentiment.
-   A positive review can contain criticism, sarcasm, or mixed opinions.
-   A negative recommendation can contain praise for selected aspects.
-   A short review may not contain enough information for a reliable
    prediction.

The UI and data exports must label these signals separately.

### 2.2 Unit of analysis

  -----------------------------------------------------------------------
  Task                    Primary unit            Output
  ----------------------- ----------------------- -----------------------
  Language identification Review                  Language code and
                                                  confidence

  Overall sentiment       Review                  Label and class
                                                  probabilities

  Aspect detection        Review/aspect mention   Aspect label, evidence
                                                  span, confidence

  Aspect sentiment        Aspect mention          Polarity and confidence

  Topic modeling          Corpus/document         Topic assignment or
                                                  distribution

  Trend analytics         Game/time bucket        Aggregated counts and
                                                  proportions
  -----------------------------------------------------------------------

### 2.3 Sentiment label policy

The target label space is:

-   `positive`
-   `negative`
-   `neutral`

Use `neutral` only when the text is genuinely neutral or has no clear
polarity. Do not automatically classify every short, ambiguous, mixed,
or low-confidence review as neutral. Such cases may instead receive an
`insufficient_evidence` or `unclassified` processing state outside the
three-class sentiment label set.

A practical MVP may begin with binary positive/negative classification
if the training dataset does not support a defensible neutral class. The
deployed schema should still allow the three-class contract.

### 2.4 Confidence is not correctness

A model confidence score is a model-derived estimate, not a calibrated
probability unless calibration has been tested. The UI should avoid
language such as "100% certain." Confidence thresholds must be selected
on validation data and documented per model version.

------------------------------------------------------------------------

## 3. End-to-end ML architecture

``` mermaid
flowchart TD
    A[Collected Steam Reviews] --> B[Text Validation]
    B --> C[Language Identification]
    C --> D{Supported Language?}
    D -->|Yes| E[Normalization and Preprocessing]
    D -->|No| X[Unsupported / Deferred]
    E --> F[Inference Queue]
    F --> G[Overall Sentiment]
    F --> H[Aspect Detection and Polarity]
    F --> I[Topic Assignment]
    G --> J[Output Validation]
    H --> J
    I --> J
    J --> K[Versioned Prediction Storage]
    K --> L[Analytics Aggregation]
    L --> M[Public Intelligence Views]
```

The diagram represents logical flow, not a requirement that all tasks
run in one process. Each pipeline stage may be a separate Celery task,
but the MVP should avoid unnecessary service decomposition.

### 3.1 Processing stages

1.  Select reviews that have not been processed by the requested model
    version.
2.  Validate text and required source fields.
3.  Detect language.
4.  Route to a supported language-specific model pipeline.
5.  Normalize text using the preprocessing policy associated with that
    model.
6.  Run sentiment, ABSA, and topic inference as applicable.
7.  Validate output labels, scores, spans, and schema.
8.  Persist results with model and pipeline provenance.
9.  Recompute affected aggregates.
10. Record processing counts, failures, latency, and model version.

### 3.2 Processing idempotency

A review must not receive duplicate output for the same model version
and pipeline run. Use deterministic selection and unique database
constraints.

A new model version creates new prediction rows. It must not overwrite
historical results from a previous version.

------------------------------------------------------------------------

## 4. Data preparation and preprocessing

Preprocessing is part of the model contract. Training and inference must
use compatible preprocessing implementations and configuration.

### 4.1 Input validation

Before NLP processing: - Reject null or malformed review text. -
Normalize invalid Unicode sequences safely. - Preserve the original
normalized review text in the source review record. - Apply a documented
maximum input length and truncation policy. - Mark empty or
whitespace-only text as unprocessable. - Avoid logging full review text
in operational logs. - Record a stable reason code for skipped or failed
inputs.

Do not delete short reviews solely because they are short. A review such
as "Great game!" contains valid sentiment evidence.

### 4.2 Language identification

Use a language identification component such as fastText's language
identification model as an initial baseline.

Recommended behavior: - Store the detected language code and detection
confidence. - Route only languages supported by an evaluated model. -
Use a configurable confidence threshold. - If language confidence is
low, mark the review as `language_uncertain`; do not silently force it
into English. - Do not translate reviews automatically in the MVP.
Translation can change sentiment, idioms, sarcasm, and aspect meaning. -
Keep language-specific train/test splits and metrics.

Language identification itself must be evaluated on a manually verified
sample that reflects Steam review text, including short text, slang, and
mixed-language reviews.

### 4.3 Text normalization

Recommended normalization: - Unicode normalization (NFC). - Normalize
line endings and repeated whitespace. - Preserve meaningful punctuation,
negation, emojis, and casing information where the model benefits from
them. - Remove or normalize URLs and obvious markup according to a
versioned rule. - Decode HTML entities if present. - Preserve
contractions or apply tokenizer-native handling. - Do not remove stop
words indiscriminately for transformer models. - Do not stem or
lemmatize transformer input unless the model was trained with that
transformation.

For classic TF-IDF models, a separate vectorization pipeline may
lowercase text, tokenize, remove carefully selected stop words, and
optionally use n-grams. Keep this pipeline distinct from transformer
preprocessing.

### 4.4 Special text phenomena

Steam reviews may contain: - Sarcasm and irony. - Slang, abbreviations,
memes, and profanity. - Mixed languages and code-switching. - Emoji and
repeated punctuation. - Long narrative reviews. - Patch notes, quotes,
and copied text. - Comparisons with other games. - Positive and negative
opinions in the same review.

The annotation guidelines and evaluation set should deliberately include
these cases. Preprocessing must not erase the signals needed to
interpret them.

### 4.5 Duplicate and near-duplicate handling

-   Detect exact duplicates for training/evaluation leakage prevention.
-   Consider near-duplicate detection for spam/copied review analysis,
    but do not automatically delete source reviews.
-   Keep duplicate handling decisions in the dataset preparation
    manifest.
-   Ensure duplicated or near-duplicated texts do not cross
    train/validation/test partitions.

### 4.6 Dataset splits

Recommended split policy: - Split by review identity and duplicate
group, not by randomly splitting individual rows without leakage
checks. - Use a stratified train/validation/test split for the first
benchmark. - Keep the test set fixed and untouched during model
tuning. - Where temporal generalization matters, add a chronological
holdout set using later review dates. - Report language and class
distributions for every split. - Keep games represented across splits
when evaluating general-purpose review models, and add a game-held-out
evaluation if cross-game generalization is a key claim.

Suggested starting proportions: 70% train, 15% validation, 15% test.
These are defaults, not mandatory proportions; dataset size and class
balance may require adjustment.

------------------------------------------------------------------------

## 5. Sentiment analysis specification

### 5.1 Objective

Classify the overall sentiment expressed in a review, independently from
the reviewer's Steam recommendation.

### 5.2 Candidate approaches

Use a staged model-selection strategy rather than immediately selecting
the most complex model.

  -----------------------------------------------------------------------
  Candidate               Description             Role
  ----------------------- ----------------------- -----------------------
  Majority-class baseline Always predicts the     Minimum benchmark
                          most common class       

  TF-IDF + Logistic       Sparse n-gram features  Interpretable, fast
  Regression              with linear classifier  baseline

  TF-IDF + Linear SVM     Linear margin-based     Strong classic-text
                          classifier              baseline

  Fine-tuned transformer  Fine-tune a pretrained  Candidate production
                          language model          model

  Multilingual            Shared model across     Candidate for
  transformer             supported languages     multilingual expansion
  -----------------------------------------------------------------------

Possible transformer families include DistilBERT, BERT, RoBERTa, and
multilingual models such as XLM-R. The exact checkpoint must be selected
through benchmark results, license review, latency testing, and language
coverage---not by model popularity alone.

### 5.3 Input contract

Required: - `review_id` - normalized review text - detected language -
preprocessing version

Optional context such as game title, genre, playtime, or Steam
recommendation should not be used in the initial text-only benchmark. If
contextual features are tested later, compare against the text-only
baseline and document potential leakage and bias.

### 5.4 Output contract

``` json
{
  "task": "sentiment",
  "label": "positive",
  "confidence": 0.91,
  "probabilities": {
    "positive": 0.91,
    "negative": 0.06,
    "neutral": 0.03
  },
  "model_key": "steam-review-sentiment",
  "model_version": "1.0.0"
}
```

The values above are illustrative only.

### 5.5 Training data and annotation

-   Prefer a manually labeled, representative Steam review dataset for
    the target domain.
-   Use multiple annotators for a meaningful subset.
-   Provide a written annotation guide with examples of positive,
    negative, neutral, mixed, sarcastic, and insufficient-evidence
    cases.
-   Resolve disagreements through adjudication.
-   Measure inter-annotator agreement (for example, Cohen's kappa for
    two annotators or an appropriate multi-rater statistic).
-   Do not treat `voted_up` as unquestioned ground truth for text
    sentiment.
-   If Steam recommendation is used as weak supervision, label it
    explicitly as a proxy target and do not present its score as
    independently validated sentiment accuracy.

### 5.6 Class imbalance

Inspect class distribution before training. Candidate techniques: -
class weights; - stratified sampling; - controlled over/undersampling
within the training set only; - threshold tuning on validation data.

Do not balance the test set artificially if the intended production
distribution is naturally imbalanced. Report both natural-distribution
metrics and class-wise metrics.

### 5.7 Decision policy

Select thresholds on validation data. If confidence is below the chosen
threshold: - mark the prediction as low confidence or unclassified; -
optionally retain the top class and score for research; - exclude
low-confidence records from headline aggregate metrics or report them as
a separate coverage category.

The policy must be consistent across UI, API, and exports.

------------------------------------------------------------------------

## 6. Aspect-Based Sentiment Analysis (ABSA)

### 6.1 Objective

ABSA identifies the game aspects discussed in a review and estimates
sentiment toward each detected aspect.

Example:

> "The combat feels great, but the frame rate drops badly in crowded
> areas."

Expected interpretation: - `gameplay` → positive - `performance` →
negative

The overall review may be mixed. A single review-level sentiment label
cannot represent these distinct opinions.

### 6.2 ABSA sub-tasks

ABSA can be implemented as two linked tasks:

1.  **Aspect detection:** determine which predefined aspect or aspects
    are mentioned.
2.  **Aspect polarity:** classify sentiment toward each detected aspect.

For a mature implementation, aspect detection may also identify a
supporting text span. The MVP may begin with multi-label aspect
classification and add span extraction when annotation resources permit.

### 6.3 Initial aspect taxonomy

Start with a controlled taxonomy. The exact definitions and examples
must be documented before annotation.

  -----------------------------------------------------------------------
  Aspect key              Display label           Scope examples
  ----------------------- ----------------------- -----------------------
  `gameplay`              Gameplay                Mechanics, combat,
                                                  controls in play,
                                                  challenge, pacing

  `story`                 Story & Narrative       Plot, characters,
                                                  dialogue, writing

  `graphics`              Graphics & Visuals      Art direction, visual
                                                  quality, animation

  `audio`                 Audio & Music           Sound effects,
                                                  soundtrack, voice
                                                  acting

  `performance`           Performance & Stability FPS, stutter, crashes,
                                                  bugs, optimization

  `content`               Content & Replayability Missions, maps, modes,
                                                  endgame, replay value

  `multiplayer`           Multiplayer             Matchmaking, co-op,
                                                  PvP, servers, community
                                                  play

  `monetization`          Monetization            DLC, microtransactions,
                                                  pay-to-win, pricing
                                                  model

  `price_value`           Price & Value           Purchase price,
                                                  discounts, value for
                                                  money

  `support_updates`       Support & Updates       Patches, developer
                                                  communication, ongoing
                                                  support

  `accessibility`         Accessibility           Accessibility options
                                                  and usability barriers

  `other`                 Other                   Relevant game-related
                                                  aspect not covered
                                                  above
  -----------------------------------------------------------------------

Do not assume every game has every aspect. Aspect definitions should be
broad enough to generalize while remaining distinct.

### 6.4 Candidate architectures

  --------------------------------------------------------------------------
  Approach          Description       Advantages        Limitations
  ----------------- ----------------- ----------------- --------------------
  TF-IDF            One-vs-rest or    Fast, useful      Weak context
  multi-label       multi-label       baseline          understanding
  classifier        linear model                        

  Transformer       Predicts multiple Handles           Requires labeled
  multi-label       aspects per       contextual        examples
  classifier        review            language better   

  Token/span        Detects aspect    Provides evidence More expensive
  extraction        mentions in text  spans             annotation

  Joint ABSA model  Aspect detection  Can model         More complex
                    and polarity      dependencies      training/debugging
                    jointly                             
  --------------------------------------------------------------------------

Recommended MVP: 1. Establish taxonomy and annotation guide. 2. Train a
TF-IDF multi-label baseline. 3. Benchmark a transformer multi-label
model. 4. Add aspect polarity classification for detected aspects. 5.
Add span-level extraction only when there is sufficient labeled data and
a clear UI use case.

### 6.5 Aspect polarity labels

Use: - `positive` - `negative` - `neutral` - `mixed` only if the
annotation design explicitly supports mixed polarity at one aspect
level.

A simpler MVP can represent multiple separate aspect mentions with
different polarities rather than using `mixed`.

### 6.6 Annotation format

An annotation record should contain: - review ID; - aspect key; -
polarity; - optional evidence span; - annotator ID in the private
annotation system; - adjudication state; - annotation guideline version.

Do not expose annotator identity in public prediction data.

### 6.7 Output contract

``` json
{
  "task": "absa",
  "review_id": "example-review-id",
  "aspects": [
    {
      "aspect": "gameplay",
      "sentiment": "positive",
      "confidence": 0.94,
      "evidence": "The combat feels great"
    },
    {
      "aspect": "performance",
      "sentiment": "negative",
      "confidence": 0.89,
      "evidence": "the frame rate drops badly"
    }
  ],
  "model_key": "steam-review-absa",
  "model_version": "1.0.0"
}
```

The IDs, labels, and scores are illustrative.

### 6.8 Taxonomy governance

-   Aspect keys are stable machine identifiers.
-   Display labels and descriptions may change without changing the
    semantic key.
-   A material change in aspect definitions requires a taxonomy version
    change.
-   If an aspect is split or merged, preserve mapping metadata for
    historical analysis.
-   Do not compare aspect trends across incompatible taxonomy versions
    without an explicit mapping.

------------------------------------------------------------------------

## 7. Topic modeling specification

### 7.1 Objective

Discover recurring themes in review corpora without requiring every
theme to be predefined.

Topic modeling complements ABSA: - ABSA answers: "What aspect is
discussed, and what sentiment is expressed toward it?" - Topic modeling
answers: "What recurring themes or discussion patterns appear in these
reviews?"

A topic is not automatically an aspect. For example, a topic may
represent "late-game boss difficulty" and span gameplay, content, and
balance.

### 7.2 Candidate methods

  -----------------------------------------------------------------------
  Method            Description       Strengths         Limitations
  ----------------- ----------------- ----------------- -----------------
  TF-IDF + NMF      Factorize         Reproducible,     Bag-of-words
                    document-term     relatively simple limitations
                    matrix                              

  LDA               Probabilistic     Established       Often weaker on
                    topic model       baseline          short/noisy texts

  BERTopic          Embeddings +      Semantic grouping Sensitive to
                    dimensionality    and useful        embedding and
                    reduction +       inspection        clustering
                    clustering +                        configuration
                    topic                               
                    representation                      

  Embedding         Sentence          Flexible semantic Requires careful
  clustering        embeddings +      representation    cluster
                    HDBSCAN/K-means                     validation
  -----------------------------------------------------------------------

Recommended evaluation: - Establish NMF or LDA as a traditional
baseline. - Benchmark BERTopic using Sentence Transformers embeddings,
UMAP, and HDBSCAN. - Compare coherence, diversity, stability, outlier
rate, and human interpretability. - Do not select a topic model solely
because its visualization looks attractive.

### 7.3 Corpus construction

Define the corpus before fitting: - one game or a group of games; -
language scope; - review date range; - review inclusion/exclusion
policy; - duplicate handling; - minimum text length; - whether positive
and negative reviews are analyzed together or separately.

For public game intelligence, a useful default is to fit topics per game
and language when there is sufficient data. Cross-game topic models can
be useful for comparative research but need a consistent corpus and
versioned scope.

### 7.4 Short-document challenge

Steam reviews may be very short. Topic models can struggle when
documents contain only a few words.

Mitigations: - use sentence/document embeddings; - aggregate only when
the research question permits it; - enforce a minimum corpus size; -
report outlier/noise assignments; - avoid presenting unstable clusters
as established topics; - consider phrase-level features for classic
topic models.

Do not concatenate unrelated reviews into artificial documents merely to
increase text length.

### 7.5 Topic model output

For each topic, store: - topic key and model version; - human-readable
label; - representative terms; - representative review IDs or examples,
subject to privacy/source policy; - topic size; - coherence/diversity
metrics; - outlier designation.

For each review assignment, store: - review ID; - topic ID; - assignment
score where supported; - primary-topic flag if the method produces
one; - pipeline run ID.

Some topic methods produce hard cluster assignments rather than
calibrated probabilities. Do not label every cluster distance or
membership strength as a probability.

### 7.6 Human topic labeling

Topic labels should be reviewed by a human before being displayed as
authoritative descriptions.

Suggested workflow: 1. Generate candidate topics. 2. Inspect
representative terms and representative reviews. 3. Merge redundant
topics or split incoherent clusters where justified. 4. Assign concise
labels and descriptions. 5. Record curator and labeling
guideline/version. 6. Publish topic model version and corpus scope.

The model's raw topic number is not a stable semantic identity across
retraining.

### 7.7 Topic quality checks

Evaluate: - topic coherence; - topic diversity; - topic size
distribution; - outlier/noise proportion; - redundancy between topics; -
stability across random seeds or resampled corpora; - human
interpretability; - coverage of important review themes.

Use human review as a required complement to automatic metrics.

------------------------------------------------------------------------

## 8. Model selection strategy

### 8.1 Selection principles

Select models using evidence across: - predictive quality; - per-class
and per-language performance; - robustness to noisy user-generated
text; - inference latency and throughput; - memory and compute
requirements; - model and dataset licensing; - reproducibility and
maintainability; - explainability and operational complexity.

A marginal metric improvement may not justify a much larger or slower
model.

### 8.2 Recommended staged selection

**Stage 1 --- Baselines** - Majority-class baseline. - TF-IDF + Logistic
Regression. - TF-IDF + Linear SVM. - NMF/LDA topic baseline.

**Stage 2 --- Neural candidates** - Fine-tuned pretrained transformer
for sentiment. - Transformer multi-label model for aspects. - Sentence
Transformer embeddings + BERTopic for topics.

**Stage 3 --- Operational validation** - Benchmark latency on realistic
review lengths. - Measure throughput with the intended worker
hardware. - Evaluate memory usage and batch-size behavior. - Test long
reviews, empty reviews, mixed-language reviews, slang, and malformed
text. - Confirm model license and artifact distribution rights.

**Stage 4 --- Release decision** - Compare candidates against
predeclared acceptance criteria. - Review error slices and confusion
matrices. - Record limitations and intended use. - Approve a specific
immutable model artifact and configuration.

### 8.3 Avoid model selection by benchmark score alone

A model with high overall accuracy can fail on minority classes or
languages. Report: - macro F1; - per-class precision, recall, and F1; -
confusion matrix; - calibration metrics where confidence is used; -
per-language metrics; - temporal holdout metrics; - coverage and
abstention rate; - inference latency and throughput.

------------------------------------------------------------------------

## 9. Evaluation methodology

### 9.1 Evaluation dataset governance

-   Maintain a versioned, manually reviewed evaluation dataset.
-   Keep the final test set inaccessible to routine training/tuning
    workflows.
-   Document annotation instructions, annotator count, adjudication,
    language, date range, and game coverage.
-   Prevent duplicate or near-duplicate leakage across splits.
-   Track dataset lineage and license/source restrictions.
-   Re-evaluate when the taxonomy, preprocessing, or model task
    definition changes.

### 9.2 Sentiment metrics

  -----------------------------------------------------------------------
  Metric                              Why it matters
  ----------------------------------- -----------------------------------
  Accuracy                            Overall fraction of correct
                                      predictions; can hide imbalance

  Precision                           Reliability of positive predictions
                                      for a class

  Recall                              Fraction of actual class examples
                                      recovered

  Macro F1                            Gives each class equal weight

  Weighted F1                         Reflects class frequency

  Confusion matrix                    Shows systematic class confusion

  Calibration / Brier score           Assesses probability quality when
                                      probabilities are used

  Coverage                            Fraction of eligible reviews
                                      receiving a usable prediction
  -----------------------------------------------------------------------

Primary selection metric: **macro F1**, supported by per-class
precision/recall and confusion-matrix analysis. Accuracy is
supplementary, not the sole acceptance metric.

### 9.3 ABSA metrics

Aspect detection: - micro and macro precision/recall/F1; - per-aspect
F1; - exact match only as a supplementary strict metric; - span-level F1
if span extraction is implemented.

Aspect polarity: - macro F1 across polarity classes; - per-aspect
polarity confusion matrices; - joint aspect-plus-polarity F1 to measure
end-to-end performance.

Report both detection and polarity quality. A polarity model evaluated
only on gold-standard aspects can overstate end-to-end quality.

### 9.4 Topic modeling metrics

Automatic: - coherence (such as NPMI or a clearly specified coherence
implementation); - topic diversity; - outlier rate; - topic size
distribution; - stability across seeds/resamples.

Human: - topic interpretability rating; - redundancy rating; -
usefulness for understanding game feedback; - review-level assignment
plausibility.

Topic metrics depend on tokenization, corpus, and implementation. Record
those settings with every evaluation result.

### 9.5 Slice-based evaluation

At minimum, inspect performance by: - language; - review length; -
positive vs negative recommendation (`voted_up`); - class; - game; -
review date period; - Early Access vs non-Early Access, if available; -
purchase type, if available and appropriate.

Do not infer protected or sensitive personal attributes from review
text.

### 9.6 Error analysis

Review false positives, false negatives, and low-confidence examples.
Tag error categories such as: - sarcasm/irony; - mixed sentiment; -
negation; - domain-specific slang; - comparison between games; - quoted
text; - aspect ambiguity; - language detection error; - insufficient
context; - annotation disagreement.

Use error analysis to decide whether to improve labels, data coverage,
preprocessing, model architecture, or abstention policy.

### 9.7 Provisional release gates

The following are initial engineering targets, not achieved performance
claims. They must be reviewed after the first labeled dataset is built.

  -----------------------------------------------------------------------
  Task                    Provisional target      Additional requirement
  ----------------------- ----------------------- -----------------------
  Sentiment               Macro F1 ≥ 0.80         No major class-specific
                                                  failure; report
                                                  per-language metrics

  Aspect detection        Micro F1 ≥ 0.75         Report per-aspect macro
                                                  F1

  Aspect polarity         Macro F1 ≥ 0.75         Evaluate end-to-end
                                                  aspect-plus-polarity

  Topic modeling          No universal numeric    Human interpretability
                          gate                    and stability review
                                                  required

  Confidence              Calibration assessed    Threshold chosen on
                                                  validation set

  Operations              Stable batch inference  Latency, memory, and
                                                  failure recovery
                                                  benchmarked
  -----------------------------------------------------------------------

If the dataset is small or annotation agreement is low, targets may be
unrealistic. In that case, publish the limitation and use a
restricted/experimental label rather than relaxing evaluation silently.

------------------------------------------------------------------------

## 10. Inference and production execution

### 10.1 Batch inference

Use background workers for NLP inference. Avoid running expensive model
inference inside synchronous public API requests.

Recommended flow: 1. Query unprocessed reviews for a specific model
version. 2. Build bounded batches. 3. Run preprocessing and inference.
4. Validate output schema and numeric ranges. 5. Persist predictions in
a transaction. 6. Update pipeline counters. 7. Trigger or enqueue
aggregation after successful completion.

### 10.2 Batch sizing

Batch size depends on model, sequence length, and hardware. Determine it
empirically. Use configurable batch sizes and handle out-of-memory
errors by reducing batch size or splitting the batch.

### 10.3 Retry and failure behavior

-   Retry transient infrastructure errors with bounded backoff.
-   Do not retry deterministic malformed-input errors indefinitely.
-   Record item-level failures where useful.
-   A failed batch must not be counted as successful.
-   Ensure reruns are idempotent.
-   Do not silently drop failed reviews from coverage metrics.

### 10.4 Model serving

For MVP, load approved models in Celery workers or a dedicated inference
process if resource contention becomes measurable. Keep model loading
and inference behind a stable internal interface so deployment can
change without changing API contracts.

### 10.5 Resource controls

-   Limit concurrent model tasks based on memory.
-   Use bounded queues.
-   Separate ingestion and NLP worker concurrency.
-   Monitor CPU, RAM, GPU memory where applicable, queue depth, and
    inference duration.
-   Do not assume GPU availability in the first deployment.

------------------------------------------------------------------------

## 11. Model versioning and reproducibility

### 11.1 Version identity

Every model release must have: - stable `model_key`; - immutable
`version`; - task identifier; - artifact checksum; -
tokenizer/preprocessor identity; - label schema or taxonomy version; -
training dataset version; - evaluation dataset version; - training code
commit; - hyperparameter/configuration snapshot; - framework/library
versions; - creation and approval metadata.

Recommended semantic versioning: - **MAJOR:** incompatible task/label
schema or output contract. - **MINOR:** materially changed model
behavior or retraining with a new approved release. - **PATCH:**
packaging/runtime fix that does not intentionally change model outputs.
If numerical outputs can change, record a new artifact/build identifier
even if the semantic version remains compatible.

Model version labels are immutable. Never replace an artifact behind an
existing version string.

### 11.2 Versioned dependencies

A prediction is reproducible only if the relevant components are
identified: - model artifact; - tokenizer; - preprocessing
configuration; - label schema/taxonomy; - inference code version; -
relevant library/runtime versions.

Store a compact manifest and artifact checksum. Avoid relying on a
mutable `latest` model reference for historical results.

### 11.3 Model registry lifecycle

Suggested lifecycle states: - `development` - `candidate` - `approved` -
`active` - `deprecated` - `retired`

Only approved/active models may be selected for public production
analytics. A model can be deprecated for new inference while its
historical predictions remain available.

### 11.4 Promotion workflow

``` mermaid
flowchart TD
    A[Dataset and Annotation Review] --> B[Train Candidate]
    B --> C[Offline Evaluation]
    C --> D{Meets Release Gates?}
    D -->|No| E[Reject or Iterate]
    D -->|Yes| F[Error and Bias Review]
    F --> G[Artifact and License Review]
    G --> H[Register Candidate]
    H --> I[Shadow / Sample Validation]
    I --> J{Approved?}
    J -->|No| E
    J -->|Yes| K[Activate Version]
    K --> L[Run Production Inference]
    L --> M[Monitor Quality and Drift]
```

### 11.5 Prediction provenance

Every stored prediction must be traceable to: - review ID; - model
ID/version; - pipeline run ID; - prediction timestamp; -
preprocessing/label schema version, directly or through the immutable
model manifest.

For aggregate analytics, record the exact model-version combination
used. A combined analytics version key may include sentiment, ABSA, and
topic versions.

### 11.6 Reprocessing policy

When a new model version is approved: 1. Keep existing predictions
intact. 2. Create a new pipeline run. 3. Process the selected review
corpus with the new version. 4. Compare old and new metrics on the fixed
evaluation set. 5. Recompute aggregates under a new model-version key.
6. Publish the new analytics version after validation. 7. Keep the prior
aggregate available for comparison or reproducibility.

Do not mix predictions from different model versions inside one
aggregate unless the aggregation contract explicitly defines and records
that mixture.

### 11.7 Rollback

Rollback means switching the active model selection back to a previously
approved immutable version. It does not mean deleting newer predictions.

After rollback: - new inference uses the selected prior version; -
historical predictions remain; - aggregates identify which version they
represent; - operational logs record the activation change.

------------------------------------------------------------------------

## 12. Monitoring, drift, and quality management

### 12.1 Operational monitoring

Track: - number of reviews eligible for processing; - processed,
skipped, and failed counts; - queue depth and task age; - batch
throughput; - inference latency percentiles; - worker memory and CPU/GPU
use; - model load failures; - invalid output count; - prediction
coverage by game and language.

### 12.2 Data and prediction monitoring

Monitor: - language distribution changes; - review length
distribution; - class prediction distribution; - confidence
distribution; - aspect prevalence; - topic prevalence and outlier
rate; - shifts by game and time window.

A shift is a signal for investigation, not proof that model quality has
declined.

### 12.3 Drift types

-   **Data drift:** input text/language/length distribution changes.
-   **Prediction drift:** model output distribution changes.
-   **Concept drift:** relationship between review text and correct
    labels changes.
-   **Taxonomy drift:** aspect/topic definitions or meanings change.

Ground-truth evaluation on a newly annotated sample is needed to
determine whether predictive quality has degraded.

### 12.4 Human review loop

Periodically sample: - low-confidence predictions; - new slang or
emerging game-specific terms; - reviews from underrepresented
languages; - disagreement between Steam recommendation and model
sentiment; - newly appearing aspects/topics; - high-impact error
categories.

Human review should create new labeled examples only through a
documented annotation workflow.

------------------------------------------------------------------------

## 13. Dataset and experiment management

### 13.1 Dataset manifest

Every training/evaluation dataset release should record: - dataset
version and creation date; - source and collection window; - included
games and languages; - sampling method; - inclusion/exclusion
criteria; - duplicate handling; - label distribution; - annotation
guideline version; - annotator/adjudication process; -
train/validation/test split identifiers; - license and usage
restrictions; - checksum or immutable artifact reference.

### 13.2 Experiment tracking

Use MLflow or an equivalent experiment tracker to record: - experiment
ID; - dataset version; - code commit; - model checkpoint/base model; -
hyperparameters; - metrics by split and slice; - confusion matrices and
evaluation artifacts; - runtime and hardware details; - selected
artifact URI and checksum.

MLflow is a recommended tool, not a mandatory runtime dependency for
inference.

### 13.3 Reproducibility

-   Set and record random seeds.
-   Pin dependency versions.
-   Store training configuration.
-   Preserve dataset manifests.
-   Record hardware/runtime where it can affect results.
-   Keep evaluation scripts version-controlled.
-   Do not claim bit-for-bit reproducibility if nondeterministic GPU
    operations or mutable external artifacts prevent it.

------------------------------------------------------------------------

## 14. Security, privacy, and responsible use

-   Do not use Steam account identifiers or personal profile details as
    model features.
-   Avoid retaining unnecessary author information.
-   Restrict access to private annotation datasets and model artifacts.
-   Sanitize review text in logs and error traces.
-   Treat review content as untrusted user-generated input.
-   Do not execute code, links, or instructions found inside reviews.
-   Do not infer sensitive personal attributes from review text.
-   Respect applicable Steam terms, dataset licenses, and institutional
    policies.
-   Publish model limitations and collection/sampling methodology.
-   Do not present model output as a definitive judgment of a game or
    its community.

------------------------------------------------------------------------

## 15. API and database integration

The ML subsystem should expose internal service interfaces to the
application and workers. Public API responses should not expose internal
model artifact paths or secrets.

### 15.1 Internal service interfaces

Suggested logical operations: - `detect_language(review_text)` -
`predict_sentiment(review_text, language, model_version)` -
`predict_aspects(review_text, language, model_version)` -
`assign_topics(review_text, corpus_model_version)` -
`validate_prediction(task, output_schema)` -
`run_batch(task, selection, model_version)`

These are service-level contracts, not necessarily public HTTP
endpoints.

### 15.2 Database mapping

  ML concept                   Database table
  ---------------------------- ------------------------
  Model registry               `ml_model`
  Pipeline execution           `pipeline_run`
  Item-level execution error   `pipeline_run_item`
  Overall sentiment            `sentiment_prediction`
  Aspect taxonomy              `aspect`
  Aspect polarity/detection    `aspect_prediction`
  Topic definition             `topic`
  Review-topic assignment      `review_topic`
  Game/time aggregates         `game_analytic`

The model manifest should include fields that are not represented as
first-class columns in the initial database schema, such as dataset
checksum, preprocessing version, taxonomy version, artifact checksum,
and code commit. These may be stored in `ml_model.config` or a dedicated
immutable manifest artifact, with selected searchable fields promoted to
columns if needed.

### 15.3 Output validation

Before persistence: - task name matches the requested pipeline; - model
version is registered and approved for the intended environment; -
labels belong to the versioned label schema; - confidence and
probabilities are within valid ranges; - probability vectors satisfy the
documented tolerance; - aspect keys exist in the selected taxonomy
version; - evidence spans are within the normalized input bounds; -
topic IDs belong to the selected topic model version; - no unexpected
personal metadata is included.

------------------------------------------------------------------------

## 16. MVP implementation roadmap

### Phase 1 --- Sentiment baseline

-   Build and document an English review annotation set.
-   Implement language detection and preprocessing.
-   Train majority, TF-IDF Logistic Regression, and Linear SVM
    baselines.
-   Evaluate macro F1, per-class metrics, calibration, and error slices.
-   Register one approved sentiment model.
-   Persist versioned sentiment predictions.

### Phase 2 --- ABSA

-   Finalize aspect taxonomy and annotation guidelines.
-   Label a representative set of aspect mentions and polarity.
-   Train a multi-label aspect baseline.
-   Benchmark a transformer candidate.
-   Add aspect polarity and confidence handling.
-   Persist aspect predictions with provenance.

### Phase 3 --- Topic modeling

-   Build per-game/per-language corpora with minimum-size rules.
-   Compare NMF/LDA and BERTopic candidates.
-   Evaluate coherence, diversity, stability, outliers, and human
    interpretability.
-   Add human-readable topic curation.
-   Persist topics and review assignments.

### Phase 4 --- Production quality

-   Add batch inference and retry behavior.
-   Add model registry promotion/rollback.
-   Add monitoring and drift dashboards.
-   Add reprocessing and aggregate version comparison.
-   Publish methodology and known limitations.

------------------------------------------------------------------------

## 17. Open decisions

The following decisions require empirical results or product policy
before production:

1.  Whether the first sentiment release is binary or three-class.
2.  The exact English training/evaluation dataset and its license.
3.  The minimum number of manually annotated examples per class and
    aspect.
4.  The supported language list and language-detection threshold.
5.  The final transformer checkpoint, if it outperforms classic
    baselines enough to justify its cost.
6.  The ABSA implementation depth: multi-label classification only, or
    span extraction as well.
7.  Whether topic models are per-game, per-language, or shared across
    games for each use case.
8.  Minimum corpus size for publishing topic results.
9.  Confidence/abstention thresholds for each task.
10. The aggregate sentiment score formula and treatment of unclassified
    reviews.
11. Model artifact storage and access policy.
12. Evaluation cadence and the process for collecting newly annotated
    examples.

------------------------------------------------------------------------

## 18. Final specification summary

SteamScoop's ML architecture should be incremental and evidence-driven:

-   Begin with transparent, reproducible classical baselines.
-   Adopt transformer models only when measured quality gains justify
    their operational cost.
-   Treat sentiment, ABSA, and topic modeling as separate but
    complementary tasks.
-   Preserve source recommendation signals separately from model
    interpretation.
-   Version preprocessing, taxonomies, datasets, models, and pipeline
    runs.
-   Evaluate class-wise, language-wise, temporally, and with human
    review.
-   Keep historical predictions and aggregates reproducible when models
    change.
-   Communicate uncertainty and limitations instead of presenting
    predictions as facts.

The goal is not simply to attach AI labels to Steam reviews. The goal is
to build a defensible, inspectable, and reproducible game-research
pipeline.
