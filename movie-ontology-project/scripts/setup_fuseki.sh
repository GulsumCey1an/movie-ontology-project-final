#!/usr/bin/env bash
# setup_fuseki.sh — Download Apache Jena Fuseki and load the Movie KG
# Tested on: Ubuntu 22+, macOS 13+, Windows WSL2
# Requirements: Java 11+

set -e

FUSEKI_VERSION="5.2.0"
FUSEKI_URL="https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-${FUSEKI_VERSION}.tar.gz"
FUSEKI_DIR="apache-jena-fuseki-${FUSEKI_VERSION}"

echo "=== Movie Knowledge Graph — Fuseki Setup ==="
echo "Fuseki version: $FUSEKI_VERSION"
echo ""

# Check Java
if ! command -v java &>/dev/null; then
    echo "ERROR: Java not found. Install Java 11+ first."
    exit 1
fi
echo "Java OK: $(java -version 2>&1 | head -1)"

# Download Fuseki
if [ ! -d "$FUSEKI_DIR" ]; then
    echo "Downloading Apache Jena Fuseki $FUSEKI_VERSION..."
    curl -L "$FUSEKI_URL" -o fuseki.tar.gz
    tar -xzf fuseki.tar.gz
    rm fuseki.tar.gz
    echo "Downloaded."
fi

# Start Fuseki with in-memory dataset and load our ontology
echo ""
echo "Starting Fuseki server on http://localhost:3030/"
echo "Dataset name: /movies"
echo "SPARQL endpoint: http://localhost:3030/movies/sparql"
echo ""
echo "Loading movie-ontology.ttl..."

cd "$FUSEKI_DIR"

# Create dataset config
cat > movie-dataset.ttl << CONFIG
@prefix fuseki: <http://jena.apache.org/fuseki#> .
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ja:     <http://jena.hpl.hp.com/2005/11/Assembler#> .

<#service> rdf:type fuseki:Service ;
    fuseki:name "movies" ;
    fuseki:endpoint [ fuseki:operation fuseki:query ; fuseki:name "sparql" ] ;
    fuseki:endpoint [ fuseki:operation fuseki:update ; fuseki:name "update" ] ;
    fuseki:endpoint [ fuseki:operation fuseki:gsp-r ; fuseki:name "get" ] ;
    fuseki:dataset <#dataset> .

<#dataset> rdf:type ja:RDFDataset ;
    ja:defaultGraph <#model> .

<#model> rdf:type ja:FileModel ;
    ja:location "../movie-ontology.ttl" .
CONFIG

echo "Starting Fuseki... (Press Ctrl+C to stop)"
./fuseki-server --conf=movie-dataset.ttl --port=3030
