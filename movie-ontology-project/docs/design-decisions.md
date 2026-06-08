# Design Decisions Log

A running log of the modelling choices made during ontology development.
Each entry: **Decision · Rationale · Alternatives considered**.

---

## 1. Person modelling: superclass + role-based subclasses

**Decision.** `Person` is a superclass; `Actor`, `Director`, `Producer`,
`Writer`, `Composer` are subclasses. An individual may belong to **more than
one** of these subclasses simultaneously (e.g. Christopher Nolan is both a
`Director` and a `Writer`).

**Rationale.** Real-world filmmaking professionals very often play multiple
roles; multiple typing in OWL handles this naturally without role-explosion.

**Alternatives considered.** A single `Person` class with a `hasRole` object
property pointing to a `Role` enumeration. Rejected because it pushes role
information into a separate hop and complicates SPARQL queries.

---

## 2. `Actor` declared `owl:disjointWith` `Director`

**Decision.** Pedagogically useful disjointness for demonstrating reasoner
behaviour; slightly unrealistic in practice (some persons direct films they
star in).

**Rationale.** Provides an opportunity to showcase consistency checking with
HermiT. If we later need to model director-actors (e.g. Clint Eastwood) we
will remove this disjointness and replace with a more nuanced model.

---

## 3. `collaboratesWith` as `owl:SymmetricProperty`

**Decision.** Declaring this property symmetric lets the reasoner materialise
the inverse direction automatically.

**Rationale.** Reduces manual triple authoring and demonstrates inferred
knowledge — a key value-add of OWL over plain RDF.

---

## 4. `hasActor` ⇄ `actsIn` declared `owl:inverseOf`

**Decision.** Both directions of the actor-movie relationship are modelled as
inverse properties.

**Rationale.** Allows competency questions to be phrased from either side
("Which actors are in this film?" vs. "Which films does this actor appear
in?") without duplicating data.

---

## 5. Datatype choices

| Property | Datatype | Reasoning |
|---|---|---|
| `releaseYear`, `duration`, `awardYear` | `xsd:integer` | Whole-number quantities |
| `imdbRating` | `xsd:float` | Fractional, range 0.0–10.0 |
| `budget`, `boxOffice` | `xsd:long` | Values can exceed 2³¹ |
| `birthDate` | `xsd:date` | ISO 8601 calendar date |
| `title`, `fullName` | `xsd:string` | Free text |

---

## 6. Naming convention

- **Classes**: `UpperCamelCase` (`Movie`, `AcademyAward`).
- **Properties**: `lowerCamelCase` verb phrases (`hasDirector`, `releaseYear`).
- **Individuals**: `UpperCamelCase` reflecting a real-world identifier
  (`ChristopherNolan`, `TheDarkKnight`). Spaces and punctuation are removed.

---

## 7. Namespace

A single namespace `http://www.semanticweb.org/movieontology#` is used. This
is the Protégé default-style IRI; it will be replaced with a stable
project-owned domain before any public release.

---

## 8. Future extensions (not yet implemented)

- Add `TVSeries`, `Episode`, `StreamingPlatform` subclasses.
- Align with **schema.org `Movie`** and **DBpedia ontology** for
  interoperability.
- Define **SHACL shapes** to validate that every `Movie` has at least one
  `hasDirector` and one `hasGenre` triple.
- Expose the ontology and data via an Apache Jena Fuseki SPARQL endpoint.
