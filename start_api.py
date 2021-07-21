# This is the RESTful API module

from flask import Flask, jsonify, request, session
from flask_restful import reqparse, abort, Resource, Api
from flask_cors import CORS, cross_origin
from flask_session import Session
import json
import time
import globalvar as gl

from query_builder import solr_query_builder
from document_searcher import solr_document_searcher
from text_parser import search_result_parser
from text_parser import concept2dic
from carrot_clustering import search_result_clustering
from cluster_concept import *
from cluster_reorder import reorder_cluster
from topic_2d import proj_cluster
from highlight_labels import process_highlight
from concept_cluster import concept_clustering, edit_cluster
from phrase_parser import search_phrase_parser
from concept_summary import extract_sent_candids, generate_summary

app = Flask(__name__)
# SESSION_TYPE = 'filesystem'
# app.config.from_object(__name__)
app.secret_key = b'Z\x17s\xcf!!\xcd\x84\x07\x1e2(\x8fk\x1dX\x8f\x1a\x96\x99\x87zO\x98'
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)
# api = Api(app)
CORS(app)


def is_valid_request(json_data):
    if json_data['advanced']:
        return True, ""
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

# class SearchAPI(Resource):
@app.route('/search/query', methods=['POST'])
@cross_origin(supports_credentials=True)
def SearchAPI():
    
    json_data = request.get_json(force=True)
    # print(json_data)
    is_valid, error_msg = is_valid_request(json_data)
    if is_valid:
        if json_data['advanced']:
            query_string = json_data['advanced_query']
            free_text = json_data['free_text_query']
        else:
        # step 1: build search string
            query_string, free_text = solr_query_builder(json_data)
        # step 2: search solr index
        print(json_data['num_docs'])
        t1 = time.time()
        # TODO
        solr_results = solr_document_searcher(query_string, False, json_data['num_docs'])
        t2 = time.time()
        print(f"time to retreive: {t2 - t1}")
        #step 3: parse search results
        top_k_docs = min(int(json_data['num_docs']), len(solr_results['response']['docs']))
        # print(top_k_docs)
        top_k_cons = 10
        cluster_field = ['title', 'abstract']
        concepts_original = search_result_parser(solr_results, True, top_k_docs)
        phrases = search_phrase_parser(solr_results, True, top_k_docs)
        t3 = time.time()
        print(f"time to parse concepts: {t3 - t2}")
        clustering_alg = json_data['clustering_algorithm']
        num_clusters = int(json_data['num_clusters'])
        if json_data['snomed']==0:
            clusters = concept_clustering(concepts_original, num_clusters, top_k_docs)
        elif json_data['snomed']==1:
            clusters = concept_clustering(phrases, num_clusters, top_k_docs)
        else:
            clusters = search_result_clustering(solr_results, False, top_k_docs, cluster_field, clustering_alg, num_clusters)
        t4 = time.time()
        print(f"time to clustering: {t4 - t3}")
        print(len(clusters))
        for cluster in clusters:
            summary = generate_summary(free_text, cluster['documents'], cluster['cid'], solr_results['response']['docs'], 3, snomed=(json_data['snomed']==0))
            cluster['summary'] = summary

        t5 = time.time()
        print(f"time to generate summary: {t5 - t4}")
        reorder_index, idx_to_groups, d3_json = reorder_cluster(clusters)
        # proj_cluster(clusters, idx_to_cluster1)
        cluster_idx = [int(idx) for idx in reorder_index]
        # idx_to_cluster1 = [int(idx) for idx in idx_to_cluster1]
        # idx_to_cluster2 = [int(idx) for idx in idx_to_cluster2]
        # json2 = {}
        # concepts_original_dict = concept2dic(concepts_original, json2)
        # clusters = process_cluster_concept2(concepts_original_dict, clusters, 5)
        session['concepts_original'] = concepts_original
        clusters = process_cluster_concept(solr_results, clusters, 5, concepts_original)
        t6 = time.time()
        print(f"time to collect cluster info: {t6 - t5}")
        print(f"total: {t6 - t1}")
        # all_concepts = dict(sorted(concepts_original.items(), key = lambda x: len(x[1].pmids), reverse = True))
        # frequent_concepts={}
        # terms=[]
        # for cui,concept in all_concepts.items():
        #     term=list(concept.mentions)[0]
        #     if term not in terms:
        #         terms.append(term)
        #         frequent_concepts[cui]=concept
        #     if len(terms)==top_k_cons:
        #         break
        # json={}
        # concepts=concept2dic(frequent_concepts,json)
        
        content={'solr_results':solr_results,
                'clusters': clusters,
                "cluster_order": cluster_idx,
                "idx_to_groups": idx_to_groups, # put clusters into groups, determine its color
                "d3_json": d3_json}
        session['solr_results'] = solr_results
        print(len(session['solr_results']['response']['docs']))
        session['clusters'] = clusters
        print(len(session['clusters']))
        session['cluster_order'] = cluster_idx
        session['idx_to_groups'] = idx_to_groups
        session['d3_json'] = d3_json
        session['must_exclude'] = []
        session['top_k_docs'] = top_k_docs
        session['free_text'] = free_text
        response=jsonify(content)
        # response.headers.add("Access-Control-Allow-Origin", "*")
        print(response.headers)
        return response

    else:
        response = {"message": "Wrong JSON format: " + error_msg}
        # response.headers.add("Access-Control-Allow-Origin", "*")
        return response

# class EditClusterAPI(Resource):
@app.route('/search/edit_cluster', methods=['POST'])
@cross_origin(supports_credentials=True)
def EditClusterAPI():
    json_data = request.get_json(force=True)
    is_valid = True
    if is_valid:
        concepts_original = session['concepts_original']
        current_clusters = session['clusters']
        solr_results = session['solr_results']
        top_k_docs = session['top_k_docs']
        print(len(solr_results['response']['docs']))
        new_clusters = []
        if json_data['action']=='delete':
            session['must_exclude'].append(json_data['cid'])
            new_clusters = edit_cluster(current_clusters, concepts_original, session['must_exclude'], top_k_docs)
            cluster = new_clusters[-1]
            summary = generate_summary(session['free_text'], cluster['documents'], cluster['cid'], solr_results['response']['docs'], 3, snomed=True)
            cluster['summary'] = summary
            new_clusters[-1] = cluster
            print(cluster)
        else:
            # case when the concept already exists
            for cid in json_data['cid']:
                c_object = concepts_original[cid]
                labels = []
                lower_labels = []
                for label in list(c_object.mentions):
                    if label.lower() not in lower_labels:
                        labels.append(label)
                        lower_labels.append(label.lower())
                summary = generate_summary(session['free_text'], list(c_object.docids), cid, solr_results['response']['docs'], 3, snomed=True)
                c_dict = {
                    "labels": labels,
                    "documents": list(c_object.docids),
                    "cid": cid,
                    "summary": summary
                }
                current_clusters.append(c_dict)
            new_clusters = current_clusters
        reorder_index, idx_to_groups, d3_json = reorder_cluster(new_clusters)
        cluster_idx = [int(idx) for idx in reorder_index]
        clusters = process_cluster_concept(solr_results, new_clusters, 5, concepts_original)
        content={
                'clusters': clusters,
                "cluster_order": cluster_idx,
                "idx_to_groups": idx_to_groups, # put clusters into groups, determine its color
                "d3_json": d3_json}
        session['clusters'] = clusters
        session['cluster_order'] = cluster_idx
        session['idx_to_groups'] = idx_to_groups
        session['d3_json'] = d3_json
        response = jsonify(content)
        # response.headers.add("Access-Control-Allow-Origin", "*")
        return response

# class ConceptAPI(Resource):
@app.route('/search/cluster_score', methods=['POST'])
@cross_origin(supports_credentials=True)
def ConceptAPI():
    json_data = request.get_json(force=True)
    # json data should include solr_results, clusters, selected_clusters
    # is_valid, error_msg = is_valid_request2(json_data)
    is_valid = True
    if is_valid:
        top_k_docs = int(json_data['num_docs'])
        solr_results = json_data['solr_results']
        clusters = json_data['clusters']
        selected_clusters = json_data['selected_clusters'] # a list of selected cluster ids
        concepts_original = search_result_parser(solr_results, True, top_k_docs)
        intersect_cluster = process_cluster_concept_one(solr_results, clusters, 5, concepts_original, selected_clusters)
        content = {'intersect_cluster': intersect_cluster}
        response=jsonify(content)
        # response.headers.add("Access-Control-Allow-Origin", "*")
        print(response)
        return response
    else:
        response = {"message": "Wrong JSON format: " + error_msg}
        # response.headers.add("Access-Control-Allow-Origin", "*")
        return response

# class HighlightLabelAPI(Resource):
@app.route('/search/highlight_label', methods=['POST'])
@cross_origin(supports_credentials=True)
def HighlightLabelAPI():
    json_data = request.get_json(force=True)
    target_clusters = json_data['target_clusters']
    print(target_clusters)
    docs = json_data['docs']
    if len(target_clusters)==0:
        content = {"docs": docs}
    else:
        new_docs = []
        for doc in docs:
            nd = process_highlight(doc, target_clusters)
            new_docs.append(nd)
        content = {"docs": new_docs}
    response = jsonify(content)
    # response.headers.add("Access-Control-Allow-Origin", "*")
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
     
# api.add_resource(SearchAPI, '/search/query')
# api.add_resource(ConceptAPI, '/search/cluster_score')
# api.add_resource(HighlightLabelAPI, '/search/highlight_label')
# api.add_resource(EditClusterAPI, '/search/edit_cluster')
     
if __name__ == '__main__':
    app.run(host="0.0.0.0",debug = True, port = 8983)

