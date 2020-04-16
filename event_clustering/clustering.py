import w2v
from collections import defaultdict
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import scipy.spatial.distance as distance
from multiprocessing import Pool
import multiprocessing as multi
import numpy as np
import sys
import json
import argparse
import pickle
import os


""" input json
  [{
    "modifier_mrphs": "[不特定:人 が] ペットボトル は 開け られ ない",
    "head_mrphs": "[著者 が] 不満だ",
    "modifier_reps": "[不特定:人 が/が] ペットボトル/ぺっとぼとる は/は 開ける/あける られる/られる ない/ない",
    "head_reps": "[著者 が/が] 不満だ/ふまんだ",
    "relation": "原因・理由",
    "doc_id": "4490357"
  },...
"""


def clustering(vec_list, label_list, similarity_threshold):
    # vec_list: クラスタリングで使われるvec, repsのw2vの平均
    # label_list: vecに対応するラベル, reps
    # similarity_threshold]: クラスタリングのしきい値
    vecs = np.empty((len(vec_list), vec_list[0].size), dtype=np.float32)
    index2label = []
    for i, (vec, label) in enumerate(zip(vec_list, label_list)):
        index2label.append(label)
        vecs[i] = vec
    pdis = distance.pdist(vecs, metric='cosine')
    z = linkage(pdis, method="complete")
    labels = fcluster(z, 1.0 - similarity_threshold, criterion='distance')
    clusters = defaultdict(list)
    for i, label in enumerate(labels):
        clusters[label].append(i)

    clusters_dict = {}
    average_vec_dict = {}
    for label, doc_ids in sorted(clusters.items(), key=lambda x: -len(x[1])):
        temp_vecs = []
        for doc_id in doc_ids:
            clusters_dict[str(label)] = clusters_dict.get(str(label), []) + [index2label[doc_id]]
            temp_vecs.append(vec_list[doc_id])
        average_vec = sum(temp_vecs)/len(temp_vecs)
        average_vec_dict[str(label)] = average_vec
    return clusters_dict, average_vec_dict


def wrapper(rep):
    repname_list = rep.split()
    return w2v.repname_list2ave_vec(repname_list), rep


def main(event_path, out_path, threshold=0.75):
    with open(event_path) as f:
        event_json = json.load(f)
    reps = []
    rep2mrphs = defaultdict(list)
    for event in event_json:
        reps.append(event["modifier_reps"])
        reps.append(event["head_reps"])
        rep2mrphs[event["modifier_reps"]].append(event["modifier_mrphs"])
        rep2mrphs[event["head_reps"]].append(event["head_mrphs"])

    with Pool(multi.cpu_count()) as pool:
        callback = pool.map(wrapper, reps)

    vec_list = []
    label_list = []
    for vec, label in callback:
        if vec is not False:
            if label not in label_list:
                vec_list.append(vec)
                label_list.append(label)
    clusters_dict, average_vec_dict = clustering(vec_list, label_list, threshold)
    
    json_path = out_path + '_' + str(threshold) + '.json'
    mrph_json_path = out_path + '_' + str(threshold) + '.mrph.json'
    pickle_path = out_path + '_' + str(threshold) + '.vec.pickle'
    
    with open(json_path, 'w') as fw:
        json.dump(clusters_dict, fw, ensure_ascii=False, indent=2)

    with open(mrph_json_path, 'w') as fw:
        cluster2mrph = defaultdict(set)
        for cluster_id, rep_list in clusters_dict.items():
            for rep in rep_list:
                mrphs = rep2mrphs[rep]
                for mrph in mrphs:
                    cluster2mrph[cluster_id].add(mrph)
            cluster2mrph[cluster_id] = list(cluster2mrph[cluster_id])
        json.dump(cluster2mrph, fw, ensure_ascii=False, indent=2)
    with open(pickle_path, 'wb') as fw:
        pickle.dump(average_vec_dict, fw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--event_path', help='path of input json', type=str)
    parser.add_argument('--out_path', help='path of output json and pickle', type=str)
    parser.add_argument('--keywords', help='to select topic', type=str, nargs='*')
    parser.add_argument('--thresholds', help='float thresholds for clustering', type=float, nargs='*', default=[0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50])
    args = parser.parse_args()
    event_dir = args.event_path
    out_dir = args.out_path
    keywords = args.keywords
    thresholds = args.thresholds
    for keyword in keywords:
        event_path = os.path.join(event_dir, '{}.event_pairs.json'.format(keyword))
        out_path = os.path.join(out_dir, keyword)
        for threshold in thresholds:
            main(event_path, out_path, threshold)

