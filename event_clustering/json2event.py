#!/usr/bin/env python3
"""Extract event pairs and generate SVGs

Usage:
  $0 --json_file /share/tool/causalgraph/fuman/data/20191228/water.jsonl.xz --svg_dir water.svg > water.event_pairs.json

"""
import argparse
import json
import lzma
import subprocess
import sys

import os
from ishi import Ishi
from pyknp import BList
from pyknp_eventgraph import EventGraph, EventGraphVisualizer

# error ids for outputting SVG
error_ids = {}

# List of want patterns
want_pattern_list = [['欲しい/ほしい']]

# volition checker
ishi = Ishi()


def generate_event_pairs_and_svg_from_json(args):
    json_file = args.json_file
    target_sub_category = args.target_sub_category
    target_relations = args.target_relation
    svg_dir = args.svg_dir
    svg_detail_dir = args.svg_detail_dir

    evgviz = EventGraphVisualizer()

    all_event_pairs = []
    with lzma.open(json_file, mode='rt') as f:
        for line in f:
            json_obj = json.loads(line.strip())
            sub_category = json_obj['sub_category']
            fuman_id = json_obj['id']
            fuman_split_knp = json_obj['fuman_split_knp']
            if target_sub_category is None or sub_category == target_sub_category:
                evg = EventGraph.build([BList(''.join(knp_list)) for knp_list in fuman_split_knp])
                # extract and print event pairs
                event_pairs = extract_event_pairs(evg, fuman_id, target_relations)
                all_event_pairs.extend(event_pairs)
                # output an SVG if svg_dir is specified
                if event_pairs and fuman_id not in error_ids:
                    if svg_dir:
                        svg_filename = os.path.join(svg_dir, fuman_id + '.svg')
                        if not os.path.exists(svg_filename):
                            print("generating {}".format(svg_filename), file=sys.stderr)
                            try:
                                evgviz.make_image(evg, svg_filename, with_detail=False, with_original_text=False)
                                if svg_detail_dir:
                                    svg_detail_filename = os.path.join(svg_detail_dir, fuman_id + '.svg')
                                    evgviz.make_image(evg, svg_detail_filename, with_original_text=False)
                            except subprocess.CalledProcessError as err:
                                print("subprocess.CalledProcessError: {}".format(err), file=sys.stderr)
    print(json.dumps(all_event_pairs, indent=2, ensure_ascii=False))


# check whether an event is a solution from rep
def include_want_from_rep(rep_str):
    reps = rep_str.split()
    for pattern in want_pattern_list:
        flag = True
        start_index = 0
        # for words in a pattern
        for pat_rep in pattern:
            start_index_org = start_index
            for i, rep in enumerate(reps[start_index:]):
                if rep == pat_rep:
                    start_index = i + 1
                    break
            # no match -> next pattern
            if start_index == start_index_org:
                flag = False
                break
        if flag:
            return True
    return False


def check_volition(event):
    # will be simplified by rethinking the design of EventGraph
    nominative = event.pas.arguments.get('ガ', None)
    if nominative:
        for base_phrase in nominative.bps:
            tag = base_phrase.tag
            if base_phrase.tid == -1:  # exophora
                # tag.midasi: "不特定:人 が"
                if tag.midasi.split(' ')[0] in {'著者', '読者', '不特定:人'}:
                    break
                else:
                    return False
            if '<SM-主体>' in tag.fstring:
                break
        else:
            return False
    return ishi(event.end)


def include_want(event):
    # モダリティ-依頼Ａ (〜して下さい), モダリティ-依頼Ｂ (〜して欲しい)
    if '依頼Ａ' in event.features.modality or '依頼Ｂ' in event.features.modality:
        return True
    # モダリティ-評価:弱 (〜したらよい), モダリティ-評価:強 (〜するべきだ)
    elif ('評価:弱' in event.features.modality or '評価:強' in event.features.modality):
        return True
    else:
        # check want expressions from rep
        return include_want_from_rep(event.normalized_reps)


def replace_ga2_with_ga(str):
    return str.replace('が２]', 'が]')


def extract_event_pairs(evg, index, target_relations):
    event_pairs = []
    for event in evg.events:
        for relation in event.outgoing_relations:
            head_event = evg.events[relation.head_evid]
            if relation.label in target_relations:
                modifier_is_solution = include_want(event)
                modifier_reps = ' '.join(event.content_rep_list)
                head_is_solution = include_want(head_event)
                head_reps = ' '.join(head_event.content_rep_list)
                event_pairs.append({
                    'sentence': evg.sentences[event.ssid].surf,
                    'modifier_mrphs': replace_ga2_with_ga(event.normalized_mrphs_without_exophora),
                    'head_mrphs': replace_ga2_with_ga(head_event.normalized_mrphs_without_exophora),
                    'modifier_reps': modifier_reps,
                    'head_reps': head_reps,
                    'modifier_is_solution': modifier_is_solution,
                    'head_is_solution': head_is_solution,
                    'modifier_has_volition': check_volition(event),
                    'head_has_volition': check_volition(head_event),
                    'relation': relation.label,
                    'doc_id': index
                })
    return event_pairs


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_file", default=None, type=str, required=True,
                        help="input json file (*.jsonl.xz).")
    parser.add_argument("--svg_dir", default=None, type=str,
                        help="directory for SVG outputs.")
    parser.add_argument("--svg_detail_dir", default=None, type=str,
                        help="directory for SVG (detail version) outputs.")
    parser.add_argument("--target_sub_category", default=None, type=str,
                        help="specify a target subcategory (default: no filtering).")
    parser.add_argument("--target_relation", default=['原因・理由', '逆接', '条件-逆条件'], type=str, nargs='*',
                        help="specify a target relation.")
    args = parser.parse_args()

    if not args.json_file:
        print("Specify an input file (*.jsonl.xz).", file=sys.stderr)
    generate_event_pairs_and_svg_from_json(args)
