# From Free Text to Validated Drug-Disease Relations

Code and data for the paper:

> Mustafa M., Al-Doghman F., Hussain F., Ali M. *From Free Text to Validated Drug-Disease Relations: Benchmarking Open-Weight LLMs with UMLS Normalization and Multi-Source Evidence.* (Submitted to *Applied Artificial Intelligence*.)

The study has two levels:

- **Level 1 - model benchmarking.** Five locally deployed open-weight LLMs extract drug indications from 500 expert-annotated LabeledIn records with one frozen zero-shot prompt. Outputs are scored against the LabeledIn gold standard at UMLS concept level, with bootstrap confidence intervals and paired bootstrap tests.
- **Level 2 - validation framework.** The selected model (Gemma3) is applied to 500 DrugBank records, producing 2,110 candidate drug-disease relations. Each relation is normalized to UMLS, disambiguated with same-drug DrugCentral evidence, corroborated against DrugCentral, DailyMed, openFDA and LabeledIn, and screened by a non-therapeutic safety gate. 1,074 relations (50.9%) were automatically confirmed and 1,036 (49.1%) were routed to review.

---

## Repository contents

### `level1_labeledin/`

| File | Description |
|---|---|
| `openbioLLM.ipynb`, `pubmedlama.ipynb`, `gemma3.ipynb`, `medgemma.ipynb`, `Qwen3-8B.ipynb` | Run each model on the 500 LabeledIn records through Ollama |
| `llm_models_evaluation.ipynb` | Concept-level scoring against the LabeledIn gold standard |
| `finalstatistics.ipynb` | Micro-averaged precision, recall and F1; bootstrap 95% CIs; paired bootstrap comparisons |
| `LabeledIn_5_Model_Bootstrap_Statistics.xlsx` | Output of `finalstatistics.ipynb` (Tables 4-5 of the paper) |
| LabeledIn results files | Per-record model outputs for the five models |

### `level2_extraction_results/`

| File | Description |
|---|---|
| `drug_disease_relations_validated_SHAREABLE.csv` | All 2,110 extracted relations with every validation step and the final decision (DrugBank text and UMLS names removed - see *Licensing*) |
| `data_dictionary_relations.csv` | Plain-English description of all 55 columns |
| `validation_statistics_FINAL.csv` | Overall counts (relations, confirmed, review, drug-level coverage) |
| `validation_source_statistics_FINAL.csv` | Evidence counts per source (Table 6) |
| `validation_status_summary_FINAL.csv` | Counts per final validation status (Table 7) |
| `ablation_study.py` | Cumulative component ablation (Figure 3) - runs on the shareable CSV |
| `ablation_study_results.csv` | Output of `ablation_study.py` |
| `sample20.py` | Draws the random sample of 20 automatically confirmed relations (seed 42) |
| `LLM_Manual_Validation_Audit_30_plus_20_shareable.xlsx` | Manual audit of 30 review-routed relations (purposive) and 20 automatically confirmed relations (random) |

---

## Models and settings (Level 1)

All models were run locally with [Ollama](https://ollama.com), temperature 0.1, context window 4,096 tokens, and the same frozen prompt (Box 1 of the paper). Maximum generation length was 1,000 tokens (3,000 for MedGemma 1.5, which emits a reasoning trace).

| Model | Ollama tag |
|---|---|
| OpenBioLLM-8B | `koesn/llama3-openbiollm-8b:q5_K_M` |
| PubMed-Llama-3B | `kronos483/Llama-3.2-3B-PubMed:latest` |
| MedGemma 1.5-4B | `medgemma1.5:4b` |
| Gemma3-4B | `gemma3:4b` |
| Qwen3-8B | `qwen3:8b` (thinking disabled) |

Bootstrap: 10,000 resamples of the 500 records, percentile 95% intervals, seed 42.

---

## Reproducing the results

**Level 1.** Open the notebooks in Google Colab (GPU runtime), set the data path in the first cells, and run them in order: model notebooks → `llm_models_evaluation.ipynb` → `finalstatistics.ipynb`.

**Ablation (Level 2).** No licensed data are needed:

```bash
python ablation_study.py --input drug_disease_relations_validated_SHAREABLE.csv
```

Expected result: 210 → 338 → 389 → 1,103 → 1,074 automatically confirmed relations (29 blocked by the safety gate).

**Random confirmed-relation sample.**

```bash
python sample20.py
```

Draws the same 20 relations used in the manual check (pandas `DataFrame.sample`, `random_state = 42`).

---

## Key columns of the relations file

| Column | Meaning |
|---|---|
| `drug_name`, `drugbank_id` | The drug |
| `gemma_disease` | Disease phrase extracted by Gemma3 |
| `gemma_umls_cui` | Accepted UMLS concept |
| `evidence_sources` | Sources that supported the relation |
| `validation_status` | Final status (Table 3 of the paper) |
| `add_to_kg` | `YES` = automatically confirmed (1,074); `NO_NOT_YET` = kept for review (964); `NO` = non-therapeutic or unresolved (72) |

See `data_dictionary_relations.csv` for all 55 columns. UMLS semantic type codes used in `gemma_umls_semantic_tuis`: T047 Disease or Syndrome, T191 Neoplastic Process, T048 Mental or Behavioral Dysfunction, T046 Pathologic Function, T033 Finding, T184 Sign or Symptom, T037 Injury or Poisoning, T020 Acquired Abnormality, T019 Congenital Abnormality, T190 Anatomical Abnormality, T049 Cell or Molecular Dysfunction.

---

## Data sources and licensing

| Source | Version | Use | Redistributed here? |
|---|---|---|---|
| DrugBank | 5.1.15 (academic licence) | Input indication text | **No.** Only DrugBank IDs and drug names (DrugBank Open Vocabulary, CC0) are included. Researchers with a DrugBank licence can retrieve the text by `drugbank_id`. |
| UMLS Metathesaurus | 2026AA | Concept normalization | **No concept names.** Only CUIs and semantic type codes are included. UMLS requires a licence from the U.S. National Library of Medicine. |
| DrugCentral | - | Structured indication evidence | **No indication names.** Only match results (TRUE/FALSE), UMLS CUIs and a similarity score are included. DrugCentral is available at https://drugcentral.org (CC BY-SA 4.0). |
| DailyMed / openFDA | Accessed 2026 | Regulatory label evidence | Matched label passages (U.S. government work, public domain) |
| LabeledIn | - | Gold standard (Level 1) and evidence (Level 2) | Model outputs on LabeledIn records |

**Licences for this repository**

- Code: MIT License (`LICENSE`)
- Data files: CC BY 4.0 (`LICENSE-DATA`)

---

## Citation

If you use this code or data, please cite the paper above and the archived version of this repository: 10.5281/zenodo.23620569.

## Contact

Marwa Mustafa, University of Technology Sydney
