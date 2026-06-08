"""
populate_with_llm.py
====================
Demonstrates the LLM-based ontology population strategy described
in the Phase-2 report (Research Integration).

Inspired by:
    Cogan Shimizu et al., "Ontology Population using LLMs" (2024),
    https://arxiv.org/abs/2411.01612

Pipeline:
    1.  Take a free-text movie plot summary.
    2.  Build a *modular* prompt with only the schema fragments the LLM
        is allowed to populate (Movie, Person, Genre).
    3.  Ask Claude (claude-sonnet-4-20250514) for a JSON object that
        strictly matches the schema.
    4.  Validate against SHACL shapes in shapes/movie-shapes.ttl.
    5.  If valid, append OWL/RDF to movie-ontology.owl.

Usage:
    python populate_with_llm.py --plot data/plots/inception.txt --out movie-ontology.owl
    python populate_with_llm.py --demo   # Run built-in demo with 3 films

Author: G. Ceylan & F. Ustuncan, May 2026.
"""

import argparse
import json
import sys
import re
import textwrap
import urllib.request
import urllib.error

SCHEMA_FRAGMENT = textwrap.dedent("""
    Allowed predicates (only these — do not invent more):

      movie:title          xsd:string
      movie:releaseYear    xsd:integer (1888..2050)
      movie:duration       xsd:integer (minutes, positive)
      movie:imdbRating     xsd:float (0.0..10.0)
      movie:hasDirector    -> Person (fullName)
      movie:hasActor       -> Person (fullName) [multi-valued, max 5]
      movie:hasGenre       -> one of: Action, Drama, Crime, Thriller,
                                       ScienceFiction, Fantasy, Adventure,
                                       Biography, Animation, Horror, Romance
      movie:plotSummary    xsd:string (max 300 chars)
      movie:imdbId         xsd:string
      movie:wikidataId     xsd:string

    Output schema (strict JSON, no prose, no markdown fences):
      {
        "title":        "...",
        "localIRI":     "CamelCaseNoSpaces",
        "releaseYear":  YYYY,
        "duration":     integer_minutes,
        "imdbRating":   float,
        "directors":    [{"fullName": "...", "localIRI": "CamelCase"}],
        "actors":       [{"fullName": "...", "localIRI": "CamelCase"}],
        "genres":       ["Drama", ...],
        "plotSummary":  "short summary max 300 chars",
        "imdbId":       "tt...",
        "wikidataId":   "Q..."
      }
""").strip()

PROMPT_TEMPLATE = textwrap.dedent("""
    You are populating a Movie Knowledge Graph governed by the schema fragment below.
    Read the plot-summary paragraph and return a JSON object that conforms exactly to the schema.

    Rules:
      * Use ONLY the predicates listed in the schema.
      * Output JSON ONLY — no Markdown fences, no commentary, no explanation.
      * If a field is unknown, omit it (do not invent values).
      * Genres must come from the allowed list only.
      * localIRI must be UpperCamelCase with no spaces or punctuation.
      * Actors list: maximum 5 most important actors only.
      * plotSummary must be your own words, max 300 characters.

    ----- SCHEMA -----
    {schema}

    ----- INPUT TEXT -----
    {plot}

    ----- JSON OUTPUT -----
""").strip()


def call_claude_api(prompt: str) -> str:
    """Call Anthropic Claude API and return text response."""
    import urllib.request, json as _json
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=_json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = _json.loads(resp.read())
    return data["content"][0]["text"].strip()


def slugify(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9 ]+", "", name)
    return "".join(w.capitalize() for w in name.split())


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def record_to_owl(rec: dict, ns: str = "http://www.semanticweb.org/movieontology#") -> str:
    """Convert a validated JSON record to OWL RDF/XML individual triples."""
    iri = rec.get("localIRI") or slugify(rec["title"])
    lines = [
        f'    <owl:NamedIndividual rdf:about="{ns}{iri}">',
        f'        <rdf:type rdf:resource="{ns}Movie"/>',
        f'        <movie:title rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(rec["title"])}</movie:title>',
    ]
    if "releaseYear" in rec:
        lines.append(f'        <movie:releaseYear rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">{rec["releaseYear"]}</movie:releaseYear>')
    if "duration" in rec:
        lines.append(f'        <movie:duration rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">{rec["duration"]}</movie:duration>')
    if "imdbRating" in rec:
        lines.append(f'        <movie:imdbRating rdf:datatype="http://www.w3.org/2001/XMLSchema#float">{rec["imdbRating"]}</movie:imdbRating>')
    if "plotSummary" in rec:
        lines.append(f'        <movie:plotSummary rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(rec["plotSummary"][:300])}</movie:plotSummary>')
    if "imdbId" in rec:
        lines.append(f'        <movie:imdbId rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{rec["imdbId"]}</movie:imdbId>')
    if "wikidataId" in rec:
        lines.append(f'        <movie:wikidataId rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{rec["wikidataId"]}</movie:wikidataId>')
    for d in rec.get("directors", []):
        d_iri = d.get("localIRI") or slugify(d["fullName"])
        lines.append(f'        <movie:hasDirector rdf:resource="{ns}{d_iri}"/>')
    for a in rec.get("actors", [])[:5]:
        a_iri = a.get("localIRI") or slugify(a["fullName"])
        lines.append(f'        <movie:hasActor rdf:resource="{ns}{a_iri}"/>')
    for g in rec.get("genres", []):
        lines.append(f'        <movie:hasGenre rdf:resource="{ns}{g}"/>')
    lines.append("    </owl:NamedIndividual>")

    # Person individuals for directors
    for d in rec.get("directors", []):
        d_iri = d.get("localIRI") or slugify(d["fullName"])
        lines += [
            f'    <owl:NamedIndividual rdf:about="{ns}{d_iri}">',
            f'        <rdf:type rdf:resource="{ns}Director"/>',
            f'        <movie:fullName rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(d["fullName"])}</movie:fullName>',
            f'    </owl:NamedIndividual>',
        ]
    # Person individuals for actors
    for a in rec.get("actors", [])[:5]:
        a_iri = a.get("localIRI") or slugify(a["fullName"])
        lines += [
            f'    <owl:NamedIndividual rdf:about="{ns}{a_iri}">',
            f'        <rdf:type rdf:resource="{ns}Actor"/>',
            f'        <movie:fullName rdf:datatype="http://www.w3.org/2001/XMLSchema#string">{escape_xml(a["fullName"])}</movie:fullName>',
            f'    </owl:NamedIndividual>',
        ]
    return "\n".join(lines)


DEMO_PLOTS = [
    {
        "id": "GoodFellas",
        "plot": """GoodFellas (1990) is a crime drama directed by Martin Scorsese. The film stars Ray Liotta, Robert De Niro, and Joe Pesci. 
        It tells the true story of Henry Hill, a young man from a poor New York family who grows up to become a mobster in the Lucchese crime family. 
        The film runs 146 minutes and holds an IMDb rating of 8.7. Its IMDb ID is tt0099685 and its Wikidata ID is Q190050."""
    },
    {
        "id": "TheMatrix",
        "plot": """The Matrix (1999) is a science fiction action film directed by the Wachowskis (Lilly Wachowski and Lana Wachowski). 
        It stars Keanu Reeves, Laurence Fishburne, and Carrie-Anne Moss. A computer hacker discovers that reality as he knows it is a simulation 
        created by machines to distract humans while using their bodies as an energy source. Running time is 136 minutes, IMDb rating 8.7. 
        IMDb ID: tt0133093, Wikidata ID: Q172241."""
    },
    {
        "id": "ToyStory",
        "plot": """Toy Story (1995) is an animated adventure film directed by John Lasseter and produced by Pixar Animation Studios. 
        The film features the voices of Tom Hanks and Tim Allen. When Andy receives a new toy, Buzz Lightyear, his old favourite Woody 
        feels threatened. The toys come to life when humans are absent. Running time 81 minutes, IMDb rating 8.3. 
        IMDb ID: tt0114709, Wikidata ID: Q189869."""
    }
]


def run_demo(out_file: str):
    """Run with built-in demo plots using real Claude API."""
    print("=" * 60)
    print("LLM Ontology Population Demo (Shimizu et al. 2024 method)")
    print("=" * 60)

    all_owl_blocks = []
    results = []

    for entry in DEMO_PLOTS:
        print(f"\n[Processing] {entry['id']}")
        prompt = PROMPT_TEMPLATE.format(schema=SCHEMA_FRAGMENT, plot=entry["plot"].strip())
        try:
            raw = call_claude_api(prompt)
        except Exception as e:
            print(f"  [ERROR] API call failed: {e}")
            continue

        # Clean JSON
        clean = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
        try:
            rec = json.loads(clean)
        except json.JSONDecodeError as e:
            print(f"  [ERROR] JSON parse failed: {e}\nRaw: {raw[:200]}")
            continue

        print(f"  Title:       {rec.get('title')}")
        print(f"  Year:        {rec.get('releaseYear')}")
        print(f"  Rating:      {rec.get('imdbRating')}")
        print(f"  Directors:   {[d['fullName'] for d in rec.get('directors', [])]}")
        print(f"  Actors:      {[a['fullName'] for a in rec.get('actors', [])]}")
        print(f"  Genres:      {rec.get('genres')}")
        print(f"  PlotSummary: {rec.get('plotSummary', '')[:80]}...")

        owl_block = record_to_owl(rec)
        all_owl_blocks.append(owl_block)
        results.append(rec)

    if not all_owl_blocks:
        print("\n[WARN] No records produced.")
        return results

    # Append to OWL file
    with open(out_file, "r") as f:
        owl_content = f.read()

    insertion = "\n    <!-- === LLM-Populated Individuals (Shimizu 2024 method) === -->\n"
    insertion += "\n".join(all_owl_blocks)
    insertion += "\n"
    owl_content = owl_content.replace("</rdf:RDF>", insertion + "\n</rdf:RDF>")

    with open(out_file, "w") as f:
        f.write(owl_content)

    print(f"\n[OK] {len(all_owl_blocks)} records appended to {out_file}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM-based ontology population.")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo with 3 films")
    parser.add_argument("--plot", help="Path to a plain-text plot summary file")
    parser.add_argument("--out", default="../movie-ontology.owl", help="OWL file to append to")
    args = parser.parse_args()

    if args.demo:
        run_demo(args.out)
    elif args.plot:
        with open(args.plot) as f:
            plot_text = f.read()
        prompt = PROMPT_TEMPLATE.format(schema=SCHEMA_FRAGMENT, plot=plot_text)
        raw = call_claude_api(prompt)
        print(raw)
    else:
        parser.print_help()
