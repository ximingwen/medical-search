import requests
import json

def search_result_clustering(search_result, local, top_k_docs, field_list, algorithm='Lingo', num_clusters=10):
    if local:
        url = "http://localhost:8985/service/cluster"
    else:
        url = "http://10.4.80.108:8985/service/cluster"
    
    parsed_results = search_result['response']
    # collect docs and field to be clustered
    doc_list = []
    for doc in parsed_results['docs'][:top_k_docs]:
        doc_dict = {}
        for field in field_list:
            doc_dict[field] = doc[field]
        doc_list.append(doc_dict)
    # may include other settings
    parameters = {"desiredClusterCount": num_clusters}
    req_frame = {"algorithm": algorithm, "language": "English", "documents": doc_list, "parameters": parameters}
    r = requests.post(url, json=req_frame, headers={"Content-Type": "text/json"})
    clusters = r.json()['clusters']
    final_clusters = process_clusters(search_result, clusters, top_k_docs)
    return clusters

def process_clusters(search_result, clusters, top_k_docs):
    clustered_docs = set()
    for cluster in clusters:
        pmids = []
        for idx in cluster['documents']:
            pmids.append(search_result['response']['docs'][idx]['pmid'])
        clustered_docs.update(cluster['documents'])
        cluster['pmids'] = pmids
    unclustered_docs = []
    unclustered_pmid = []
    for i in range(top_k_docs):
        if i not in clustered_docs:
            unclustered_docs.append(i)
            unclustered_pmid.append(search_result['response']['docs'][i]['pmid'])
    clusters.append({"documents": unclustered_docs, "labels": ["others"], "pmids": unclustered_pmid})
    return clusters


