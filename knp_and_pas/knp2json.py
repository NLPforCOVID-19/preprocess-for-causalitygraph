import sys
import json
import logging
import argparse
from pathlib import Path

from tqdm import tqdm

"""
省略解析済みの knp ファイル群から、
fuman_split_knp フィールドが空である jsonl ファイルを見ながら
fuman_split_knp フィールドを埋めた jsonl ファイルを出力
"""

logger = logging.getLogger()


# output_obj = {
#     'id': '',
#     'user_id': '',
#     'category': classes[0],
#     'sub_category': classes[0],
#     'company': '',
#     'branch': '',
#     'product': '',
#     'text': ''.join(sentences),
#     'created_at': '',
#     'sentences': [
#         sentences
#     ],
#     'fuman_split_knp': []
# }
# print(json.dumps(output_obj, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pas-dir', required=True, type=str,
                        help='path to directory where tagged knp files are located')
    parser.add_argument('--skipped-file', required=True, type=str,
                        help='path to a file in which skipped knp files are listed')
    args = parser.parse_args()

    skipped = []
    for line in tqdm(sys.stdin.readlines()):
        json_obj = json.loads(line.strip())
        json_obj['fuman_split_knp'] = []
        tagged_knp_file = Path(args.pas_dir) / f'fuman{json_obj["id"]}.knp'
        if tagged_knp_file.exists():
            with tagged_knp_file.open(mode='rt') as f:
                buff = []
                for knp_line in f:
                    buff.append(knp_line)
                    if knp_line.rstrip() == 'EOS':
                        json_obj['fuman_split_knp'].append(buff)
                        buff = []
        else:
            skipped.append(tagged_knp_file)
            logger.info(f'skipped: {tagged_knp_file}')

        print(json.dumps(json_obj, ensure_ascii=False))
    with open(args.skipped_file, mode='wt') as f:
        for path in skipped:
            f.write(path.name + '\n')


if __name__ == '__main__':
    main()
