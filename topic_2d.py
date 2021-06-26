import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
from sklearn import manifold


def corr_to_dist(corr_array):
    # print(corr_array)
    dist_array = np.zeros(corr_array.shape)
    for i in range(len(corr_array)):
        for j in range(i, len(corr_array)):
            dist_array[i, j] = corr_array[i, i] + corr_array[j, j] - 2 * corr_array[i, j]
            dist_array[j, i] = corr_array[i, i] + corr_array[j, j] - 2 * corr_array[i, j]
    # print(dist_array)
    return dist_array

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

def proj_cluster(clusters, idx_to_cluster1):
    cluster_copy = clusters.copy()
    del cluster_copy[len(clusters)-1]
    cluster_names = []
    cluster_size = []
    for cluster in cluster_copy:
        cluster_names.append(cluster['labels'][0])
        cluster_size.append(len(cluster['documents']))
    asize = np.array(cluster_size)
    max_size = np.amax(asize)
    dot_size = 100 * ( asize / max_size )
    corr_matrix = cluster_to_matrix(cluster_copy)
    adist = corr_to_dist(corr_matrix)
    amax = np.amax(adist)
    adist /= amax
    mds = manifold.TSNE(n_components=2, metric="precomputed", random_state=6)
    results = mds.fit(adist)

    coords = results.embedding_
    plt.figure()
    plt.scatter(
        coords[:, 0], coords[:, 1], marker = 'o', s=dot_size, alpha=0.5, c=idx_to_cluster1[0:len(coords[:, 0])]
        )
    # for label, x, y in zip(cluster_names, coords[:, 0], coords[:, 1]):
    #     plt.annotate(
    #         label,
    #         fontsize=8,
    #         xy = (x, y), xytext = (-20, 20),
    #         textcoords = 'offset points', ha = 'right', va = 'bottom',
    #         bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
    #         arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))

    plt.savefig('proj_2d.png')
