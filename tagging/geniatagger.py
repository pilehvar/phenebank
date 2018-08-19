#!/usr/bin/env python
import subprocess
import os.path
from nltk import word_tokenize

class GeniaTagger(object):

    def __init__(self, path_to_tagger):
        self._path_to_tagger = path_to_tagger
        self._dir_to_tagger = os.path.dirname(path_to_tagger)
        self._tagger = subprocess.Popen('./'+os.path.basename(path_to_tagger),
                                        cwd=self._dir_to_tagger,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def parse(self, text):
        results = list()
        thisline = list()

        text = text.encode('utf-8')
        for oneline in text.split('\n'):
            self._tagger.stdin.write(oneline+'\n')
            while True:
                r = self._tagger.stdout.readline()[:-1]
                if not r:
                    break
                thisline.append(tuple(r.split('\t')))

            results.append(thisline)
            thisline = list()

        return results


def _main():
    tagger = GeniaTagger('../utils/Genia_tagger/geniatagger')
    input = 'It is well known that x-linked adrenoleukodystrophy (X-ALD) is the most common peroxisomal disorder [1] . ' \
            'The disease is caused by mutations in the ABCD1 gene that encodes for the peroxisomal membrane protein ALDP which is involved in the '

    print tagger.parse(input)
    print word_tokenize(input)

    
if __name__ == '__main__':
        _main()
