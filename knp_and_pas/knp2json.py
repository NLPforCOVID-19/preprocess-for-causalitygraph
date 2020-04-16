import sys
import json
import logging
import argparse
from pathlib import Path
from collections import defaultdict

from tqdm import tqdm

"""
省略解析済みの knp ファイル群から、
fuman_split_knp フィールドを埋めた jsonl ファイルを出力
"""

logger = logging.getLogger()


def main():
    """
    stdin: tsv
    stdout: jsonl
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--pas-dir', required=True, type=str,
                        help='path to directory where tagged knp files are located')
    parser.add_argument('--skipped-file', required=True, type=str,
                        help='path to a file in which skipped knp files are listed')
    args = parser.parse_args()

    skipped = []
    did2topic = {}
    did2sentences = defaultdict(list)
    for line in tqdm(sys.stdin.readlines()):
        sid, topic, sent = line.strip().split('\t')
        did = '-'.join(sid.split('-')[:-1])
        did2topic[did] = topic
        did2sentences[did].append(sent)

    for did, sentences in did2sentences.items():

        output_obj = {
            'id': did,
            'user_id': '',
            'category': did2topic[did],
            'sub_category': did2topic[did],
            'company': '',
            'branch': '',
            'product': '',
            'text': ''.join(sentences),
            'created_at': '',
            'sentences': [
                sentences
            ],
            'fuman_split_knp': []
        }
        tagged_knp_file = Path(args.pas_dir) / f'{did}.knp'
        if tagged_knp_file.exists():
            with tagged_knp_file.open() as f:
                buff = []
                for knp_line in f:
                    buff.append(knp_line)
                    if knp_line.rstrip() == 'EOS':
                        output_obj['fuman_split_knp'].append(buff)
                        buff = []
        else:
            skipped.append(tagged_knp_file)
            logger.info(f'skipped: {tagged_knp_file}')

        print(json.dumps(output_obj, ensure_ascii=False))

    with open(args.skipped_file, mode='wt') as f:
        for path in skipped:
            f.write(path.name + '\n')


if __name__ == '__main__':
    main()
