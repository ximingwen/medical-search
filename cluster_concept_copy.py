import json
from nltk.stem import PorterStemmer
from Concept_class import Concept_global, Concept_cluster

'''
set concept:
cui: {
    "mentions: []
    "pmids": [] which doc contain this concept, indicate global df
}

cluster concept:
cui: {
    "mentions": []
    "net_count": int how many times in total this concept mentioned, indicate tf
    "pmids": [] indicate cluster df
    "score": float, for ranking, can only be calculated when global df is avail
}
'''



def doc_list_parser(doc_list, global_concept):
    concepts = {}
    for doc in doc_list:
        pmid = doc['pmid']
        title_ents=json.loads(doc['title_snomed_ents'])
        for ent in title_ents:
            concepts = update_concept_cluster(concepts, ent, pmid)
            global_concept = update_concept_global(global_concept, ent, pmid)
        abstract_ents=json.loads(doc['abstract_snomed_ents'])
        for ent in abstract_ents:
            concepts = update_concept_cluster(concepts, ent, pmid)
            global_concept = update_concept_global(global_concept, ent, pmid)
    return concepts, global_concept
    

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

def update_concept_global(concepts, step_code_string, pmid):
    punctuation=['.',',','"',";",':',"'"]
    text=step_code_string[3].strip(".,\"':;()")
    #for each in punctuation:
    text=text
    text=text[0].upper()+text[1:]
    cui_snomeds=step_code_string[2].split(".")
    for cui_snomed in cui_snomeds:
        cui=cui_snomed.split(";")[0]
        if cui not in concepts:
            concepts[cui] = Concept_global(cui, text, pmid)
        else:
            concepts[cui].mentions.add(text)
            concepts[cui].pmids.add(pmid)

    return concepts


def process_cluster_concept(solr_results, all_clusters, top_k):
    parsed_results = solr_results['response']
    all_docs = solr_results['response']['docs']
    global_concepts = {}
    for cluster in all_clusters:
        doc_list = []
        for idx in cluster['documents']:
            doc_list.append(all_docs[idx])
        concepts, global_concepts = doc_list_parser(doc_list, global_concepts)
        # sorted_concepts = dict(sorted(concpets.items(), key=lambda item: item[1]['count'], reverse = True))
        # concepts_dict = {}
        # for cui, content in sorted_concepts.items():
        #     concepts_dict[cui] = content['text'][0]
        #     if len(concepts_dict)==top_k:
        #         break
        cluster['concepts'] = concepts
    for cluster in all_clusters:
        concepts = cluster['concepts']
        concepts_dict = {}
        for cui, concept_obj in concepts.items():
            global_obj = global_concepts[cui]
            df = len(global_obj.pmids)
            tf = concept_obj.net_count
            concepts[cui].score = float(tf/df)
        sorted_concepts = dict(sorted(concepts.items(), key=lambda item: item[1].score, reverse = True))
        for cui, concept_obj in sorted_concepts.items():
            concepts_dict[cui] = concept_obj.to_json()
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
            df = len(co_pmids)
            intercet = (cl_pmids & co_pmids)
            if len(intercet) != 0:
                cl_concepts[cui] = {"count": len(intercet), "text": content['mentions'][0], "df": df, "score": float(len(intercet)/df)}
        sorted_concepts = dict(sorted(cl_concepts.items(), key=lambda item: item[1]['score'], reverse = True))
        concepts_dict = {}
        for cui, content in sorted_concepts.items():
            concepts_dict[cui] = content['text']
            if len(concepts_dict)==top_k:
                break
        cluster['concepts'] = concepts_dict
    return all_clusters


