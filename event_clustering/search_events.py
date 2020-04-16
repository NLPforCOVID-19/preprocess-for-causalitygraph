import re
import json
import argparse
from typing import List, Dict, Tuple
from collections import defaultdict

from pyknp import KNP


class EventSearcher:

    def __init__(self, category: str = 'water', data_date: str = '20191228', threshold: str = '0.75'):
        with open('fuman_categories.txt') as f:
            categ_lines = f.readlines()
        categ_dic = {}
        for line in categ_lines:
            categ = line.strip().split()
            super_categ = categ[2]
            sub_categ = categ[3]
            categ_dic[super_categ] = categ_dic.get(super_categ, []) + [sub_categ]
        if category in categ_dic:
            self.categories = categ_dic[category]
        else:
            self.categories = [category]

        self.knp = KNP(jumancommand='/mnt/violet/share/tool/juman++v2/bin/jumanpp')

        self.events: List[Dict[str, str]] = []
        self.rep2cluster: Dict[str, Dict[str, str]] = {}

        for category in self.categories:
            event_path = f'/share/tool/causalgraph/fuman/event_pairs/{data_date}/{category}.event_pairs.json'
            clustering_path = f'/share/tool/causalgraph/fuman/clustering/{data_date}/{category}_{threshold}.json'
            # clustering_path = f'/mnt/hinoki/ytanaka/causalgraph/clustering/{category}_{threshold}.json'
            
            self.rep2cluster[category] = {}
            with open(clustering_path, 'r') as f:
                json_data = json.load(f)
            for clusterid, reps in json_data.items():
                for rep in reps:
                    self.rep2cluster[category][rep] = category + '-' + threshold + '-' + clusterid
            with open(event_path, 'r') as f:
                for event_pair in json.load(f):
                    # TODO: rethink the use of 逆接
                    if event_pair['relation'] != '原因・理由':
                        continue

                    if event_pair['modifier_reps'] in self.rep2cluster[category]:
                        self.events.append({'mrphs': event_pair['modifier_mrphs'], 'reps': event_pair['modifier_reps'], 'sentence': event_pair['sentence'], 'cluster_id': self.rep2cluster[category][event_pair['modifier_reps']]})
                    if event_pair['head_reps'] in self.rep2cluster[category]:
                        self.events.append({'mrphs': event_pair['head_mrphs'], 'reps': event_pair['head_reps'], 'sentence': event_pair['sentence'], 'cluster_id': self.rep2cluster[category][event_pair['head_reps']]})

    @staticmethod
    def _match(query_reps: List[str], reps: List[str]) -> bool:
        return set(query_reps) <= set(reps)

    @staticmethod
    def _modify_mrphs(mrphs: str) -> str:
        revised_event_text = ''

        # remove omitted arguments
        flag = True
        for character in mrphs:
            if character == '[':
                flag = False
                continue
            elif character == ']':
                flag = True
                continue
            if flag:
                revised_event_text += character

        # remove white spaces
        revised_event_text = revised_event_text.replace(' ', '').strip()

        return revised_event_text

    # def sort_events(self, events: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        # max_len = max([len(event_mrph) for event_mrph, event_sent in events])
        # sorted_list = []
        # for i in range(max_len):
            # sorted_list.extend(sorted([(event_mrph, event_sent) for event_mrph, event_sent in events if len(event_mrph) == i+1], key=lambda x: x[0]))
        # return sorted_list

    def _sort_events(self, events: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        # mrphの頻度の大きいものが先にくるように並び替え
        event_count = defaultdict(int)
        mrph2sents = defaultdict(list)
        for event_mrph, event_sent in events:
            event_count[event_mrph] += 1
            mrph2sents[event_mrph].append(event_sent)
        ans_list = []
        for event_mrph, _ in sorted(event_count.items(), key=lambda x:-x[1]):
            ans_list.extend([(event_mrph, event_sent) for event_sent in sorted(mrph2sents[event_mrph])])
        return ans_list

    def search(self, query: str) -> List[Tuple[str, int]]:
        query_reps = self._query2reps(query)
        cluster_freqs: Dict[str, int] = defaultdict(int)
        cluster2events: Dict[str, set[tuple(str, str)]] = defaultdict(set)
        for event in self.events:
            reps: List[str] = event['reps'].split()
            cluster_id: str = event['cluster_id']
            sentence: str = event['sentence']
            # if query is empty string, show all clusters
            if query == "" or self._match(query_reps, reps):
                mrphs = self._modify_mrphs(event['mrphs'])
                if (mrphs, sentence) not in cluster2events[cluster_id]:
                    cluster_freqs[cluster_id] += 1
                cluster2events[cluster_id].add((mrphs, sentence))
        return [(cluster_id, self._sort_events(list(cluster2events[cluster_id])), freq) for cluster_id, freq in sorted(cluster_freqs.items(), key=lambda x: -x[1])]

    def _query2reps(self, query: str) -> List[str]:
        repname_re = re.compile(r'<正規化代表表記:([^>]+)>')
        repetition_re = re.compile(r'(?P<c>.)(?P=c){2,}')
        result = self.knp.parse(query)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', help='what topic you want to search', type=str, default='water')
    parser.add_argument('--data-date', help='event data dir', type=str, default='20191228')
    parser.add_argument('--threshold', help='threshold of clustering file', type=str, default='0.75')
    args = parser.parse_args()
    category = args.category
    data_date = args.data_date
    threshold = args.threshold
    searcher = EventSearcher(category, data_date, threshold)
    while True:
        query = input()
        results = searcher.search(query)
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
