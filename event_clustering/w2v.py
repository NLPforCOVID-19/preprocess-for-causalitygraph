import gensim
import ast
import sys
import re
import numpy as np
from multiprocessing import Pool
import multiprocessing as multi
from tqdm import tqdm 
from sklearn.metrics.pairwise import cosine_similarity

# repname or midasi
w2v_path = '/share/data/word2vec/2016.08.02/w2v.repname.256.100K.bin'
# w2v_path = '/share/data/word2vec/2016.08.02/w2v.midasi.256.100K.bin'

model = gensim.models.KeyedVectors.load_word2vec_format(w2v_path, binary=True, encoding='utf8', unicode_errors='ignore')

def mrph2str(mrph):
    if mrph.bunrui == u"数詞":
        return u"<数量>"
    match = mrph2str.repname_re.search(mrph.fstring)
    if match:
        midasi = match.group(1)
    else:
        midasi = mrph.midasi
    # midasi = mrph2str.repetition_re.sub("\g<c>\g<c>", midasi)
    return midasi

mrph2str.repname_re = re.compile(u"\<正規化代表表記\:([^\>]+)\>")
mrph2str.repetition_re = re.compile(u"(?P<c>.)(?P=c){2,}")

def mrph2decomposed_str(mrph):
    if mrph.bunrui == u"数詞":
        return u"<数量>", None
    match = mrph2str.repname_re.search(mrph.fstring)
    if match:
        midasi = match.group(1)
    else:
        midasi = mrph.genkei
    midasi = mrph2str.repetition_re.sub("\g<c>\g<c>", midasi)
    ending = None
    if mrph.katuyou2 not in (u'*', u'語幹'):
        ending = '<' + mrph.katuyou2 + '>'
    return midasi, ending

def get_ave_vec(line):
    hinsi_list = ['名詞', '形容詞', '動詞']
    import pyknp
    knp = pyknp.KNP()
    decompose = True
    total_vec = []
    result = knp.parse(line)
    for mrph in result.mrph_list():
        if mrph.hinsi in hinsi_list:
            if decompose == True:
                midasi, ending = mrph2decomposed_str(mrph)
                if midasi in model.vocab:
                    total_vec.append(model[midasi])
            else:
                midasi = mrph2str(mrph)
    if total_vec == []:
        return False
    return sum(total_vec)/len(total_vec)

def repname_list2ave_vec(repname_list):
    total_vec = []
    for repname in repname_list:
        if repname in model.vocab:
            total_vec.append(model[repname])
    if total_vec == []:
        return False
    return sum(total_vec)/len(total_vec)


def cos_sim(v1, v2):
    x = (np.linalg.norm(v1) * np.linalg.norm(v2))
    if x == 0:
        return 0
    else:
        return np.dot(v1, v2) / x

if __name__ == "__main__":
    # test
    dougi_path = '/mnt/hinoki/kawahara/causalgraph/phrase_dougi/synonyms.txt'
    hangi_path = '/mnt/hinoki/kawahara/causalgraph/phrase_dougi/antonyms.txt'
    neutral_path = '/mnt/hinoki/kawahara/causalgraph/phrase_dougi/neutrals.txt'
    path_list = [dougi_path, hangi_path, neutral_path]
    out_path_list = ['dougi.txt', 'hangi.txt', 'neutral.txt']

    def main(line):
        temp = line.split()[0].split('##')
        event1 = temp[0]
        event2 = temp[1]
        return event1, event2, cos_sim(get_ave_vec(event1), get_ave_vec(event2))

    for path, out_path in zip(path_list, out_path_list):
        output_list = []
        with open(path) as f:
            lines = f.readlines()

            with Pool(multi.cpu_count()) as pool, tqdm(total=len(lines)) as t:
                callback = []
                for i in pool.imap(main, lines):
                    callback.append(i)
                    print(i)
                    t.update(1)
        with open(out_path, 'w') as f:
            for event1, event2, sim in callback:
                f.write(event1 + ' ' + event2 + ' ' + str(sim) + '\n')


