import importlib.resources
from urllib.parse import urlparse

from loguru import logger
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD
from rdflib.util import from_n3
from warcio.archiveiterator import ArchiveIterator

# Define namespaces
DOWARC = Namespace("https://github.com/DOWARC/dowarc#")
ORE = Namespace("http://www.openarchives.org/ore/terms/")

def load_dowarc_mapping():
    """
    Load RDF vocabulary and map WARC header labels to ontology URIs.
    """
    mapping = {}
    with importlib.resources.path(__name__, "../vocab/dowarc.owl") as data_path:
        g = Graph().parse(data_path)

        for s, p, o in g.triples((None, RDFS.label, None)):
            if isinstance(o, str) and "WARC-" in o:
                mapping[o.strip()] = s
    return mapping


def safe_uri_or_bnode(value: str):
    """
    Return URIRef if value is serializable, else fall back to BNode.
    Prevents rdflib crashes on invalid or unsafe URIs.
    """
    try:
        return from_n3(value)
    except:
        try:
            logger.debug(value)
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.path:
                raise ValueError("Invalid URI format")

            uri = URIRef(value)
            _ = uri.n3()  # Check if rdflib can serialize it
            logger.debug(uri)
            return uri
        except:
            # Optional: click.echo(f"?? Unsafe URI: {value} ? using BNode", err=True)
            logger.debug("BNode")
            return BNode()

def extract_metadata_complex(warc_file_stream, warc_path, warc_file_iri):
    """
    Extraction of the original ORE based datamodel
    """

    graph = Graph()
    graph.bind("dowarc", DOWARC)
    graph.bind("ore", ORE)

    mapping = load_dowarc_mapping()

    warc_file_iri = URIRef(f"https://example.org/{warc_path.name}")
    graph.add((warc_file_iri, RDF.type, DOWARC.WARCfile))

    for record in ArchiveIterator(warc_file_stream):
        record_id = record.rec_headers.get("WARC-Record-ID")
        if not record_id:
            continue

        record_uri = safe_uri_or_bnode(record_id)
        graph.add((warc_file_iri, ORE.aggregates, record_uri))
        graph.add((record_uri, ORE.isAggregatedBy, warc_file_iri))
        graph.add((record_uri, RDF.type, DOWARC.WARCrecord))

        for key, value in record.rec_headers.headers:
            if key in mapping:
                prop_uri = mapping[key]
                val_node = safe_uri_or_bnode(value)
                label_str = f"{record_id}_{key}"

                graph.add((val_node, RDF.type, prop_uri))
                graph.add((val_node, RDFS.label, Literal(label_str, lang="en")))

                # Type inference
                if "Date" in key:
                    lit = Literal(value, datatype=XSD.dateTime)
                elif "Length" in key:
                    lit = Literal(value, datatype=XSD.integer)
                else:
                    lit = Literal(value)

                graph.add((val_node, RDF.value, lit))
                graph.add((record_uri, ORE.aggregates, val_node))

    return graph


def extract_metadata_simple(warc_file_stream, warc_path, warc_file_iri):
    """
    Extraction of a simplified warc data model
    """
    graph = Graph()
    graph.bind("dowarc", DOWARC)
    graph.bind("dct", DCTERMS)

    mapping = load_dowarc_mapping()

    graph.add((warc_file_iri, RDF.type, DOWARC.WARCfile))

    for record in ArchiveIterator(warc_file_stream):
        record_id = record.rec_headers.get("WARC-Record-ID")
        if not record_id:
            continue

        record_uri = safe_uri_or_bnode(record_id)
        graph.add((warc_file_iri, DCTERMS.relation, record_uri))
        graph.add((record_uri, RDF.type, DOWARC.WARCrecord))

        for key, value in record.rec_headers.headers:
            if key in mapping:
                prop_uri = mapping[key]

                # Type inference
                if "Date" in key:
                    lit = Literal(value, datatype=XSD.dateTime)
                elif "Length" in key:
                    lit = Literal(value, datatype=XSD.integer)
                elif "IP-Address" in key:
                    lit = Literal(value)
                elif "Target-URI" in key:
                    lit = URIRef(value)
                else:
                    logger.debug(value)
                    try:
                        lit = from_n3(value)
                    except Exception:
                        lit = Literal(value)

                graph.add((record_uri, prop_uri, lit))

    return graph
