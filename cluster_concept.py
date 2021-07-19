import json
from nltk.stem import PorterStemmer
from Concept_class import Concept_global, Concept_cluster
import math
from concept_score import get_score, get_kl

'''
set concept:
cui: {
    "mentions: []
    "pmids": [] which doc contain this concept, indicate global df
    "net_count":  how many times this concept occurs in the whole set
}

cluster concept:
cui: {
    "mentions": []
    "net_count": int how many times in total this concept mentioned, indicate tf
    "pmids": [] indicate cluster df
    "score": float, for ranking, can only be calculated when global df is avail
}
concept_count: total concept occurrence in the cluster
'''


# collect all the concepts in a doc list
def doc_list_parser(doc_list):
    concepts = {}
    for doc in doc_list:
        pmid = doc['pmid']
        title_ents=json.loads(doc['title_snomed_ents'])
        for ent in title_ents:
            concepts = update_concept_cluster(concepts, ent, pmid)
        abstract_ents=json.loads(doc['abstract_snomed_ents'])
        for ent in abstract_ents:
            concepts = update_concept_cluster(concepts, ent, pmid)
    return concepts
    

def update_concept_cluster(concepts, step_code_string, pmid):
    punctuation=['.',',','"',";",':',"'"]
    text=step_code_string[3].strip(".,\"':;()")
    #for each in punctuation:
    text=text
    text=text[0].upper()+text[1:]
    cui_snomeds=step_code_string[2].split(".")
    for cui_snomed in cui_snomeds:
        cui=cui_snomed.split(";")[0]
        if cui not in concepts:
            concepts[cui] = Concept_cluster(cui, text, pmid, 1)
        else:
            concepts[cui].mentions.add(text)
            concepts[cui].pmids.add(pmid)
            concepts[cui].net_count += 1

    return concepts


def process_cluster_concept(solr_results, all_clusters, top_k, global_concepts):
    all_docs = solr_results['response']['docs']
    N = len(all_docs) # total number of docs

    # process the concepts for each cluster
    # concepts are stored as object
    for i, cluster in enumerate(all_clusters):
        doc_list = []
        for idx in cluster['documents']:
            doc_list.append(all_docs[idx])
        concepts = doc_list_parser(doc_list)
        concept_count = 0
        for cui, concept_obj in concepts.items():
            concept_count += concept_obj.net_count
            global_concepts[cui].clusters.add(i)
        cluster['concepts'] = concepts
        cluster['concept_count'] = concept_count # the total number of concept occurrence
    
    # calculate the average of concept occurrence for each cluster
    # calculate the average number of documents for each cluster
    num_clusters = len(all_clusters) # total number of clusters
    num_concepts = 0 # total concept occurance for all clusters
    cluster_doc_sum = 0 # sum of number of docs for all clusters
    for cluster in all_clusters:
        num_concepts += cluster['concept_count']
        cluster_doc_sum += len(cluster['documents'])
    avg_concepts_per_cluster = float(num_concepts/num_clusters)
    avg_docs_per_cluster = float(cluster_doc_sum/num_clusters)
    # calculate the total concept occurrence of all the documents
    num_concepts_global = 0
    for cui, concept_obj in global_concepts.items():
        num_concepts_global += concept_obj.net_count
    
    for cluster in all_clusters:
        concepts = cluster['concepts']
        concepts_dict = {}
        for cui, concept_obj in concepts.items():
            global_obj = global_concepts[cui]
            score = get_score(cui, concept_obj, global_obj, cluster, N, num_clusters, 
                            avg_concepts_per_cluster, avg_docs_per_cluster, num_concepts_global)
            concepts[cui].score = score
        sorted_concepts = dict(sorted(concepts.items(), key=lambda item: item[1].score, reverse = True))
        for cui, concept_obj in sorted_concepts.items():
            concepts_dict[cui] = concept_obj.to_json()
            if len(concepts_dict)==top_k:
                break
        cluster['concepts'] = concepts_dict
    return all_clusters

# right now, only process the case when there are more than two selected clusters
# if there is only one, we can directly get the recommendation list from the original list
def process_cluster_concept_one(solr_results, clusters, top_k, global_concepts, selected_clusters):
    all_docs = solr_results['response']['docs']

    # collect doc id
    old = []
    for cid in selected_clusters:
        cluster = clusters[cid]
        docid_list = []
        if len(old)==0:
            for idx in cluster['documents']:
                docid_list.append(idx)
        else:
            for idx in cluster['documents']:
                if idx in old:
                    docid_list.append(idx)
        old = docid_list.copy()
    # collect docs
    doc_list = []
    for did in old:
        doc_list.append(all_docs[did])
    # get all the concepts in the selected documents
    # get the total number of concepts in them
    concepts = doc_list_parser(doc_list)
    concept_count = 0
    for cui, concept_obj in concepts.items():
        concept_count += concept_obj.net_count
    
    intersect_cluster = {}
    intersect_cluster['concepts'] = concepts
    intersect_cluster['concept_count'] = concept_count # the total number of concept occurrence

    num_concepts_global = 0
    for cui, concept_obj in global_concepts.items():
        num_concepts_global += concept_obj.net_count
    # get scores for each concept
    for cui, concept_obj in concepts.items():
        global_obj = global_concepts[cui]
        score = get_kl(concept_obj, global_obj, intersect_cluster, num_concepts_global)
        concepts[cui].score = score
    
    sorted_concepts = dict(sorted(concepts.items(), key=lambda item: item[1].score, reverse = True))
    concepts_dict = {}
    for cui, concept_obj in sorted_concepts.items():
        # print(concept_obj.score)
        concepts_dict[cui] = concept_obj.to_json()
        if len(concepts_dict)==top_k:
            break
    intersect_cluster['concepts'] = concepts_dict
    return intersect_cluster

    


# def process_cluster_concept2(all_concepts, all_clusters, top_k):
#     for cluster in all_clusters:
#         cl_pmids = set(cluster['pmids'])
#         cl_concepts = {}
#         for cui, content in all_concepts.items():
#             co_pmids = set(content['pmids'])
#             df = len(co_pmids)
#             intercet = (cl_pmids & co_pmids)
#             if len(intercet) != 0:
#                 cl_concepts[cui] = {"count": len(intercet), "text": content['mentions'][0], "df": df, "score": float(len(intercet)/df)}
#         sorted_concepts = dict(sorted(cl_concepts.items(), key=lambda item: item[1]['score'], reverse = True))
#         concepts_dict = {}
#         for cui, content in sorted_concepts.items():
#             concepts_dict[cui] = content['text']
#             if len(concepts_dict)==top_k:
#                 break
#         cluster['concepts'] = concepts_dict
#     return all_clusters


