import json
import sys
import pyknp
import re
import os
import argparse
from event_clustering import sort_by_cluster
# import sort_by_cluster
import pickle
from collections import defaultdict


class Search_event():
    def __init__(self, data_dir, svg_dir_url, keyword='water', data_date='20200120', threshold='0.6', category_file=None):
        # keywordが上位カテゴリならその下位カテゴリをkeyword_listに，下位カテゴリならそれをkeyword_list
        if category_file is not None:
            with open(category_file) as f:
                categ_lines = f.readlines()
            categ_dic = {}
            for line in categ_lines:
                categ = line.strip().split()
                super_categ = categ[2]
                sub_categ = categ[3]
                categ_dic[super_categ] = categ_dic.get(super_categ, []) + [sub_categ]
            if keyword in categ_dic:
                self.keyword_list = categ_dic[keyword]
            else:
                self.keyword_list = [keyword]
        else:
            self.keyword_list = [keyword]
        
        self.data_dir = data_dir
        self.svg_dir_url = svg_dir_url
        self.threshold = str(float(threshold))
        self.data_date = data_date
        self.negative_pattern_list = ['不満だ/ふまんだ', '嫌だ/いやだ', '困る/こまる']
        
        self.knp = pyknp.KNP(jumancommand='/mnt/violet/share/tool/juman++v2/bin/jumanpp')
        self.rep2cluster = {}
        self.event_json = {}
        self.cluster_vec_dict = {}
        self.url_format_str = {}
        self.rep2events = {}

        for keyword in self.keyword_list:
            clustering_file = os.path.join(self.data_dir, 'clustering/{}/{}_{}.json'.format(data_date, keyword, threshold))
            cluster_vec_file = os.path.join(self.data_dir, 'clustering/{}/{}_{}.vec.pickle'.format(data_date, keyword, threshold))
            event_path = os.path.join(self.data_dir, 'event_pairs/{}/{}.event_pairs.json'.format(data_date, keyword))
            self.url_format_str[keyword] = os.path.join(self.svg_dir_url, '{}/{}/{{}}.svg'.format(data_date, keyword))

            self.rep2cluster[keyword] = {}
            self.event_json[keyword] = []
            self.cluster_vec_dict[keyword] = {}
            self.rep2events[keyword] = defaultdict(list)
        
            with open(clustering_file, 'r') as f:
                for key, value in json.load(f).items():
                    for v in value:
                        self.rep2cluster[keyword][v] = key

            with open(event_path, 'r') as f:
                self.event_json[keyword] = json.load(f)

            with open(cluster_vec_file, 'rb') as f:
                self.cluster_vec_dict[keyword] = pickle.load(f)

            for event in self.event_json[keyword]:
                self.rep2events[keyword][event["modifier_reps"]].append((event, "modifier"))
                self.rep2events[keyword][event["head_reps"]].append((event, "head"))

    def _add_cluster(self, clusters, rep, mrph, url_id, sentence, keyword):
        mrph = mrph.replace(' ', '')
        url = self.url_format_str[keyword].format(url_id)
        cluster_id = self.rep2cluster[keyword].get(rep, None)
        if cluster_id is None:
            return
        else:
            # cluster_id = keyword + '.' + cluster_id
            cluster_id = cluster_id
            category = keyword
        for cluster in clusters:
            if cluster_id == cluster['cluster_id']:
                for event in cluster['events']:
                    if event['text'] == mrph:
                        return 
                cluster['events'].append({'event_id': keyword + '.' + url_id, 'text': mrph, 'url': url, 'sentence': sentence})
                return 
        clusters.append({'category': category, 'cluster_id': cluster_id, 'events': [{'event_id': keyword + '.' + url_id, 'text': mrph, 'url': url, 'sentence': sentence}]})

    def _str2mainreps(self, line):
        repname_re = re.compile(u"\<代表表記\:([^\>]+)\>")
        repetition_re = re.compile(u"(?P<c>.)(?P=c){2,}")
        result = self.knp.parse(line)
        reps = []
        for mrph in result.mrph_list():
            if mrph.hinsi in ('動詞', '形容詞', '名詞', '副詞'):
                match = repname_re.search(mrph.fstring)
                if match:
                    rep = match.group(1)
                else:
                    rep = mrph.midasi
                rep = repetition_re.sub("\g<c>\g<c>", rep)
                reps.append(rep)
        return reps

    def _rep_match(self, patterns, dat_str, len_limit=0):
        dat_reps = dat_str.split()
        # length check (if specified)
        if len_limit > 0 and len(dat_reps) > len_limit:
            return False
        # for each pattern
        for pat_rep in patterns:
            if pat_rep in dat_reps:
                return True
        return False

    def _query_match(self, query_rep_list, rep):
        rep = rep.split()
        if query_rep_list == []:
            return False
        for q in query_rep_list:
            if q not in rep:
                return False
        return True

    def _sort_results(self, clusters):
        vecs = []
        weights = []
        idx_list = []
        temp_dict = {}
        for cluster in clusters:
            # idx = cluster['cluster_id']
            # keyword = idx.split('.')[0]
            # idxnum = idx.split('.')[1]
            keyword = cluster['category']
            idxnum = cluster['cluster_id']
            idx = keyword + '.' + idxnum
            idx_list.append(idx)
            vecs.append(self.cluster_vec_dict[keyword][idxnum])
            temp_dict[idx] = cluster
            weight = len(cluster['events'])
            weights.append(weight)
        sorted_idx = sort_by_cluster.main(vecs, idx_list, weights)
        sorted_clusters = []
        for idx in sorted_idx:
            sorted_clusters.append(temp_dict[idx])
        return sorted_clusters

    def query_search(self, query):
        results = {'query': [query], 'solutions': [], 'results': [], 'causes': []}
        query_list = [self._str2mainreps(query)]
        return self._search(results, query_list)

    def cluster_search(self, cluster_id):
        category = cluster_id.split('-')[0]
        threshold = cluster_id.split('-')[1]
        cluster_index = cluster_id.split('-')[2]
        cluster_search_file = os.path.join(self.data_dir, 'clustering/{}/{}_{}.json'.format(self.data_date, category, threshold))
        cluster_search_mrph_file = os.path.join(self.data_dir, 'clustering/{}/{}_{}.mrph.json'.format(self.data_date, category, threshold))
        with open(cluster_search_file, 'r') as f:
            cluster2reps = json.load(f)
        with open(cluster_search_mrph_file, 'r') as f:
            cluster2mrphs = json.load(f)
        query_reps = [rep for rep in cluster2reps[cluster_index]]
        events = []
        for rep in query_reps:
            events.extend(self.rep2events[category][rep])
        query_mrphs = [mrph.replace(' ', '') for mrph in cluster2mrphs[cluster_index]]
        results = {'query': query_mrphs, 'solutions': [], 'results': [], 'causes': []}
        return self._classify_events(events, results, category)

    def track_cluster_search(self, query_event, track_keyword, track_threshold='0.75'):
        cluster_search_file = os.path.join(self.data_dir, 'clustering/{}/{}_{}.json'.format(self.data_date, track_keyword, track_threshold))
        cluster_search_mrph_file = os.path.join(self.data_dir, 'clustering/{}/{}_{}.mrph.json'.format(self.data_date, track_keyword, track_threshold))
        with open(cluster_search_file, 'r') as f:
            cluster2reps = json.load(f)
        with open(cluster_search_mrph_file, 'r') as f:
            cluster2mrphs = json.load(f)
        mrph2cluster = {}
        for cluster_id, mrphs in cluster2mrphs.items():
            for mrph in mrphs:
                mrph2cluster[mrph.replace(" ", "")] = cluster_id
        search_cluster_id = mrph2cluster[query_event]
        query_reps = [rep for rep in cluster2reps[search_cluster_id]]
        events = []
        for rep in query_reps:
            events.extend(self.rep2events[track_keyword][rep])
        query_mrphs = [mrph.replace(' ', '') for mrph in cluster2mrphs[search_cluster_id]]
        results = {'query': query_mrphs, 'solutions': [], 'results': [], 'causes': []}
        return self._classify_events(events, results, track_keyword)

    def _classify_events(self, events, results, keyword):
        for event, form in events:
            rep1 = event["modifier_reps"]
            rep2 = event["head_reps"]
            mrph1 = event["modifier_mrphs"]
            mrph2 = event["head_mrphs"]
            is_solution1 = event["modifier_is_solution"]
            is_solution2 = event["head_is_solution"]
            has_volition2 = event["head_has_volition"]
            docid = event["doc_id"]
            sentence = event["sentence"]
            relation = event["relation"]

            # TODO: rethink the use of 逆接
            if relation != '原因・理由':
                continue

            # query matches event1 (should not be an event of solution)
            if is_solution1 is False and form == "modifier":
                if is_solution2 or has_volition2:
                    self._add_cluster(results['solutions'], rep2, mrph2, docid, sentence, keyword)
                else:
                    # exclude negative expressions as a result
                    if not self._rep_match(self.negative_pattern_list, rep2, 4):
                        self._add_cluster(results['results'], rep2, mrph2,  docid, sentence, keyword)
            # query matches event2 (should have a causal relation; should not be an event of solution)
            if is_solution2 is False and relation == '原因・理由' and form == "head":
                self._add_cluster(results['causes'], rep1, mrph1, docid, sentence, keyword)

        results['solutions'] = self._sort_results(results['solutions'])
        results['results'] = self._sort_results(results['results'])
        results['causes'] = self._sort_results(results['causes'])
        return results


    def _search(self, results, query_list):
        for keyword in self.keyword_list:
            for query in query_list:
                for event in self.event_json[keyword]:
                    rep1 = event["modifier_reps"]
                    rep2 = event["head_reps"]
                    mrph1 = event["modifier_mrphs"]
                    mrph2 = event["head_mrphs"]
                    is_solution1 = event["modifier_is_solution"]
                    is_solution2 = event["head_is_solution"]
                    has_volition2 = event["head_has_volition"]
                    docid = event["doc_id"]
                    sentence = event["sentence"]
                    relation = event["relation"]

                    # TODO: rethink the use of 逆接
                    if relation != '原因・理由':
                        continue

                    # query matches event1 (should not be an event of solution)
                    if is_solution1 is False and self._query_match(query, rep1):
                        if is_solution2 or has_volition2:
                            self._add_cluster(results['solutions'], rep2, mrph2, docid, sentence, keyword)
                        else:
                            # exclude negative expressions as a result
                            if not self._rep_match(self.negative_pattern_list, rep2, 4):
                                self._add_cluster(results['results'], rep2, mrph2,  docid, sentence, keyword)
                    # query matches event2 (should have a causal relation; should not be an event of solution)
                    if is_solution2 is False and relation == '原因・理由' and self._query_match(query, rep2):
                        self._add_cluster(results['causes'], rep1, mrph1, docid, sentence, keyword)

        results['solutions'] = self._sort_results(results['solutions'])
        results['results'] = self._sort_results(results['results'])
        results['causes'] = self._sort_results(results['causes'])
        return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', help='what topic you want to search', type=str, default='water')
    parser.add_argument('--svg_dir_url', help='url of directory including svg file', type=str, default='water')
    parser.add_argument('--data_date', help='event data dir', type=str, default='20200120')
    parser.add_argument('--threshold', help='threshold of clustering', type=str, default='0.6')
    parser.add_argument('--mode', help='search mode: query, cluster, of track_cluster', type=str, default='query')
    parser.add_argument('--track_threshold', help='threshold for clustering file to track cluster', type=str, default='0.75')
    parser.add_argument('--track_keyword', help='topic for clustering file to track cluster', type=str, default=None)
    parser.add_argument('--category_file', help='category hierarchy file', type=str, default=None)
    parser.add_argument('--data_dir', help='directory of data. $DATA_DIR/clustering and $DATA_DIR/event_pairs are required', type=str, default=None)
    args = parser.parse_args()
    keyword = args.keyword
    svg_dir_url = args.svg_dir_url
    data_date = args.data_date
    threshold = args.threshold
    mode = args.mode
    track_threshold = args.track_threshold
    track_keyword = args.track_keyword
    data_dir = args.data_dir
    category_file = args.category_file
    search_event = Search_event(data_dir, svg_dir_url, keyword, data_date, threshold, category_file)
    while True:
        input_str = input()
        if mode == 'query':
            results = search_event.query_search(input_str) 
        elif mode == 'cluster':
            results = search_event.cluster_search(input_str) 
        elif mode == 'track_cluster':
            results = search_event.track_cluster_search(input_str, track_keyword, track_threshold) 
        else:
            print('Your input about mode option is invalid!')
            break
        print(json.dumps(results, ensure_ascii=False, indent=2))

