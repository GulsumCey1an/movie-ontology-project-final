# 🎬 Movie Knowledge Graph Ontology

[![OWL 2](https://img.shields.io/badge/OWL-2.0-blue)](movie-ontology.owl)
[![SHACL](https://img.shields.io/badge/SHACL-v2.1-green)](shapes/movie-shapes.ttl)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Knowledge Engineering and Ontologies — Spring 2026 Course Project**

An OWL 2 ontology and knowledge graph for the movie domain, supporting SPARQL querying, SHACL validation, Wikidata-based population, and LLM-driven enrichment.

---

## 📋 Project Objective

Design and implement an IMDb-like Movie Knowledge Graph that:
- Models movies, TV series, persons, genres, awards, franchises, and streaming platforms using OWL 2
- Populates the KG from Wikidata (SPARQL) and LLMs (Shimizu et al. 2024 method)
- Supports 25 competency questions via SPARQL
- Validates data quality with SHACL shapes
- Integrates with LLMs for ontology-grounded question answering

---

## 👥 Team Members

| Name | Student ID | Email |
|------|-----------|-------|
| Gülsüm Ceylan | 220316065 | 220316065@ogr.cbu.edu.tr |
| Furkan Üstüncan | 220316049 | 220316049@ogr.cbu.edu.tr |

---

## 📂 Repository Structure

```
movie-ontology-project/
├── movie-ontology.owl              # OWL 2 RDF/XML ontology (v2.1)
├── movie-ontology.ttl              # Turtle serialisation (same content)
├── README.md                       # This file
├── CHANGELOG.md                    # Version history
│
├── shapes/
│   └── movie-shapes.ttl           # SHACL validation shapes (5 shapes)
│
├── queries/
│   └── example-queries.sparql     # 25 SPARQL queries (CQ1–CQ25)
│
├── scripts/
│   ├── fetch_movies_wikidata.py   # Wikidata SPARQL → OWL population
│   ├── populate_with_llm.py       # LLM-based population (Shimizu 2024)
│   └── setup_fuseki.sh            # Apache Jena Fuseki setup script
│
├── data/
│   ├── seed_movies.csv            # Wikidata QIDs for target films
│   ├── llm_population_output.json # LLM extraction results (3 films)
│   └── validation-report.txt     # pySHACL validation results
│
├── docs/
│   └── ORSD-MovieOntology-v2.docx # Ontology Requirements Specification
│
└── widoco-docs/
    └── index-en.html              # Ontology documentation (WIDOCO-style)
```

---

## 🔗 Links

- **GitHub Repository:** [github.com/GulsumCey1an/movie-ontology-project](https://github.com/GulsumCey1an/movie-ontology-project)
- **WIDOCO Documentation:** [GulsumCey1an.github.io/movie-ontology-project](https://GulsumCey1an.github.io/movie-ontology-project/widoco-docs/index-en.html)
- **SPARQL Endpoint (local):** `http://localhost:3030/movies/sparql` (see setup below)

---

## 📊 Dataset Sources

| Source | Type | Access | Used for |
|--------|------|--------|----------|
| [Wikidata SPARQL](https://query.wikidata.org/) | Linked Data | Public | Core metadata (title, year, director, cast) |
| [TMDb API](https://api.themoviedb.org/3/) | REST JSON | Free key | Plot summaries, streaming availability |
| [IMDb Datasets](https://datasets.imdbws.com/) | TSV | Free download | Ratings at scale |
| [DBpedia SPARQL](https://dbpedia.org/sparql) | Linked Data | Public | Cross-check / backup |
| Claude (Anthropic) | LLM | API | Ontology population from plot text |

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.9+
- Java 11+ (for Fuseki)

### Python dependencies

```bash
pip install rdflib pyshacl SPARQLWrapper requests
```

### Validate the ontology with SHACL

```bash
pyshacl -s shapes/movie-shapes.ttl -i none movie-ontology.owl
```

### Run LLM population demo

```bash
python scripts/populate_with_llm.py --demo --out movie-ontology.owl
```

### Start SPARQL endpoint (Apache Jena Fuseki)

```bash
bash scripts/setup_fuseki.sh
# Then open: http://localhost:3030
```

### Convert OWL to Turtle

```python
from rdflib import Graph
g = Graph()
g.parse("movie-ontology.owl", format="xml")
g.serialize("movie-ontology.ttl", format="turtle")
```

---

## 🧪 Ontology Statistics (v2.1)

| Metric | v1 | v2.1 |
|--------|-----|------|
| Classes | 20 | 25 |
| Object Properties | 15 | 21 |
| Data Properties | 9 | 14 |
| Named Individuals | 26 | 51 |
| Competency Questions | 16 | 25 |
| External Alignments | 0 | 5 |
| SHACL Shapes | 0 | 5 |

---

## 📖 Key References

1. Shimizu, C., Barua, A., Hitzler, P. et al. (2024). *Ontology Population using LLMs*. arXiv:2411.01612.
2. Allemang, D. & Sequeda, J. (2024). *Increasing the LLM Accuracy for Question Answering: Ontologies to the Rescue!* arXiv:2405.11706.
3. Fernandez, M. H. (2023). *Personalized ontology and deep training tree-based optimal GRU-RNN*. Wiley. DOI: 10.1002/cpe.7420.
4. Fernández-López, M. et al. (1997). *METHONTOLOGY: From Ontological Art towards Ontological Engineering*.
5. Garijo, D. (2017). *WIDOCO: A Wizard for Documenting Ontologies*. GitHub.
