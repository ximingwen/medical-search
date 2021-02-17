# This module takes the query string from query_builder, include it into
# one or multiple URLs, and submit the search request to Solr

import requests
import json
import unicodedata
import globalvar as gl

SOLR_URL_PREFIX_LOCAL = 'http://localhost:12345/solr/MEDLINEv6/select'
SOLR_URL_PREFIX_SERVER = 'http://10.4.80.108:8984/solr/MEDLINEv6/select'

# this is a simple searcher just only returns the first 100 results
def solr_document_searcher(query_string, local):
    if local:
        SOLR_URL_PREFIX = SOLR_URL_PREFIX_LOCAL
    else:
        SOLR_URL_PREFIX = SOLR_URL_PREFIX_SERVER

    payload = {'q': query_string, 'start': '0', 'rows': '100',"facet.field":"snomed_codes","facet":"on"}
    r = requests.get(SOLR_URL_PREFIX, params=payload)
    # print(r.url)

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
    query_string = 'abstract:nicotine^1.0 OR title:nicotine^1.0 OR abstract:tobacco^1.0 OR title:tobacco^1.0 OR abstract:pain^1.0 OR title:pain^1.0 OR abstract:opioid^5.0 OR title:opioid^5.0'

    results = solr_document_searcher(query_string, False)
    print (json.dumps(results))