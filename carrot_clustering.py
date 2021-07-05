import requests
import json

def process_field(field, doc):
    content = doc[field][0]
    span_info = doc[f"{field}_spans"]
    content_words = content.split(" ")
    after_list = []
    span_i = 0
    for i, word in enumerate(content_words):
        if span_i >= len(span_info):
            after_list += content_words[i:]
            break
        current_span = span_info[span_i]['span']
        if i < current_span[0]:
            after_list.append(word)
        elif i==current_span[0]:
            after_list.append("_".join(content_words[current_span[0]: current_span[1]+1]))
        if i==current_span[1]:
            span_i += 1
    new_content = " ".join(after_list)
    return new_content


def search_result_clustering(search_result, local, top_k_docs, field_list, algorithm='Lingo', num_clusters=10):
    if local:
        url = "http://localhost:8985/service/cluster"
    else:
        url = "http://10.4.80.108:8985/service/cluster"
    
    parsed_results = search_result['response']
    # collect docs and field to be clustered
    doc_list = []
    for i, doc in enumerate(parsed_results['docs'][:top_k_docs]):
        doc_dict = {}
        for field in field_list:
            # doc_dict[field] = doc[field]
            doc_dict[field] = [process_field(field, doc)]
        doc_list.append(doc_dict)
    # may include other settings
    # parameters = {"desiredClusterCount": num_clusters}
    # print(algorithm)
    if algorithm == "Lingo":
        parameters = {"desiredClusterCount": num_clusters}
    elif algorithm == "STC":
        parameters = {"maxClusters": num_clusters}
    elif algorithm == "Bisecting K-Means":
        parameters = {"clusterCount": num_clusters}
    req_frame = {"algorithm": algorithm, "language": "English", "documents": doc_list, "parameters": parameters}
    r = requests.post(url, json=req_frame, headers={"Content-Type": "text/json"})
    # print(r.json())
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
