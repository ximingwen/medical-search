# This module takes the query string from query_builder, include it into
# one or multiple URLs, and submit the search request to Solr

import requests
import json
import unicodedata
import globalvar as gl

SOLR_URL_PREFIX_LOCAL = 'http://localhost:12345/solr/MEDLINEv6/select'
SOLR_URL_PREFIX_SERVER = 'http://10.4.80.108:8984/solr/MEDLINEv6/clustering'

# this is a simple searcher just only returns the first 100 results
def solr_document_searcher(query_string, local, num_docs):
    if local:
        SOLR_URL_PREFIX = SOLR_URL_PREFIX_LOCAL
    else:
        SOLR_URL_PREFIX = SOLR_URL_PREFIX_SERVER
    #clustering.engine=kmeans
    #'LingoClusteringAlgorithm.desiredClusterCountBase': '10'
    payload = {'q': query_string, 'start': '0', 'rows': num_docs,"facet.field":"snomed_codes","facet":"off"}
    # payload = {'q': query_string, 'start': '0', 'rows': '100',"facet.field":"snomed_codes","facet":"on", 
    #             'LingoClusteringAlgorithm.desiredClusterCountBase': 10, "carrot.snippet": "abstract", "carrot.title": "title"}
    r = requests.get(SOLR_URL_PREFIX, params=payload)
    print(payload)

    search_result = r.json()
    '''
    assert 'response' in search_result, \
        'search_result_parser: no "response" key in search_result object'
    '''
    if 'response' not in search_result:
        print(search_result)
        with open('./log.json', 'w') as f:
            json.dump(search_result, f)
    else:
    # preprocess certain non-ascii strings
        with open('./log.json', 'w') as f:
            json.dump(search_result, f)
        response = search_result['response']
        for i in range(len(response['docs'])):
            abstract = response['docs'][i]['abstract'][0]
            response['docs'][i]['abstract'][0] = unicodedata.normalize("NFD", abstract)

            title = response['docs'][i]['title'][0]
            response['docs'][i]['title'][0] = unicodedata.normalize("NFD", title)

        gl._init(response,'search_result')  
    return search_result


# Unit test
if __name__ == '__main__':
    query_string = 'abstract:headache OR title:headache'

    results = solr_document_searcher(query_string, False)
    clusters = results['clusters']
    for c in clusters:
        print(c['labels'], len(c['docs']))
    # print (json.dumps(results))