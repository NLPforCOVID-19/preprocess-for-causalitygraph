import argparse
from pathlib import Path
from collections import defaultdict

from tqdm import tqdm
from pyknp import BList

"""
コマンドライン上で bertknp から出力された、1ファイルの knp 解析結果を文書ごとに分割する
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--knp-file', required=True, type=str, help='path to knp file')
    parser.add_argument('--tsv-file', required=True, type=str, help='path to tsv file')
    parser.add_argument('--output-dir', required=True, type=str,
                        help='path to directory where split knp files are exported')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    sent2knp = {}
    with open(args.knp_file, mode='rt') as f:
        buff = ''
        for line in tqdm(f.readlines(), desc='1/3'):
            buff += line
            if line.strip() == 'EOS':
                sent = ''.join(bnst.midasi for bnst in BList(buff).bnst_list())
                sent2knp[sent] = buff
                buff = ''

    did2knp = defaultdict(str)
    ignored_dids = set()
    with open(args.tsv_file, mode='rt') as f:
        for line in tqdm(f.readlines(), desc='2/3'):
            line = line.strip()
            sid, sent = line.split('\t')
            did = sid.split('-')[0]
            if sent not in sent2knp:
                ignored_dids.add(did)
                continue
            knp_string = sent2knp[sent]
            assert knp_string.startswith('# ')
            knp_string = knp_string[:2] + f'S-ID:{sid} ' + knp_string[2:]
            did2knp[did] += knp_string

    for did, knp_result in tqdm(did2knp.items(), desc='3/3'):
        if did in ignored_dids:
            continue
        with output_dir.joinpath(f'{did}.knp').open(mode='wt') as f:
            f.write(knp_result)


if __name__ == '__main__':
    main()
