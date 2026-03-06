# Austronesian Research Toolkit

A Python toolkit for researching Austronesian language **roots (字根)**, **phonology (字音)**, **cognates (同源詞)**, and **sound change (音變)** — with a focus on Taiwanese indigenous languages, Philippine languages, and related Austronesian families.

---

## Overview

The Austronesian language family is one of the largest in the world, with over 1,200 languages spoken across Taiwan, the Philippines, Indonesia, Madagascar, and the Pacific. Taiwan is considered the **homeland** of the Austronesian expansion, making it especially important for historical-comparative linguistics.

This toolkit provides:

| Component | Description |
|-----------|-------------|
| **Data models** | `Language`, `Lexeme`, `CognateSet` |
| **ABVD client** | Fetch vocabulary and cognate data from the [Austronesian Basic Vocabulary Database](https://abvd.eva.mpg.de/) |
| **ACD scraper** | Query reconstructed roots from the [Austronesian Comparative Dictionary](https://www.trussel2.com/ACD/) |
| **Cognate analysis** | Heuristic cognate detection using edit-distance clustering and database labels |
| **Sound-change analysis** | Phoneme tokenisation, rule application, and correspondence-table generation |
| **Root utilities** | Proto-form normalisation, naive reconstruction, and formatted comparison tables |
| **CLI** | Command-line access to all major features |

---

## Key Online Databases

| Database | URL | Focus |
|----------|-----|-------|
| ABVD | https://abvd.eva.mpg.de/ | 400+ languages, 210 basic meanings, cognate labels |
| ACD | https://www.trussel2.com/ACD/ | Proto-Austronesian reconstruction, roots, reflexes |
| POLLEX | https://pollex.org.nz/ | Proto-Polynesian lexicon |
| Glottolog | https://glottolog.org/ | Global language classification and genealogy |
| WALS | https://wals.info/ | Cross-linguistic structural features |
| Lexibank | https://lexibank.clld.org/ | Downloadable word-list datasets |
| PHOIBLE | https://phoible.org/ | Phoneme inventories |
| Ethnologue | https://ethnologue.com/ | Language distribution and speaker counts |
| ASJP | https://asjp.clld.org/ | Language distance from Swadesh lists |
| IDS | https://ids.clld.org/ | Intercontinental Dictionary Series |
| Concepticon | https://concepticon.clld.org/ | Concept-list cross-reference |
| Academia Sinica | https://www.sinica.edu.tw/ | Formosan language archives (Taiwan) |
| Taiwan Indigenous Languages | https://ilrdc.tw/ | Official multi-tribal dictionaries |

---

## Installation

Requires Python 3.9+.

```bash
pip install -e ".[dev]"
```

---

## Quick Start

### Python API

```python
from austronesian.databases.abvd import ABVDClient
from austronesian.databases.acd import ACDClient
from austronesian.analysis.cognates import find_potential_cognates
from austronesian.analysis.roots import format_comparison_table, reconstruct_proto
from austronesian.analysis.sound_change import build_correspondence_table

# --- ABVD: fetch a language and its words ---
client = ABVDClient()
lang = client.get_language(1)          # Malagasy
print(lang)

words = client.get_words(1)
for w in words[:5]:
    print(w)

# --- ABVD: compare a meaning across languages ---
table = client.compare_word("eye", language_ids=[1, 2, 3])
for lang_name, forms in table.items():
    print(f"{lang_name}: {forms}")

# --- ABVD: search for languages ---
amis_langs = client.search_languages("Amis")

# --- ACD: search for reconstructed roots ---
acd = ACDClient()
roots = acd.search("mata")
for root in roots:
    print(format_comparison_table(root))

# --- Heuristic cognate clustering ---
from austronesian.models.lexeme import Lexeme
lexemes = [
    Lexeme(language_name="Amis",    form="mata", meaning="eye"),
    Lexeme(language_name="Tagalog", form="mata", meaning="eye"),
    Lexeme(language_name="Malay",   form="mata", meaning="eye"),
    Lexeme(language_name="Maori",   form="mata", meaning="eye"),
]
cognate_sets = find_potential_cognates(lexemes, meaning="eye", threshold=0.4)
for cs in cognate_sets:
    print(format_comparison_table(cs))

# --- Sound-change rule application ---
from austronesian.analysis.sound_change import apply_rules, tokenise
tokenise("ngipen")               # ['ng', 'i', 'p', 'e', 'n']
apply_rules("mata", {"t": "d"}) # 'mada'

# --- Proto-form reconstruction (naive, majority-vote) ---
from austronesian.models.cognate import CognateSet
cs = CognateSet(
    meaning="eye",
    members=[
        Lexeme(form="mata"),
        Lexeme(form="mata"),
        Lexeme(form="maca"),
    ],
)
print(reconstruct_proto(cs))   # *mata

# --- Phoneme correspondence table ---
corr = build_correspondence_table(cognate_sets, lang_a="Amis", lang_b="Tagalog")
print(corr)
```

### CLI

```bash
# Search ABVD for languages by name
austronesian abvd search-lang "Amis"

# Fetch metadata for ABVD language id=1
austronesian abvd language 1

# Compare the meaning "eye" across three languages
austronesian abvd compare "eye" --ids 1,2,3

# Search the ACD for the root "mata"
austronesian acd search "mata"
```

---

## Project Structure

```
Austronesian/
├── pyproject.toml                  # Build & dependency config
├── src/
│   └── austronesian/
│       ├── __init__.py
│       ├── models/
│       │   ├── language.py         # Language dataclass
│       │   ├── lexeme.py           # Lexeme (word form) dataclass
│       │   └── cognate.py          # CognateSet dataclass
│       ├── databases/
│       │   ├── abvd.py             # ABVD REST API client
│       │   └── acd.py              # ACD HTML scraper
│       ├── analysis/
│       │   ├── cognates.py         # Edit-distance cognate detection
│       │   ├── sound_change.py     # Phoneme tokenisation & correspondence tables
│       │   └── roots.py            # Proto-form utilities & display
│       └── cli/
│           └── main.py             # CLI entry point
├── data/
│   ├── raw/                        # Downloaded raw data
│   └── processed/                  # Processed/analysed output
├── notebooks/                      # Jupyter notebooks for exploration
└── tests/
    ├── test_models.py
    ├── test_abvd.py
    └── test_analysis.py
```

---

## Research Workflow

Recommended flow for **root / sound-change research**:

```
1. Use ABVD  → collect cognate sets across languages
2. Use ACD   → look up Proto-Austronesian reconstructions
3. Use find_potential_cognates() → cluster similar forms
4. Use build_correspondence_table() → identify sound correspondences
5. Use format_comparison_table()  → produce publishable comparison tables
6. Use reconstruct_proto()        → generate candidate proto-forms
```

Example comparison table output:

```
Meaning : eye
Proto   : *mata
───────────────────────────────────────
Language            Form
───────────────────────────────────────
Amis                mata
Malay               mata
Maori               mata
Tagalog             mata
───────────────────────────────────────
```

---

## Testing

```bash
pytest
```

55 tests cover models, the ABVD client (using mocked HTTP), and analysis utilities.

---

## References

- Blust, R. & Trussel, S. (ongoing). *Austronesian Comparative Dictionary*. https://www.trussel2.com/ACD/
- Greenhill, S.J., Blust, R., & Gray, R.D. (2008). *The Austronesian Basic Vocabulary Database: From Bioinformatics to Lexomics*. Evolutionary Bioinformatics, 4:271–283.
- Glottolog 4.x. https://glottolog.org/
- Blust, R. (2013). *The Austronesian Languages* (revised edition). Pacific Linguistics.
