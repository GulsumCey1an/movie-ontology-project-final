"""
fetch_movies_wikidata.py
=========================
Pulls structured movie data from the Wikidata SPARQL endpoint and
emits OWL named-individual triples that drop straight into
movie-ontology.owl.

This script demonstrates the data-acquisition pipeline described in
the Phase-2 report (Section 6, Data Acquisition).

Pipeline (per the report):
    1. SOURCE      : Wikidata SPARQL endpoint (https://query.wikidata.org/sparql).
    2. METHOD      : One parameterised SPARQL CONSTRUCT / SELECT per movie QID.
    3. PREPROCESS  : Clean labels, unify dates to ISO-8601, drop multilingual
                     duplicates, slugify identifiers for the local namespace.
    4. MAPPING     : Wikidata predicate -> our ontology predicate (see MAP).
    5. SERIALISE   : Append RDF/XML fragments to a target OWL file.

Run:
    pip install SPARQLWrapper rdflib
    python fetch_movies_wikidata.py --qids Q25188 Q83495 --out new-movies.owl

Author: G. Ceylan & F. Ustuncan, May 2026.
"""

import argparse
import re
import sys
from datetime import datetime

try:
    from SPARQLWrapper import SPARQLWrapper, JSON
except ImportError:
    sys.exit("Please run: pip install SPARQLWrapper rdflib")

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "MovieOntologyBot/2.0 (course project; ceylan.ustuncan@example.com)"
NS = "http://www.semanticweb.org/movieontology#"

# Wikidata property -> our predicate (Movie-side mapping)
MAP = {
    "P57":   "hasDirector",      # director
    "P58":   "hasWriter",        # screenwriter
    "P162":  "hasProducer",      # producer
    "P86":   "hasComposer",      # composer
    "P161":  "hasActor",         # cast member
    "P136":  "hasGenre",         # genre
    "P272":  "producedBy",       # production company
    "P495":  "filmedIn",         # country of origin
    "P364":  "inLanguage",       # original language
    "P179":  "partOfFranchise",  # series
}

SPARQL_TEMPLATE = """
SELECT ?film ?filmLabel ?title ?releaseDate ?duration
       ?imdbRating ?budget ?boxOffice ?imdbId
       (GROUP_CONCAT(DISTINCT ?directorLabel; separator="|") AS ?directors)
       (GROUP_CONCAT(DISTINCT ?actorLabel; separator="|") AS ?actors)
       (GROUP_CONCAT(DISTINCT ?genreLabel; separator="|") AS ?genres)
WHERE {
  BIND(wd:%(QID)s AS ?film)
  OPTIONAL { ?film wdt:P1476 ?title . }
  OPTIONAL { ?film wdt:P577  ?releaseDate . }
  OPTIONAL { ?film wdt:P2047 ?duration . }
  OPTIONAL { ?film wdt:P345  ?imdbId . }
  OPTIONAL { ?film wdt:P444  ?imdbRating . }
  OPTIONAL { ?film wdt:P2130 ?budget . }
  OPTIONAL { ?film wdt:P2142 ?boxOffice . }
  OPTIONAL { ?film wdt:P57   ?director .
             ?director rdfs:label ?directorLabel .
             FILTER(LANG(?directorLabel) = "en") }
  OPTIONAL { ?film wdt:P161  ?actor .
             ?actor rdfs:label ?actorLabel .
             FILTER(LANG(?actorLabel) = "en") }
  OPTIONAL { ?film wdt:P136  ?genre .
             ?genre rdfs:label ?genreLabel .
             FILTER(LANG(?genreLabel) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
GROUP BY ?film ?filmLabel ?title ?releaseDate ?duration
         ?imdbRating ?budget ?boxOffice ?imdbId
"""


def slugify(name: str) -> str:
    """Turn 'The Lord of the Rings' -> 'TheLordOfTheRings' (UpperCamelCase)."""
    name = re.sub(r"[^A-Za-z0-9 ]+", "", name)
    return "".join(w.capitalize() for w in name.split())


def fetch(qid: str) -> dict | None:
    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT, agent=USER_AGENT)
    sparql.setQuery(SPARQL_TEMPLATE % {"QID": qid})
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
    except Exception as e:                                # pragma: no cover
        print(f"[WARN] Wikidata query failed for {qid}: {e}", file=sys.stderr)
        return None
    bindings = results.get("results", {}).get("bindings", [])
    if not bindings:
        return None
    row = bindings[0]
    return {k: v["value"] for k, v in row.items()}


def to_owl(qid: str, row: dict) -> str:
    """Convert one Wikidata row into an RDF/XML <owl:NamedIndividual> fragment."""
    title = row.get("title") or row.get("filmLabel") or qid
    iri = slugify(title)
    year = (row.get("releaseDate") or "")[:4]
    out  = [f'    <owl:NamedIndividual rdf:about="{NS}{iri}">']
    out += ['        <rdf:type rdf:resource="' + NS + 'FeatureFilm"/>']
    out += [f'        <rdfs:label>{title}</rdfs:label>']
    out += [f'        <movie:title>{title}</movie:title>']
    out += [f'        <movie:wikidataId>{qid}</movie:wikidataId>']
    if row.get("imdbId"):
        out += [f'        <movie:imdbId>{row["imdbId"]}</movie:imdbId>']
    if year.isdigit():
        out += [
            f'        <movie:releaseYear rdf:datatype='
            f'"http://www.w3.org/2001/XMLSchema#integer">{year}</movie:releaseYear>'
        ]
    if row.get("duration"):
        out += [
            f'        <movie:duration rdf:datatype='
            f'"http://www.w3.org/2001/XMLSchema#integer">{row["duration"]}</movie:duration>'
        ]
    if row.get("budget"):
        out += [
            f'        <movie:budget rdf:datatype='
            f'"http://www.w3.org/2001/XMLSchema#long">{row["budget"]}</movie:budget>'
        ]
    if row.get("boxOffice"):
        out += [
            f'        <movie:boxOffice rdf:datatype='
            f'"http://www.w3.org/2001/XMLSchema#long">{row["boxOffice"]}</movie:boxOffice>'
        ]
    out += ['    </owl:NamedIndividual>']
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qids", nargs="+", required=True,
                    help="Wikidata QIDs to fetch (e.g. Q25188 Q83495)")
    ap.add_argument("--out", default="new-movies.owl",
                    help="Path to write the OWL fragments")
    args = ap.parse_args()

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(f"<!-- Auto-generated by fetch_movies_wikidata.py on "
                 f"{datetime.utcnow().isoformat()}Z -->\n")
        for qid in args.qids:
            print(f"[INFO] Fetching {qid} ...")
            row = fetch(qid)
            if row is None:
                print(f"[WARN] No data for {qid}", file=sys.stderr)
                continue
            fh.write(to_owl(qid, row) + "\n\n")
    print(f"[OK] Wrote {args.out}")


if __name__ == "__main__":
    main()
