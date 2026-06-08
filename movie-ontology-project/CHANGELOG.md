# Changelog

All notable changes to the Movie Knowledge Graph Ontology project are documented in this file. Format adapted from [Keep a Changelog](https://keepachangelog.com/).

---

## [2.0.0] — 2026-05-11

**Phase 2 release.** Major schema extension, alignment with external ontologies, SHACL validation layer, and data-acquisition tooling.

### Added

- **Classes (5 new):**
  - `AudiovisualWork` — abstract parent of `Movie`, `TVSeries`, `Episode`.
  - `TVSeries`
  - `Episode`
  - `StreamingPlatform`
  - `Character`
- **Object Properties (6 new):**
  - `hasEpisode` / `episodeOf` (inverse pair)
  - `availableOn` (movie/TV → streaming platform)
  - `basedOn` (adaptation source)
  - `sequelOf` / `prequelOf` (inverse pair)
  - `playsCharacter`
- **Datatype Properties (5 new):**
  - `plotSummary` (xsd:string) — for LLM-driven extraction
  - `imdbId` (xsd:string)
  - `tmdbId` (xsd:string)
  - `wikidataId` (xsd:string)
  - `seasonNumber`, `episodeNumber` (xsd:integer)
- **Individuals (15 new):**
  - Persons: `PeterJackson`, `ElijahWood`, `HowardShore`
  - Movies: `FellowshipOfTheRing`, `ReturnOfTheKing`
  - Streaming Platforms: `Netflix`, `HBOMax`, `DisneyPlus`
  - Production Company: `NewLineCinema`
  - Country: `NewZealand`
  - Genres: `Fantasy`, `Adventure`, `Biography`
  - Franchise: `LordOfTheRingsTrilogy`
  - Award: `OscarBestPicture2004`
- **Competency Questions (6 new):** CQ17–CQ22 covering streaming, sequels, external IDs, and country-based filming queries.
- **Alignment annotations:** every major class/property now carries `rdfs:seeAlso` to schema.org, DBpedia, Wikidata, MO (Bouza 2010) and/or FOAF.
- **Ontology metadata:** `owl:versionInfo`, `owl:versionIRI`, `owl:priorVersion`, `dc:creator`, `dc:date`, `dcterms:license`.
- **SHACL shapes** in `shapes/movie-shapes.ttl` validating Movie / Person / TVSeries / Episode completeness rules.
- **Python scripts:**
  - `scripts/fetch_movies_wikidata.py` — Wikidata SPARQL → OWL fragments.
  - `scripts/populate_with_llm.py` — modular LLM prompting for ontology population (Shimizu et al. 2024).
- **Seed data file:** `data/seed_movies.csv` with 10 candidate Wikidata QIDs.
- **Documentation:**
  - `PHASE2-REPORT.md` — research integration, mandatory paper review, data acquisition section.
  - `ORSD-MovieOntology-v2.docx` — updated specification document.
  - This `CHANGELOG.md`.

### Changed

- `Movie` is now a subclass of the new `AudiovisualWork` class (was directly under `owl:Thing` in v1).
- All existing movie individuals now carry `imdbId` and `wikidataId` for federated linking.
- `Inception` and `TheDarkKnight` now carry an `availableOn` triple.
- README rewritten and re-organised; old README kept in Git history.

### Made disjoint

- `Movie` ⊥ `TVSeries`
- `Movie` ⊥ `Episode`

### Kept (no behavioural change)

- `Actor` ⊥ `Director` (pedagogical disjointness from v1)
- `hasActor` ⇄ `actsIn` (inverse)
- `hasDirector` ⇄ `directs` (inverse)
- `collaboratesWith` (symmetric)
- All v1 IRIs — no breaking renames.

---

## [1.0.0] — 2026-04-28

Initial Phase 1 release.

### Added

- 20 OWL classes (`Movie`, `Person` and their subclasses, `Genre`, `Award` taxonomy, `Country`, `Language`, `Franchise`, `ProductionCompany`).
- 15 object properties including the inverse pairs and the symmetric `collaboratesWith`.
- 9 datatype properties.
- 26 named individuals (4 movies, 9 persons, 5 genres, 2 countries, 1 language, 2 production companies, 1 franchise, 2 awards).
- 16 Competency Questions in `queries/example-queries.sparql`.
- `ORSD-MovieOntology.docx` (NeOn-style specification document).
- README, design-decisions log.
