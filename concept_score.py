import json
from nltk.stem import PorterStemmer
from Concept_class import Concept_global, Concept_cluster
import math

'''
set concept:
cui: {
    "mentions: []
    "pmids": [] which doc contain this concept, indicate global df
    "net_count":  how many times this concept occurs in the whole set
    "clusters": [] this concept appears in which cluster
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

def get_score(
    cui, # the cui of the concept to calculate the score
    concept_obj, # the object of this concept in the cluster
    global_obj, # the object of this concept in the whole doc set
    cluster, # the cluster that this concept belong to
    N, # total number of retrieved docs
    Nc, # total number of clusters
    avg_concepts_per_cluster, # average number of concepts for each cluster
    avg_docs_per_cluster, # average number of docs for each cluster
    num_concepts_global # total number of concepts for all the retrieved docs
    ):

    # a. bm25
    k = 1.2
    b = 0.75
    # freq of concept in this cluster
    f_c = concept_obj.net_count # len(concept_obj.pmids)
    n_c = len(global_obj.clusters)
    D = cluster['concept_count'] # len(cluster['documents'])
    avgd = avg_concepts_per_cluster # aavg_docs_per_cluster
    tf = (f_c * (k + 1))/(f_c + k * (1 - b + b * (D / avgd)))
    idf = math.log(1 + (Nc - n_c + 0.5)/(n_c + 0.5))
    
    # b. mi
    #   1) p_x|y
    p_xy = float(concept_obj.net_count/cluster['concept_count'])
    #   2) p_x
    p_x = float(global_obj.net_count/num_concepts_global)
    mi = p_xy * math.log(p_xy/p_x)
    return mi

def get_kl(concept_obj, global_obj, cluster, num_concepts_global):
    #   1) p_x|y
    p_xy = float(concept_obj.net_count/cluster['concept_count'])
    #   2) p_x
    p_x = float(global_obj.net_count/num_concepts_global)
    mi = p_xy * math.log(p_xy/p_x)
    return mi