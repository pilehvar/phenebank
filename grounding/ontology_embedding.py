import os
import sys
sys.path.append('..')
import ontology.hpo as hp
import ontology.mesh as mesh
import ontology.omim as omim
import ontology.snomed as snomed
import ontology.fma as fma
import ontology.pro as pro
from nltk import ngrams
from utils.project_config import  ProjectConfig
import re
from gensim.models.keyedvectors import KeyedVectors
import numpy as np
from ontology.ontologies import Ontology
import nltk
class namemb():
    stopwords = "for an a of the in at ( ) -".split(" ")
    def __init__(self, base_embedding_path, ontology=None, load_ontologies=False, extend_ontologies=False, ignore_unknown=True):

        print("Loading vectors from", base_embedding_path)

        self.word_vectors = KeyedVectors.load_word2vec_format(base_embedding_path, binary=True)

        if load_ontologies:
            assert not ontology is None
            if ontology == Ontology.HPO:
                self.ontology = hp.Ontology()

            if ontology == Ontology.MESH:
                self.ontology = mesh.Ontology(extend_with_umls=extend_ontologies)

            if ontology == Ontology.OMIM:
                self.ontology = omim.Ontology()

            if ontology == Ontology.SNOMED:
                self.ontology = snomed.Ontology(prune=False)

            if ontology == Ontology.SNOMED:
                self.ontology = snomed.Ontology()

            if ontology == Ontology.PRO:
                self.ontology = pro.Ontology(id_filter=['PR'], human_filter=True)

            if ontology == Ontology.FMA:
                self.ontology = fma.Ontology()

        self.unk_vec = self.normalize(self.word_vectors["</s>"])

        self.include_unk = (not ignore_unknown)


    def process_name(self, name):
        return re.sub('[^0-9a-zA-Z]+', ' ', name)


    def normalize(self, v):
        norm = np.linalg.norm(v)
        if norm == 0:
            return v
        return v / norm


    def break_to_ngram(self, word, min, max):
        this_ngrams = set()
        for i in range(min,max+1):
            grams = ngrams(word, i)
            for gram in grams:
                this_ngrams.add("".join(gram))
        return this_ngrams


    def get_enhanced_embedding(self, name, ngram_backoff=True, replace_unk=False):
        adjs = []
        nouns = []
        for t in nltk.pos_tag(nltk.word_tokenize(name)):
            token = t[0]
            pos = t[1]
            if pos.lower().startswith(("n","j","r","v")):
                if pos.lower().startswith("j"):
                    adjs.append(token)
                else:
                    nouns.append(token)

        nvec = self.get_embedding(" ".join(nouns), ngram_backoff=ngram_backoff, replace_unk=replace_unk)
        jvec = self.get_embedding(" ".join(adjs), ngram_backoff=ngram_backoff, replace_unk=replace_unk)

        return np.concatenate((nvec,jvec))

    def get_oov(self, name):
        name = re.sub(r"Type ([A-Z0-9]{2,3})",r"Type_\1",name)
        name = name.replace("non-","non_")
        if not name.isupper():
            name = name.lower()
        if name.replace(" ", "_") in self.word_vectors:
            return 0,0

        oovs = 0
        total = 0
        subs = re.split("[/,.;\- ]", name)
        for n in subs:
            n = n.strip()
            if len(n) == 0 or n in self.stopwords:
                continue

            if not n in self.word_vectors:
                oovs += 1
            total += 1

        return oovs, total

    def get_embedding(self, name, ngram_backoff=True, replace_unk=True):
        # if the whole phrase is also in the vocabulary, the phrase embeddings is also added to the list
       
        word_vec = np.zeros(len(self.word_vectors["in"]))
        ngram_vec = np.zeros(len(self.word_vectors["in"]))

        name = re.sub(r"Type ([A-Z0-9]{2,3})",r"Type_\1",name)
        name = name.replace("non-","non_")
        if not name.isupper():
            name = name.lower()

        if name.replace(" ", "_") in self.word_vectors:
            word_vec = self.normalize(self.word_vectors[name.replace(" ", "_")])

        oovs = 0
        subs = re.split("[/,.;\- ]", name)
        if np.sum(word_vec) == 0:
            for n in subs:
                n = n.strip()
                if len(n) == 0 or n in self.stopwords:
                    continue

                #print(n)
                normal_vec = np.zeros(len(self.unk_vec))
  
                if n in self.word_vectors:
                    normal_vec = self.normalize(self.word_vectors[n])
                    #print(np.sum(normal_vec))
                else:
                    #print("OOV",n)
                    oovs += 1
                    if replace_unk:
                        sub_vec = np.zeros(len(self.word_vectors["in"]))
                        ngrams = self.break_to_ngram(n, 3, 6)
                        for ngram in ngrams:
                            if ngram in self.word_vectors:
                                n_vec = self.normalize(self.word_vectors[ngram])
                                np.add(sub_vec, n_vec, sub_vec)

                        normal_vec = self.normalize(sub_vec)
           
                if np.sum(normal_vec) != 0:
                    np.add(word_vec, normal_vec, word_vec)

        #if a phrase has more than one missing words, do not back-off to ngrams of the phrase
        if oovs > int(len(subs)/2) or oovs > 3:
            word_vec = np.zeros(len(self.word_vectors["in"]))

        #print(oovs)
        if ngram_backoff:
            ngrams = []
            try:
                ngrams = self.break_to_ngram(name, 3, 6)
            except Exception:
                pass	
            for ngram in ngrams:
                if ngram in self.word_vectors:
                   n_vec = self.normalize(self.word_vectors[ngram])
                   np.add(ngram_vec, n_vec, ngram_vec)


        return self.normalize(word_vec),self.normalize(ngram_vec)


    '''
    writes the vectors for entities
    note that each concept can have multiple vectors (one for each lexicalization)
    also, if the entity is multiword and has an embedding, two embeddings will be created for it:
    (1) multiword embedding, (2) average of token embeddings
    '''
    def write_vecs(self, output_path, enhanced=False, ngram_backoff=True):
        counter = {}

        wcount = 0
        ccount = 0
        id2string_map = {}
        print("Starting to write vectors")
        with open(output_path.replace(".txt", ".words.txt"), 'w') as wofile, open(output_path.replace(".txt", ".ngrams.txt"), 'w') as cofile:
            for id in self.ontology.id2name.keys():
                for nm in self.ontology.id2name[id]:
                    name = self.process_name(nm)

                    if not enhanced:
                        w_emb, c_emb = self.get_embedding(name, replace_unk=self.include_unk)
                    else:
                        w_emb, c_emb = self.get_enhanced_embedding(name, replace_unk=self.include_unk)

                    if id not in counter:
                        counter[id] = 0
                    counter[id] += 1
                    if np.sum(w_emb) != 0:
                        wofile.write(id + "#" + str(counter[id]) + " " + " ".join(map(str, w_emb)) + "\n")
                        id2string_map[id + "#" + str(counter[id])] = name
                        wcount += 1
                        wsize = len(w_emb)
                    if np.sum(c_emb) != 0:
                        cofile.write(id + "#" + str(counter[id]) + " " + " ".join(map(str, c_emb)) + "\n")
                        id2string_map[id + "#" + str(counter[id])] = name
                        ccount += 1 
                        csize = len(c_emb)

        with open(output_path.replace(".txt", ".words.txt"), 'r+') as wofile:
            content = wofile.read()
            wofile.seek(0, 0)
            wofile.write(str(wcount)+" "+str(wsize) + '\n' + content)


        with open(output_path.replace(".txt", ".ngrams.txt"), 'r+') as wofile:
            content = wofile.read()
            wofile.seek(0, 0)
            wofile.write(str(ccount)+" "+str(csize) + '\n' + content)

        with open(output_path.replace(".txt", ".key.txt"), 'w') as hfile:
            for k in id2string_map:
                hfile.write(k + "\t" + id2string_map[k] + "\n")
  


if __name__ == "__main__":

    ### Generate semantic space for an ontology
    config = ProjectConfig()
    ontology = Ontology.PRO #Ontology.OMIM   #Ontology.SNOMED

    ne = namemb(base_embedding_path=config.base_embedding_path, ontology=ontology, load_ontologies=True)
    ne.write_vecs("embeddings/"+ontology.value+".v4.name.embedding.50d.txt")


    #ne = namemb(base_embedding_path=config.base_embedding_path, ontology=Ontology.HPO, load_ontologies=False)
    #print ne.get_embedding("Russian Long-Eared White pig")
    #print ne.get_embedding("Russian Long-Eared White pig breed")
