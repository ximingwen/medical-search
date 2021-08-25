import numpy as np
import sys
'''
concepts is a dict with cui: concept object as defined in text_parser.py
    self.cui = cui
    self.snomed_codes = set(snomed_codes)
    self.mentions = set([mention])
    self.pmids = set([pmid])
    self.net_count = net_count
    self.clusters = set()
    self.docids = set([docids])
'''

stop_list = ["C0332875", "C3539106", "C1446409", "C0205160", "C0185115", "C0700287", "C1273869", "C1299583"]

def concept_clustering(concepts, num_clusters, top_k_docs):
    cui_list = []
    for cui in concepts:
        if cui not in stop_list:
            cui_list.append(cui)
    cooccur_mat = -np.ones((len(cui_list), len(cui_list)), dtype=np.int)
    for i in range(len(cui_list)):
        cooccur_mat[i, i] = len(concepts[cui_list[i]].docids)
        # for j in range(i, len(cui_list)):
        #     cooccur_mat[i, j] = len(concepts[cui_list[i]].docids.intersection(concepts[cui_list[j]].docids))
        #     cooccur_mat[j, i] = len(concepts[cui_list[i]].docids.intersection(concepts[cui_list[j]].docids))
    l = 0.5
    selected_concept = []
    while len(selected_concept) < num_clusters:
        new_concept_id = select_concept(concepts, cui_list, selected_concept, cooccur_mat, l, top_k_docs)
        selected_concept.append(new_concept_id)
    clusters = []
    print(selected_concept)
    for c in selected_concept:
        c_object = concepts[cui_list[c]]
        labels = []
        lower_labels = []
        for label in list(c_object.mentions):
            if label.lower() not in lower_labels:
                labels.append(label)
                lower_labels.append(label.lower())
        c_dict = {
            "labels": labels,
            "documents": list(c_object.docids),
            "cid": cui_list[c],
            "c_type": c_object.concept_type
        }
        clusters.append(c_dict)
    return clusters

    
def select_concept(concepts, cui_list, selected_concept, cooccur_mat, l, top_k_docs):
    best_concept = 0
    best_score = np.NINF
    # print(selected_concept)
    for i in range(cooccur_mat.shape[0]):
        if i in selected_concept:
            continue
        df = cooccur_mat[i, i]
        if df > top_k_docs/2:
            continue
        sim = [0]
        #[max(0, len(selected_concept)-5):]
        for c in selected_concept:
            if cooccur_mat[c, i] == -1:
                intersection = len(concepts[cui_list[i]].docids.intersection(concepts[cui_list[c]].docids))
                cooccur_mat[c, i] = intersection
                cooccur_mat[i, c] = intersection
            sim.append(cooccur_mat[i, c])
        max_sim = np.amax(sim)
        # if i < 30:
        #     # print(df, max_sim)
        #     print(np.where(np.array(sim)==max_sim))
        score = l * df - (1 - l) * max_sim
        if score > best_score:
            best_score = score
            best_concept = i
            # print(i, best_score)
    return best_concept

def edit_cluster(current_clusters, concepts, must_exclude, top_k_docs):
    cui_list = []
    selected_concept = []
    for cui in concepts:
        if (cui not in must_exclude) and (cui not in stop_list):
            cui_list.append(cui)
    cooccur_mat = -np.ones((len(cui_list), len(cui_list)), dtype=np.int)
    for cluster in current_clusters:
        if (cluster['cid'] not in must_exclude) and (cluster['cid'] not in stop_list):
            selected_concept.append(cui_list.index(cluster['cid']))
    for i in range(len(cui_list)):
        cooccur_mat[i, i] = len(concepts[cui_list[i]].docids)
        # for j in range(i, len(cui_list)):
        #     cooccur_mat[i, j] = len(concepts[cui_list[i]].docids.intersection(concepts[cui_list[j]].docids))
        #     cooccur_mat[j, i] = len(concepts[cui_list[i]].docids.intersection(concepts[cui_list[j]].docids))
    l = 0.5
    new_concept_id = select_concept(concepts, cui_list, selected_concept, cooccur_mat, l, top_k_docs)
    selected_concept.append(new_concept_id)
    clusters = [cluster for cluster in current_clusters if cluster['cid'] not in must_exclude]
    c_object = concepts[cui_list[new_concept_id]]
    labels = []
    lower_labels = []
    for label in list(c_object.mentions):
        if label.lower() not in lower_labels:
            labels.append(label)
            lower_labels.append(label.lower())
    c_dict = {
        "labels": labels,
        "documents": list(c_object.docids),
        "cid": cui_list[new_concept_id]
    }
    clusters.append(c_dict)
    return clusters