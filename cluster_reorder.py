import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time
import scipy
import scipy.cluster.hierarchy as sch
import seaborn as sns

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

def plot_matrix_dendrogram(corr_array, linkage):
    fig = plt.figure(figsize=(8,8))
    ax1 = fig.add_axes([0.09,0.1,0.2,0.6])
    
    ax1.set_xticks([])
    ax1.set_yticks([])

    ax2 = fig.add_axes([0.3,0.71,0.6,0.2])
    Z2 = sch.dendrogram(linkage)
    ax2.set_xticks([])
    ax2.set_yticks([])

    axmatrix = fig.add_axes([0.3,0.1,0.6,0.6])
    idx1 = Z2['leaves']
    idx2 = Z2['leaves']
    D = corr_array.copy()
    D = D[idx1,:]
    D = D[:,idx2]
    im = axmatrix.imshow(D)
    axmatrix.set_xticks([])
    axmatrix.set_yticks([])
    fig.savefig('dendrogram.png')
    return idx1

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
    print(idx_to_cluster[:num_instance])
    for i in range(num_instance):
        connect_final(idx_to_cluster[:num_instance], idx_to_cluster[i], i)
    print(idx_to_cluster[:num_instance])
    return idx_to_cluster[:num_instance]
       

def cluster_corr3(corr_array, inplace=False):
    pairwise_distances = sch.distance.pdist(corr_array)
    # print(pairwise_distances)
    linkage = sch.linkage(pairwise_distances, method='complete')
    idx1 = plot_matrix_dendrogram(corr_array, linkage)
    # print(idx1)
    # print(len(corr_array))
    # print(linkage)
    for i in range(len(linkage)):
        print(f"{len(corr_array) + i}: {linkage[i, :]}")
    cluster_distance_threshold1 = int(len(corr_array)/3)
    print(cluster_distance_threshold1)
    idx_to_cluster_array1 = cluster_max_size(len(corr_array), linkage, cluster_distance_threshold1)
    print(idx_to_cluster_array1)

    cluster_distance_threshold2 = 2*int(len(corr_array)/3)
    print(cluster_distance_threshold2)
    idx_to_cluster_array2 = cluster_max_size(len(corr_array), linkage, cluster_distance_threshold2)
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

def reorder_cluster(clusters):
    cluster_names = []
    for cluster in clusters:
        cluster_names.append(cluster['labels'][0])
    corr_matrix = cluster_to_matrix(clusters)
    # print(corr_matrix.shape)
    plot_headmap(corr_matrix, cluster_names, "before")
    # sns.heatmap(corr_matrix)
    new_corr_matrix, reorder_idx, idx_to_cluster1, idx_to_cluster2 = cluster_corr3(corr_matrix)
    new_cluster_names = []
    for i in reorder_idx:
        new_cluster_names.append(cluster_names[i])
    plot_headmap(new_corr_matrix, new_cluster_names, "after")
    # print(new_corr_matrix)
    # sns.heatmap(new_corr_matrix)
    return reorder_idx, idx_to_cluster1, idx_to_cluster2
