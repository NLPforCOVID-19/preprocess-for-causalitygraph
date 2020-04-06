import sys
import json
from tqdm import tqdm
from typing import List, Generator

# cat orig.jsonl | python scripts/preprocess_jsonl.py > processed.jsonl


def filter_(sents: List[str]) -> Generator[str]:
    for sent in sents:
        if sent.endswith('。'):
            yield sent


def main():
    for line in tqdm(sys.stdin.readlines()):
        input_obj = json.loads(line.strip())
        classes = [key for key, value in input_obj['classes'].items() if value == 1]
        if not classes:
            continue
        sentences: List[str] = list(filter_(input_obj['rawsentences']))

        output_obj = {
            'id': '',
            'user_id': '',
            'category': classes[0],
            'sub_category': classes[0],
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
        print(json.dumps(output_obj, ensure_ascii=False))


if __name__ == '__main__':
    main()
