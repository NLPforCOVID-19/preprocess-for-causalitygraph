import sys
import json
from typing import List, Generator, NamedTuple

import jaconv
from tqdm import tqdm
from pyknp import Juman
from transformers import BertTokenizer

# cat orig.jsonl | python scripts/preprocess_jsonl.py $(TARGET) > processed.tsv

"""
jsonl ファイルから文と topic と S-ID を取り出し、
S-ID <tab> topic <tab> 文
という形式の tsv に変換して出力する
"""

MAX_TOKEN_LENGTH = 192 - 2  # BERTKNP が扱える最大長
MAX_BYTE_SIZE = 4096  # Juman++ が扱える文の最大バイト数
JUMAN_COMMAND = '/mnt/violet/share/tool/juman++v2/bin/jumanpp'
BERTKNP_MODEL = '/mnt/berry/home/ueda/bertknp-0.2-20190901/pretrained_model'

jumanpp = Juman(command=JUMAN_COMMAND)
tokenizer = BertTokenizer.from_pretrained(BERTKNP_MODEL)


class Document(NamedTuple):
    did: str
    topic: str
    sentences: List[str]


def main():
    documents = []
    idx = 0
    for line in tqdm(sys.stdin.readlines()):
        input_obj = json.loads(line.strip())
        classes = [key for key, value in input_obj['classes'].items() if value == 1]
        if not classes:
            continue
        did = f'{sys.argv[1]}-{idx:04}'
        sentences: List[str] = list(filter_(input_obj['rawsentences']))
        documents.append(Document(did, classes[0], sentences))
        idx += 1

    for document in tqdm(documents):
        idx = 1
        for sentence in document.sentences:
            print(f'{document.did}-{idx:03}\t{document.topic}\t{sentence}')  # S-ID<tab>topic<tab>text
            idx += 1


def filter_(sents: List[str]) -> Generator[str, None, None]:
    for sent in sents:
        if not sent.endswith('。'):
            continue
        sent = sanitize(sent)
        if len(sent.encode('utf-8')) > MAX_BYTE_SIZE:
            continue
        tokens = tokenizer.tokenize(' '.join(mrph.midasi for mrph in jumanpp.analysis(sent)))
        if len(tokens) > MAX_TOKEN_LENGTH:
            continue
        yield sent


def sanitize(text: str) -> str:
    text = ''.join(text.split())
    return jaconv.h2z(text, ascii=True, digit=True)


if __name__ == '__main__':
    main()
