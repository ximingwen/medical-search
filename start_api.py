# This is the RESTful API module

from flask import Flask, jsonify, request
from flask_restful import reqparse, abort, Resource, Api
from flask_cors import CORS
import json
import globalvar as gl

from query_builder import solr_query_builder
from document_searcher import solr_document_searcher
from text_parser import search_result_parser
from text_parser import concept2dic
from carrot_clustering import search_result_clustering
from cluster_concept import *

app = Flask(__name__)
api = Api(app)
CORS(app)


def is_valid_request(json_data):
    if 'event' not in json_data:
        return False, '"event" key is not in request json.'
    for concept in json_data['event']:
        if 'name' not in concept:
            return False, '"name" key is not in concept {}'.format(concept)
        if 'importance' not in concept:
            return False, '"importance" key is not in {}'.format(concept)
        try:
            float(concept['importance'])
        except:
            return False, '"importance" value is not a valid number: "{}" in {}'.format(concept['importance'], concept)
    return True, ''

def is_valid_request2(json_data):
    if 'event' not in json_data:
        return False, '"event" key is not in request json.'
    for concept in json_data['event']:
        if 'name' not in concept:
            return False, '"name" key is not in concept {}'.format(concept)
        if 'importance' not in concept:
            return False, '"importance" key is not in {}'.format(concept)
        try:
            float(concept['importance'])
        except:
            return False, '"importance" value is not a valid number: "{}" in {}'.format(concept['importance'], concept)
    return True, ''

class SearchAPI(Resource):
    def post(self):
        
        json_data = request.get_json(force=True)
        # print(json_data)
        is_valid, error_msg = is_valid_request(json_data)
        if is_valid:
            # step 1: build search string
            query_string, key_terms = solr_query_builder(json_data)

            # step 2: search solr index
            solr_results = solr_document_searcher(query_string, False)
        
            #step 3: parse search results
            top_k_docs = 100
            top_k_cons = 10
            cluster_field = ['title', 'abstract']
            concepts_original = search_result_parser(solr_results, True, top_k_docs)
        
            clustering_alg = json_data['clustering_algorithm']
            num_clusters = json_data['num_clusters']
            
            clusters = search_result_clustering(solr_results, False, top_k_docs, cluster_field, clustering_alg, num_clusters)
            # json2 = {}
            # concepts_original_dict = concept2dic(concepts_original, json2)
            # clusters = process_cluster_concept2(concepts_original_dict, clusters, 5)
            clusters = process_cluster_concept(solr_results, clusters, 5, concepts_original)
            
            all_concepts = dict(sorted(concepts_original.items(), key = lambda x: len(x[1].pmids), reverse = True))
            frequent_concepts={}
            terms=[]
            for cui,concept in all_concepts.items():
                term=list(concept.mentions)[0]
                if term not in terms:
                    terms.append(term)
                    frequent_concepts[cui]=concept
                if len(terms)==top_k_cons:
                    break
            json={}
            concepts=concept2dic(frequent_concepts,json)
            
            content={'solr_results':solr_results,
                    'concepts':concepts,
                    'clusters': clusters} 
            response=jsonify(content)
            response.headers.add("Access-Control-Allow-Origin", "*")
            print(response)
            return response

        else:
            response = {"message": "Wrong JSON format: " + error_msg}
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response

class ConceptAPI(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        # json data should include solr_results, clusters, selected_clusters
        # is_valid, error_msg = is_valid_request2(json_data)
        is_valid = True
        if is_valid:
            top_k_docs = 100
            solr_results = json_data['solr_results']
            clusters = json_data['clusters']
            selected_clusters = json_data['selected_clusters'] # a list of selected cluster ids
            concepts_original = search_result_parser(solr_results, True, top_k_docs)
            intersect_cluster = process_cluster_concept_one(solr_results, clusters, 5, concepts_original, selected_clusters)
            content = {'intersect_cluster': intersect_cluster}
            response=jsonify(content)
            response.headers.add("Access-Control-Allow-Origin", "*")
            print(response)
            return response
        else:
            response = {"message": "Wrong JSON format: " + error_msg}
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response

'''
    info_focus_dict = {"event":[      
                          { 
                             "name":"ICD10 F17",
                             "importance":"10"
                          },
                          {
                             "name":"ICD10 G89",
                             "importance":"7"
                          }
                       ]}
'''
     
api.add_resource(SearchAPI, '/search/query')
api.add_resource(ConceptAPI, '/search/cluster_score')
     
if __name__ == '__main__':
    app.run(host="0.0.0.0",debug = True, port = 8983)

