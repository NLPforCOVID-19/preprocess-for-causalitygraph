from collections import defaultdict
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import scipy.spatial.distance as distance
import numpy as np
import sys
import json
import argparse
import pickle


class Leaf:
    def __init__(self, idx, weight): 
        self.weight = weight
        self.idx = idx

    def sort(self):
        return [self.idx]


class Tree:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.weight = left.weight + right.weight 

    def sort(self):
        if self.left.weight >= self.right.weight: 
            return self.left.sort() + self.right.sort()
        else:
            return self.right.sort() + self.left.sort()

def make_tree(z, label_list, weights):
    trees = []
    for label, w in zip(label_list, weights):
        trees.append(Leaf(label, w))
    for i in z:
        idx1 = int(i[0])
        idx2 = int(i[1])
        tree1 = trees[idx1]
        tree2 = trees[idx2]
        trees.append(Tree(tree1, tree2))
    return trees[-1]


def sort_by_clustering(vec_list, label_list, weights):
    # vec_list: クラスタリングで使われるvec, repsのw2vの平均
    # label_list: vecに対応するラベル, reps
    # similarity_threshold]: クラスタリングのしきい値
    if vec_list == [] or len(vec_list) == 1:
        return label_list
    vecs = np.empty((len(vec_list), vec_list[0].size), dtype=np.float32)
    index2label = []
    for i, (vec, label) in enumerate(zip(vec_list, label_list)):
        index2label.append(label)
        vecs[i] = vec
    pdis = distance.pdist(vecs, metric='cosine')
    # z = linkage(pdis, method="complete", optimal_ordering=True)
    z = linkage(pdis, method="complete")
    tree = make_tree(z, label_list, weights)
    return tree.sort()
    # return z#, sorted_label_list


def main(vec_list, label_list, weights):
    return sort_by_clustering(vec_list, label_list, weights)


if __name__ == '__main__':
    with open('./test.json') as f:
        label_dict = json.load(f)
    with open('./test.pickle', 'rb') as f:
        vec_dict = pickle.load(f)

    vec_list, idx_list = [], []
    for key, value in vec_dict.items():
        idx_list.append(str((int(key))))
        vec_list.append(value)

    weights = [1]*10
    z = main(vec_list[:10], idx_list[:10], weights)
    print(z)


    # fig = plt.figure(figsize=(15, 7))
    # dn = dendrogram(z)
    # plt.show()




    
    
