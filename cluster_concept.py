import json
from nltk.stem import PorterStemmer

def doc_list_parser(doc_list):
    concepts = {}
    for doc in doc_list:
        title_ents=json.loads(doc['title_snomed_ents'])
        for ent in title_ents:
            concepts = update_concept_set(concepts, ent)
        abstract_ents=json.loads(doc['abstract_snomed_ents'])
        for ent in abstract_ents:
            concepts = update_concept_set(concepts, ent)
    return concepts
    

def update_concept_set(concepts, step_code_string):
    punctuation=['.',',','"',";",':',"'"]
    text=step_code_string[3].strip(".,\"':;()")
    #for each in punctuation:
    text=text
    text=text[0].upper()+text[1:]
    cui_snomeds=step_code_string[2].split(".")
    for cui_snomed in cui_snomeds:
        cui=cui_snomed.split(";")[0]
        if cui not in concepts:
            concepts[cui] = {"text": [text], "count": 1}
        else:
            concepts[cui]["text"].append(text)
            concepts[cui]["count"] += 1

    return concepts


def process_cluster_concept(solr_results, all_clusters, top_k):
    parsed_results = solr_results['response']
    all_docs = solr_results['response']['docs']
    for cluster in all_clusters:
        doc_list = []
        for idx in cluster['documents']:
            doc_list.append(all_docs[idx])
        concpets = doc_list_parser(doc_list)
        sorted_concepts = dict(sorted(concpets.items(), key=lambda item: item[1]['count'], reverse = True))
        concepts_dict = {}
        for cui, content in sorted_concepts.items():
            concepts_dict[cui] = content['text'][0]
            if len(concepts_dict)==top_k:
                break
        cluster['concepts'] = concepts_dict
    return all_clusters

def process_cluster_concept2(all_concepts, all_clusters, top_k):
    for cluster in all_clusters:
        cl_pmids = set(cluster['pmids'])
        cl_concepts = {}
        for cui, content in all_concepts.items():
            co_pmids = set(content['pmids'])
            intercet = (cl_pmids & co_pmids)
            if len(intercet) != 0:
                cl_concepts[cui] = {"count": len(intercet), "text": content['mentions'][0]}
        sorted_concepts = dict(sorted(cl_concepts.items(), key=lambda item: item[1]['count'], reverse = True))
        concepts_dict = {}
        for cui, content in sorted_concepts.items():
            concepts_dict[cui] = content['text']
            if len(concepts_dict)==top_k:
                break
        cluster['concepts'] = concepts_dict
    return all_clusters


