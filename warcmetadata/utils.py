from rdflib import Graph


def guess_seed_request(graph: Graph):
    """Query a graph of a crawl and guess the record of the request for the seed url."""

    result = graph.query("""
    prefix dowarc: <https://github.com/DOWARC/dowarc#>
    select ?record ?seedUrl {
        ?record dowarc:WARC-Date ?date ;
                dowarc:WARC-Target-URI ?seedUrl ;
                dowarc:WARC-Type "request" .
    } order by ?date limit 1
    """)

    return result.bindings[0]

def get_seed_record(graph: Graph, **kwargs):
    """Query a graph to get the resources of a request and response.

    kwargs needs to be a dict of rdflib Variables and Terms.
    """

    query_bindings_str = ""
    for variable, value in kwargs.items():
        query_bindings_str += f"\nbind({value.n3()} as {variable.n3()})"

    graph_result = graph.query("""
    prefix dowarc: <https://github.com/DOWARC/dowarc#>
    construct {
        ?warcfile dct:relation ?request, ?response .
        ?request dowarc:WARC-Date ?date ;
                dowarc:WARC-Target-URI ?seedUrl ;
                dowarc:WARC-Concurrent-To ?response ;
                ?req_p ?req_o .
        ?response ?res_p ?res_o .
    } where {
        """ + query_bindings_str + """
        ?warcfile dct:relation ?request .
        ?request dowarc:WARC-Date ?date ;
                dowarc:WARC-Target-URI ?seedUrl ;
                ?req_p ?req_o .
        optional {
            ?request dowarc:WARC-Concurrent-To ?response .
            ?response ?res_p ?res_o .
            optional {
                ?warcfile dct:relation ?response .
            }
        }
    }
    """)

    return graph_result.graph