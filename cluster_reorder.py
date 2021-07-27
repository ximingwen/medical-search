import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time
import scipy
import scipy.cluster.hierarchy as sch
import seaborn as sns
from scipy.spatial.distance import squareform
import functools

def plot_headmap(corr_matrix, cluster_names, name):
    fig, ax = plt.subplots()
    im = ax.imshow(corr_matrix)

    # We want to show all ticks...
    ax.set_xticks(np.arange(len(cluster_names)))
    ax.set_yticks(np.arange(len(cluster_names)))
    # ... and label them with the respective list entries
    # ax.set_xticklabels(cluster_names)
    # ax.set_yticklabels(cluster_names)

    # # Rotate the tick labels and set their alignment.
    # plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
    #         rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    # for i in range(len(cluster_names)):
    #     for j in range(len(cluster_names)):
    #         text = ax.text(j, i, corr_matrix[i, j],
    #                     ha="center", va="center", color="w")

    # ax.set_title("Harvest of local farmers (in tons/year)")
    fig.tight_layout()
    plt.savefig(f'heatmap_{name}.png')


def cluster_to_matrix(clusters):
    num_clusters = len(clusters)
    corr_matrix = np.zeros((num_clusters, num_clusters), dtype=np.float)
    for i, cluster in enumerate(clusters):
        corr_matrix[i, i] = len(cluster['documents'])
        d_list1 = cluster['documents']
        for j in range(i, num_clusters):
            d_list2 = clusters[j]['documents']
            intersection = 0
            for did in d_list1:
                if did in d_list2:
                    intersection += 1
            corr_matrix[i, j] = intersection
            corr_matrix[j, i] = intersection
    # print(corr_matrix)
    return corr_matrix


# cut by a set threshold
def cluster_corr1(corr_array, inplace=False):
    """
    Rearranges the correlation matrix, corr_array, so that groups of highly 
    correlated variables are next to eachother 
    
    Parameters
    ----------
    corr_array : pandas.DataFrame or numpy.ndarray
        a NxN correlation matrix 
        
    Returns
    -------
    pandas.DataFrame or numpy.ndarray
        a NxN correlation matrix with the columns and rows rearranged
    """
    pairwise_distances = sch.distance.pdist(corr_array)
    # print(pairwise_distances)
    linkage = sch.linkage(pairwise_distances, method='complete')
    idx1 = plot_matrix_dendrogram(corr_array, linkage)
    # print(idx1)
    idx_reverse = []
    for i in range(len(idx1)):
        idx_reverse.append(len(idx1)-1-i)
    print(linkage)
    print(len(linkage))
    unit = int(len(linkage)/3)
    # cluster_distance_threshold1 = pairwise_distances.max()/2
    cluster_distance_threshold1 = linkage[unit, 2]
    print(cluster_distance_threshold1)
    idx_to_cluster_array1 = sch.fcluster(linkage, cluster_distance_threshold1, 
                                        criterion='distance')
    print(idx_to_cluster_array1)

    # cluster_distance_threshold2 = 3 * pairwise_distances.max()/4
    cluster_distance_threshold2 = linkage[2*unit, 2]
    print(cluster_distance_threshold2)
    idx_to_cluster_array2 = sch.fcluster(linkage, cluster_distance_threshold2, 
                                        criterion='distance')
    print(idx_to_cluster_array2)
    # arranged by clusters
    idx = np.argsort(idx_to_cluster_array1)
    # print(idx)
    
    if not inplace:
        corr_array = corr_array.copy()
    
    if isinstance(corr_array, pd.DataFrame):
        return corr_array.iloc[idx, :].T.iloc[idx, :]
    return corr_array[idx, :][:, idx], idx1, idx_to_cluster_array1, idx_to_cluster_array2

# cut by max cluster
def cluster_corr2(corr_array, inplace=False):
    pairwise_distances = sch.distance.pdist(corr_array)
    # print(pairwise_distances)
    linkage = sch.linkage(pairwise_distances, method='complete')
    idx1 = plot_matrix_dendrogram(corr_array, linkage)
    # print(idx1)
    # print(len(corr_array))
    print(linkage)
    max_cluster_threshold1 = int(len(corr_array)/3)
    print(max_cluster_threshold1)
    idx_to_cluster_array1 = sch.fcluster(linkage, max_cluster_threshold1, 
                                        criterion='maxclust')
    print(idx_to_cluster_array1)

    max_cluster_threshold2 = int(len(corr_array)/5)
    print(max_cluster_threshold2)
    idx_to_cluster_array2 = sch.fcluster(linkage, max_cluster_threshold2, 
                                        criterion='maxclust')
    print(idx_to_cluster_array2)
    # arranged by clusters
    idx = np.argsort(idx_to_cluster_array1)
    # print(idx)
    
    if not inplace:
        corr_array = corr_array.copy()
    
    if isinstance(corr_array, pd.DataFrame):
        return corr_array.iloc[idx, :].T.iloc[idx, :]
    return corr_array[idx, :][:, idx], idx1, idx_to_cluster_array1, idx_to_cluster_array2

def connect(idx_to_cluster, idx1, idx2):
    if idx2 < idx1:
        tmp = idx1
        idx1 = idx2
        idx2 = tmp
    if (idx_to_cluster[idx1]==idx1) and (idx_to_cluster[idx2]==idx2):
        idx_to_cluster[idx2] = idx1
    elif idx_to_cluster[idx1]==idx1:
        connect(idx_to_cluster, idx1, idx_to_cluster[idx2])
    elif idx_to_cluster[idx2]==idx2:
        connect(idx_to_cluster, idx_to_cluster[idx1], idx2)
    else:
        connect(idx_to_cluster, idx_to_cluster[idx1], idx_to_cluster[idx2])

def connect_final(idx_to_cluster, idx1, idx2):
    if idx2 < idx1:
        tmp = idx1
        idx1 = idx2
        idx2 = tmp
    if idx_to_cluster[idx1]==idx1:
        idx_to_cluster[idx2] = idx1
    else:
        connect_final(idx_to_cluster, idx_to_cluster[idx1], idx2)

def cluster_max_size(num_instance, linkage, max_size):
    idx_to_cluster = np.arange(0, num_instance + len(linkage))
    for i in range(len(linkage)):
        row = linkage[i, :]
        if int(row[3]) <= max_size:
            idx1 = int(row[0])
            idx2 = int(row[1])
            # if int(row[0]) >= num_instance:
            #     idx1 = idx_to_cluster[int(row[0])]

            # if int(row[1]) >= num_instance:
            #     idx2 = idx_to_cluster[int(row[1])]
            connect(idx_to_cluster, idx1, i + num_instance)
            connect(idx_to_cluster, idx1, idx2)
    # print(idx_to_cluster[:num_instance])
    for i in range(num_instance):
        connect_final(idx_to_cluster[:num_instance], idx_to_cluster[i], i)
    # print(idx_to_cluster[:num_instance])
    return idx_to_cluster[:num_instance]

def corr_to_dist(corr_array):
    # print(corr_array)
    dist_array = np.zeros(corr_array.shape)
    for i in range(len(corr_array)):
        for j in range(i, len(corr_array)):
            dist_array[i, j] = corr_array[i, i] + corr_array[j, j] - 2 * corr_array[i, j]
            dist_array[j, i] = corr_array[i, i] + corr_array[j, j] - 2 * corr_array[i, j]
    # print(dist_array)
    dist_dense = squareform(dist_array)
    return dist_dense

def add_color(n, idx, color_list):
    if len(n["children"]) == 0:
        # leaf_pos = idx.index(n["node_id"])
        n["color"] = color_list[n["node_id"]]
    else:
        for child in n["children"]:
            add_color(child, idx, color_list)


def cluster_corr3(corr_array, inplace=False):
    # pairwise_distances = sch.distance.pdist(corr_array, 'cosine')
    pairwise_distances = corr_to_dist(corr_array)
    linkage = sch.linkage(pairwise_distances, method='complete')
    idx1 = plot_matrix_dendrogram(corr_array, linkage)
    d3_json = linkage_to_tree(linkage)
    cluster_distance_threshold1 = int(len(corr_array)/3)
    idx_to_cluster_array1 = cluster_max_size(len(corr_array), linkage, cluster_distance_threshold1)
    unique_clusters = list(np.unique(idx_to_cluster_array1))
    idx_to_cluster1 = [unique_clusters.index(int(idx)) for idx in idx_to_cluster_array1]
    # print(idx_to_cluster_array1)
    # print(idx_to_cluster1)
    add_color(d3_json, idx1, idx_to_cluster1)
    # cluster_distance_threshold2 = 2*int(len(corr_array)/3)
    # idx_to_cluster_array2 = cluster_max_size(len(corr_array), linkage, cluster_distance_threshold2)
    # arranged by clusters
    idx = np.argsort(idx_to_cluster_array1)
    
    if not inplace:
        corr_array = corr_array.copy()
    
    if isinstance(corr_array, pd.DataFrame):
        return corr_array.iloc[idx, :].T.iloc[idx, :]
    return corr_array[idx, :][:, idx], idx1, idx_to_cluster1, d3_json

# Create a nested dictionary from the ClusterNode's returned by SciPy
def add_node(node, parent ):
    # First create the new node and append it to its parent's children
    newNode = dict( node_id=node.id, children=[] )
    parent["children"].append( newNode )

    # Recursively add the current node's children
    if node.left: add_node( node.left, newNode )
    if node.right: add_node( node.right, newNode )

def linkage_to_tree(linkage):
    T = sch.to_tree(linkage , rd=False )
    d3Dendro = dict(children=[], name="Root1")
    add_node( T, d3Dendro )
    return d3Dendro

def plot_matrix_dendrogram(corr_array, linkage):
    # fig = plt.figure(0, figsize=(8,8))
    # ax1 = fig.add_axes([0.09,0.1,0.2,0.6])
    
    # ax1.set_xticks([])
    # ax1.set_yticks([])

    # ax2 = fig.add_axes([0.3,0.71,0.6,0.2])
    Z2 = sch.dendrogram(linkage)
    # ax2.set_xticks([])
    # ax2.set_yticks([])

    # axmatrix = fig.add_axes([0.3,0.1,0.6,0.6])
    idx1 = Z2['leaves']
    idx2 = Z2['leaves']
    D = corr_array.copy()
    D = D[idx1,:]
    D = D[:,idx2]
    # im = axmatrix.imshow(D)
    # axmatrix.set_xticks([])
    # axmatrix.set_yticks([])
    # fig.savefig('dendrogram.png')
    return idx1

def label_tree( n, id2name, id2value):
    # If the node is a leaf, then we have its name
    if len(n["children"]) == 0:
        leafNames = [ id2name[n["node_id"]] ]
        n["name"] = leafNames[0]
        n["value"] = id2value[n["node_id"]]
    # else:
        
    #     n["name"] = str(n["node_id"])
    # If not, flatten all the leaves in the node's subtree
    else:
        leafNames = functools.reduce(lambda ls, c: ls + label_tree(c, id2name, id2value), n["children"], [])

    # Delete the node id since we don't need it anymore and
    # it makes for cleaner JSON
    # del n["node_id"]

    # Labeling convention: "-"-separated leaf names
    n["name"] = name = "-".join(sorted(map(str, leafNames)))

    return leafNames


def reorder_cluster(clusters):
    cluster_names = []
    cluster_size = []
    for cluster in clusters:
        cluster_names.append(cluster['labels'][0])
        cluster_size.append(len(cluster['documents']))
    corr_matrix = cluster_to_matrix(clusters)
    # print(corr_matrix.shape)
    # plot_headmap(corr_matrix, cluster_names, "before")
    # sns.heatmap(corr_matrix)
    new_corr_matrix, reorder_idx, idx_to_cluster1, d3_json = cluster_corr3(corr_matrix)
    # print(d3_json)
    new_cluster_names = []
    # print(reorder_idx)
    for i in reorder_idx:
        new_cluster_names.append(cluster_names[i])
    label_tree(d3_json, cluster_names, cluster_size)
    # print(d3_json['children'][0])
    # plot_headmap(new_corr_matrix, new_cluster_names, "after")
    # print(new_corr_matrix)
    # sns.heatmap(new_corr_matrix)
    return reorder_idx, idx_to_cluster1, d3_json['children'][0]

def reorder_by_type(clusters, concepts_original):
    idx_to_cluster = []
    for cluster in clusters:
        idx_to_cluster.append(concepts_original[cluster['cid']].concept_type)
        print(cluster['labels'])
    print(idx_to_cluster)
    reorder_idx = np.argsort(idx_to_cluster)
    print(reorder_idx)
    pos = [-1, -1, -1, -1, -1, -1]
    curr_type = -1
    for i, cluster_id in enumerate(reorder_idx):
        t = idx_to_cluster[cluster_id]
        if t != curr_type:
            curr_type = t
            pos[curr_type] = i
    print(pos)
    non_zero_pos = [i for i in pos if (i >= 0)]
    non_zero_pos.append(len(clusters))
    sorted_idx = []
    for i in range(len(non_zero_pos)-1):
        tmp = list(reorder_idx[non_zero_pos[i]:non_zero_pos[i + 1]])
        tmp.sort()
        sorted_idx += tmp
    print(sorted_idx)
    return sorted_idx, idx_to_cluster, pos
