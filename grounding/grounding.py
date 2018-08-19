from __future__ import print_function
from gensim.models.keyedvectors import KeyedVectors
import sys
sys.path.append('..')
import ontology_embedding as ne
from ontology import hpo
from ontology import snomed
from ontology import fma
from ontology import pro
from ontology import fma
from ontology.ontologies import Ontology
from ontology import mesh
from utils.entity import EntityType
from utils.project_config import  ProjectConfig
import re
import warnings
import operator

warnings.simplefilter("error")

class grounding():

    config = ProjectConfig()

    def __init__(self, ontology_space_path=config.ontology_embedding_path, base_embedding_path=config.base_embedding_path, ontologies=[]):

        self.ontologies = ontologies

        if len(ontologies) == 0:
            self.ontologies = [Ontology.HPO, Ontology.SNOMED, Ontology.MESH, Ontology.FMA, Ontology.PRO]


        if Ontology.HPO in self.ontologies:
            self.hp = hpo.Ontology()
        if Ontology.SNOMED in self.ontologies:
            self.snmd = snomed.Ontology(prune=False)
        if Ontology.MESH in self.ontologies:
            self.msh = mesh.Ontology()
        if Ontology.FMA in self.ontologies:
            self.fma = fma.Ontology()
        if Ontology.PRO in self.ontologies:
            self.pro = pro.Ontology(human_filter=True)
        
        self.id2string_path = ontology_space_path.replace(".bin", ".key.txt")
        self.id2string = {}

        def get_dict(path):
            map = {}
            with open(path) as ifile:
                for line in ifile:
                    comps = line.strip().split("\t")
                    if len(comps) > 1:
                        map[comps[0]] = comps[1]
                    else:
                        map[comps[0]] = ""
            return map

        self.ngram_vectors = {}
        self.word_vectors = {}

        for ont in self.ontologies:
            this_path = ontology_space_path.replace('###', ont.value)
            print("Loading ontology vectors from", this_path.replace(".bin", ".words.bin"), "and", this_path.replace(".bin", ".ngrams.bin"))
            self.word_vectors[ont] = KeyedVectors.load_word2vec_format(this_path.replace(".bin", ".words.bin"), binary=True)
            self.ngram_vectors[ont] = KeyedVectors.load_word2vec_format(this_path.replace(".bin", ".ngrams.bin"), binary=True)
            print("vocab:", len(self.word_vectors[ont].vocab), len(self.ngram_vectors[ont].vocab))
            print("vector size:", self.word_vectors[ont].vector_size)
            self.id2string.update(get_dict(this_path.replace(".bin", ".key.txt")))

        self.word2index_map = {}

        print("[Vectors loaded!]")

        self.name_embedding = ne.namemb(base_embedding_path=base_embedding_path)

        self.factor = 0.5

        # if the word-based similarity is lower than this, it will back off to ngram similarity
        self.word_threshold = 0.9


    def get_ontologies(self, type, object=False):
        if type == EntityType.Phenotype or type == EntityType.Disease:
            if object:
                return self.get_ontology(["HP", "SCTID", "D"])
            return ["HP", "SCTID", "D"]

        elif type == EntityType.GPR:
            if object:
                return self.get_ontology(["PR", "SCTID"])
            return ["PR", "SCTID"]

        elif type == EntityType.Anatomy:
            if object:
                return self.get_ontology(["SCTID","fma"])
            return ["SCTID","fma"]

        elif type == EntityType.Molecule:
            if object:
                return self.get_ontology(["SCTID"])
            return ["SCTID"]

        elif type == EntityType.Cell:
            if object:
                return self.get_ontology(["SCTID"])
            return ["SCTID"]
        elif type == EntityType.Gene_variant or type == EntityType.Pathway:
            if object:
                return self.get_ontology(["SCTID"])
            return ["SCTID"]
        else:
            return None 


    def get_ontology(self, ids):
        onts = []
        for id in ids:
            if id.startswith("SCTID"):
                onts.append(self.snmd)
            elif id.startswith("HP"):
                onts.append(self.hp)
            elif re.match("^D[0-9]+", id):
                onts.append(self.msh)
            elif id.startswith("f"):
                onts.append(self.fma)
            elif id.startswith("P"):
                onts.append(self.pro)

        return onts


    def get_ontology_by_name(self, ids):
        out_onts = set()
        for id in ids:
            if id == Ontology.SNOMED:
                out_onts.add(self.snmd)
            elif id == Ontology.MESH:
                out_onts.add(self.msh)
            elif id == Ontology.HPO:
                out_onts.add(self.hp)
            elif id == Ontology.FMA:
                out_onts.add(self.fma)
            elif id == Ontology.PRO:
                out_onts.add(self.pro)
        return out_onts


    def length_effect(self, name, items):
        out_items = {}

        for item in items:
            title = self.id2string[item[0]]
            ratio = 2.0 * abs(len(name) - len(title)) / (len(name) + len(title))
            score = item[1] - ratio / 10
            out_items[item[0]] = score

        sorted_items = []
        for k in sorted(out_items.items(), reverse=True, key=operator.itemgetter(1)):
            sorted_items.append((k[0], k[1]))

        return sorted_items

    def filter_IDs(self, items, ID_set):
        filtered = []
        for item in items:
            id = item[0]
            for ont in ID_set:
                if id.startswith(ont):
                    filtered.append((item[0], item[1]))
        return filtered

    def get_alternatives(self, name):
        alternatives = [name.lower()]
        if re.match("[A-Z0-9]+ gene", name):
            alternatives.append(name.replace('gene','').strip())
        if re.match("[A-Z0-9]+ genes", name):
            alternatives.append(name.replace('genes','').strip())
        if re.match("[A-Z0-9]+ protein", name):
            alternatives.append(name.replace('protein','').strip())
        return alternatives

    def get_closests_match(self, name, type, restricted_ontologies=[], replace_unk=True, ngram_backoff=True, topn=3, alternatives=False):

        if len(restricted_ontologies) > 0:
            ontologies = self.get_ontology_by_name(restricted_ontologies)
        else:
            ontologies = self.get_ontologies(type, object=True)        

        ID_set = self.get_ontologies(type) 
        
        names = [name]
        if alternatives:
            names += self.get_alternatives(name)
        

        for nm in names:
            if ontologies is None:
                return []
            for ontology in ontologies:
                if nm in ontology.name2ID or nm.lower() in ontology.name2ID:
                    try:
                        fid = list(ontology.name2ID[nm])[0]
                    except:
                        fid = list(ontology.name2ID[nm.lower()])[0]
                    if len(ID_set) > 0:
                        for ids in ID_set:
                            if fid.startswith(ids):
                                return [(fid, 1.0)]
                    else:
                        return [(fid, 1.0)]

        if name.isupper():
            ngram_backoff = False

        wemb, cemb = self.name_embedding.get_embedding(name, replace_unk=replace_unk, ngram_backoff=ngram_backoff)

        results = self.get_candidates(name, self.word_vectors, wemb, topn, ID_set)

        oov, total = self.name_embedding.get_oov(name)
 

        if results[0][1] < self.word_threshold and ngram_backoff and oov > 0 and oov < 3 and (oov == 2 and total > 4):
            print(name)
            print(">",results)
            results2 = self.get_candidates(name, self.ngram_vectors, cemb, topn, ID_set)
            print(">>",results2)
            return results2
 
        return results 


    def get_candidates(self, name, vectors, emb, topn, ID_set):
        max = 0
        most_similars = []
        for ont in self.ontologies:
            if get_IDinit(ont) in ID_set:
                most_similars.extend(vectors[ont].similar_by_vector(emb, topn=10))
        most_similars = self.length_effect(name, most_similars)

        pruned_set = []
        done = 1
        for sim in most_similars:
            if done > topn:
                continue
            pruned_set.append((sim[0].split("#")[0], sim[1]))
            done += 1

        return pruned_set


def get_IDinit(name):
    if name == Ontology.SNOMED:
        return "SCTID"
    if name == Ontology.HPO:
        return "HP"
    if name == Ontology.MESH:
        return "D"
    if name == Ontology.FMA:
        return "f"
    if name == Ontology.PRO:
        return "P"


if __name__ == "__main__":

    #g = grounding(ontology_space_path='/home/pilehvar/taher/grounding-release/outputs/###.v3.name.embedding.50d.txt',
    #              base_embedding_path='/media/Data/taher-data/embeddings/PubMed-2016.fasttext.50d.vec.bin', ontologies=[Ontology.HPO])
    #print(g.get_closests_match("copper deficiency", EntityType.Phenotype, topn=10, restricted_ontologies=[Ontology.HPO]))
    #exit()

    config = ProjectConfig()
    g = grounding(ontology_space_path=config.ontology_embedding_path, ontologies=[Ontology.HPO, Ontology.SNOMED, Ontology.MESH],
                  base_embedding_path=config.base_embedding_path)

    while True:
        try:
            input = raw_input
        except NameError:
            pass
        inp = input("Phenotype: ")
        results = g.get_closests_match(inp, EntityType.Phenotype, ngram_backoff=True, restricted_ontologies=[Ontology.HPO], topn=5)
        for res in results:
            if res[0].startswith("HP"):
                print (res, g.hp.id2name[res[0]])
            if res[0].startswith("SCTID"):
                print (res, g.snmd.id2name[res[0]])
            

