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
def concept_clustering(concepts, num_clusters, top_k_docs):
    cui_list = []
    cooccur_mat = -np.ones((len(concepts.keys()), len(concepts.keys())), dtype=np.int)
    for cui in concepts:
        cui_list.append(cui)
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
            "cid": cui_list[c]
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

