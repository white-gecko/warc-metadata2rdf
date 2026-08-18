from pathlib import Path

import click
from rdflib import Namespace, URIRef

from .extraction import extract_metadata_complex, extract_metadata_simple

# Define namespaces
DOWARC = Namespace("https://github.com/DOWARC/dowarc#")
ORE = Namespace("http://www.openarchives.org/ore/terms/")

DOWARC_PROFILES = {
    "complex": extract_metadata_complex,
    "simple": extract_metadata_simple,
}



@click.command(
    help="Extract metadata from a WARC file and serialize it using the DOWARC vocabulary."
)
@click.option(
    "--input",
    "-i",
    "warc_path_str",
    required=True,
    type=click.Path(exists=True),
    help="Path to the input WARC (.warc or .warc.gz) file.",
)
@click.option(
    "--iri",
    "warc_file_iri_str",
    required=False,
    help="IRI for the WARC file to use in the generated graph.",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    required=True,
    type=click.Path(),
    help="Path to the output RDF file.",
)
@click.option(
    "--format",
    "-f",
    "rdf_format",
    default="turtle",
    show_default=True,
    type=click.Choice(["xml", "turtle", "nt", "n3"], case_sensitive=False),
    help="Optional RDF serialization format.",
)
@click.option(
    "--profile",
    "-p",
    default="complex",
    show_default=True,
    type=click.Choice(DOWARC_PROFILES.keys(), case_sensitive=False),
    help="Optional selection of the DOWARC profile (experimental).",
)
def extract_metadata(warc_path_str, output_path, rdf_format, profile, warc_file_iri_str):
    """
    Main CLI entrypoint: reads WARC file, extracts metadata, builds RDF, serializes graph.
    """

    warc_path = Path(warc_path_str)

    warc_file_iri = URIRef(warc_file_iri_str or f"https://example.org/{warc_path.name}")
    with open(warc_path, "rb") as stream:
        graph = DOWARC_PROFILES[profile](stream, warc_file_iri)

    graph.serialize(destination=output_path, format=rdf_format)
    click.echo(f"Metadata exported to: {output_path} (Format: {rdf_format})")


if __name__ == "__main__":
    extract_metadata()
