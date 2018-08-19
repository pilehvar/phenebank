from __future__ import print_function
"""
PRO: the code is borrowed from HPO browser. It might contain many inconsistencies.
However, it satisfies the needs of this project: a ID2name mapping.
"""
import re   # regular expression module
import sys
sys.path.append('../..')
from utils.project_config import  ProjectConfig

class Ontology:
    """A class for an ontology instance to work with the HPO data """
    config = ProjectConfig()

    name = 'pro'
    def __init__(self, obo_file=config.pro_data_path, id_filter=[], human_filter=False):
        """ initializes the ontology instance by reading an obo_file """

        self.id_filter = id_filter

        # mapps each alternative ID to ist original ID
        self.alt2id = altID2ID(self, obo_file)

        # mapps each ID to its alternative IDs
        self.id2alt = ID2altID(self, obo_file)

        # mapps each term ID  to its parent(s)
        self.id2par = is_a_mapping(self, obo_file)

        # maps each term ID to its name:
        self.id2name = id2name(self, obo_file, human_filter=human_filter)

        # mapps each synonym and names to the termID
        self.name2ID = name_synonym2ID(self, obo_file)

        # maps each term ID to its child terms
        self.term2child = parse_top_down(self, obo_file, self.id2alt, self.alt2id)


    def collect_terms_to_root(self, termID, path=set()):
        """recursively collects all terms in the path to the root of the ontology by using the id2par dict """

        # check if term is the root (to stop recursion in that case)
        if not self.id2par[termID]:

            return path

        else:

            for par in self.id2par[termID]:

                # check if the path is already known:
                if par in self.id2root_path:

                    path.update(self.id2root_path[par])

                else:

                    path.add(par)

                    # add also alternative IDs for the parents if availabel
                    if par in self.id2alt:
                        path.update(self.id2par[par])

                    # recursively add rest of the path
                    path.update( self.collect_terms_to_root(par, path) )

        return path


def ldd_mapping(ldd2hpo_mapping_file):
    """
    returns a dictionary for LDD to HPO mapping.
    """

    ldd2hpo = {}

    for line in open(ldd2hpo_mapping_file):

        if not line.startswith("LNDB"):

            # read columns and strip semicolons
            sp = [col.strip('"') for col in line.strip('\n').split('\t')]

            # check mapping status in col 4
            if sp[4] != "no-mapping":
                hpo = sp[2]

                # include mapping terms:
                ldd2hpo[sp[1]] = set([hpo])

    return ldd2hpo

def is_a_mapping(self, obo_file):
    """ returns a dict with the mapping from each term to its parent """
    id2par = {}

    for line in open(obo_file):

        if line.startswith("[Typedef]"):
            break
        
        if line.startswith("id:"):

            if len(self.id_filter) > 0:
                flag = False
                for fid in self.id_filter:
                    if line.startswith("id: "+fid+":"):
                        flag = True
                        break

                if not flag:
                    continue

            id = re.findall('id: (.*?:.*?)\s', line)[0]
            # initialize empty set
            id2par[id] = set()

        elif line.startswith("is_a:"):
            if 'id' not in locals():
                continue

            par = re.findall('is_a: (.*?:.*?)\s', line)[0]
            # add parent term for id
            id2par[id].add(par)

    return id2par

def altID2ID(self, hpo_file):
    """
    returns a dictionary for alt_id to id mapping for the Human Pheontype Ontology (in .obo format)
    """
    alt2id = {}

    for line in open(hpo_file):

        if line.startswith("[Typedef]"):
            break

        if line.startswith("id:"):

            if len(self.id_filter) > 0:
                flag = False
                for fid in self.id_filter:
                    if line.startswith("id: " + fid + ":"):
                        flag = True
                        break

                if not flag:
                    continue

            id = re.findall('id: (.*?:.*?)\s', line)[0]


        if line.startswith("alt_id:"):

            if 'id' not in locals():
                continue

            alt_id = re.findall('alt_id: (.*?:.*?)\s', line)[0]

            if not alt_id in alt2id:
                alt2id[alt_id] = set()

            # add mapping
            alt2id[alt_id].add(id)

    return alt2id

def ID2altID(self, obo_file):
    """returns a dict {term_id:set(alt_id1, alt_id2, ...), ...}. """

    id2alt = {}

    for line in open(obo_file):

        if line.startswith("[Typedef]"):
            break

        if line.startswith("id:"):

            if len(self.id_filter) > 0:
                flag = False
                for fid in self.id_filter:
                    if line.startswith("id: " + fid + ":"):
                        flag = True
                        break

                if not flag:
                    continue

            id = re.findall('id: (.*?:.*?)\s', line)[0]

        elif line.startswith("alt_id:"):

            if 'id' not in locals():
                continue

            alt = re.findall('alt_id: (.*?:.*?)\s', line)[0]

            if id not in id2alt:
                id2alt[id] = set()

            id2alt[id].add(alt)

    return id2alt

def id2name(self, hpo_file, human_filter=False, add_human_alternative=True):
    """ returns a dict for the mapping from id to name"""
    id2name = {}

    pattern = re.compile("h[A-Z0-9]+")
    for line in open(hpo_file):

        if line.startswith("#"):
            continue

        if line.startswith("[Typedef]"):
            break

        if line.startswith("id:"):
            if len(self.id_filter) > 0:
                flag = False
                for fid in self.id_filter:
                    if line.startswith("id: " + fid + ":"):
                        flag = True
                        break

                if not flag:
                    continue

            id = re.findall('id: (.*?:.*?)\s', line)[0]

        if line.startswith("name:"):
            if 'id' not in locals():
                continue

            name = line.strip().split("name: ")[1]
            if human_filter:
                if "(human)" not in name:
                    continue

            if id not in id2name:
                id2name[id] = set()

            name = re.sub(r'\([^)]*\)', '', name)
            name = re.sub(r'\(.*\)', '', name) 
            id2name[id].add(name.strip())

            # to add alternatives such as RNA for hRNA which are human RNA 
            if add_human_alternative:
                if pattern.match(name):
                    id2name[id].add(name[1:]) 

        # synonsym tag:
        if line.startswith("synonym"):
            if 'id' not in locals():
                continue

            # find phenotype string by regular expression search
            syn_str = re.findall('^synonym: "(.*?)"', line)[0]

            if id in id2name:
                id2name[id].add(syn_str)
                if add_human_alternative:
                    if pattern.match(syn_str):
                        id2name[id].add(syn_str[1:])              

    return id2name


def get_frequencies(phrases):
    freqs = {}
    for phrase in phrases:
        for w in phrase.split(" "):
            if w not in freqs:
                freqs[w] = 0
            freqs[w] += 1
    return freqs


def name_synonym2ID(self, hpo_file, add_human_alternative=True):
    """
    returns a dictionary for each name or synonym tag, that mapps to its HPO term ID.
    """

    name2ID = {}
    pattern = re.compile("h[A-Z0-9]+")

    id = ""     # HPO term ID
    names = []  # list of names and synonyms that map to a given ID

    for line in open(hpo_file):

        if line.startswith("[Typedef]"):
            break

        # check if IDs are alreadsy readed:
        if line.startswith("[Term]") and id and names:

            if len(self.id_filter) > 0:
                flag = False
                for fid in self.id_filter:
                    if id.startswith(fid + ":"):
                        flag = True
                        break

                if not flag:
                    continue

            # update mapping with all readed names/synonyms
            if id in self.id2name:
                for name in names:
                    if not name in name2ID:
                        name2ID[name] = set()
                        if add_human_alternative:
                            if pattern.match(name):
                                name2ID[name[1:]] = set()
                    name2ID[name].add(id)
                    
                    if add_human_alternative:
                        if pattern.match(name):
                            name2ID[name[1:]].add(id)

            # delete names and id
            id = ""
            names = []

        # id tag:
        if line.startswith("id:"):

            if len(self.id_filter) > 0:
                flag = False
                for fid in self.id_filter:
                    if line.startswith("id: " + fid + ":"):
                        flag = True
                        break

                if not flag:
                    continue

            # grep for HPO term ID:
            id = re.findall('id: (.*?:.*?)\s', line)[0]

        # name tag:
        if line.startswith("name: "):
            if id != '':
                names.append(line.strip().split("name: ")[1])

        # synonsym tag:
        if line.startswith("synonym"):
            if id != '':
                # find phenotype string by regular expression search
                syn_str = re.findall('^synonym: "(.*?)"', line)[0]

                names.append(syn_str)

    # handle last entry:
    for name in names:
        if not name in name2ID:
            name2ID[name] = set()
        name2ID[name].add(id)
        if add_human_alternative:
            if pattern.match(name):
                name2ID[name[1:]].add(i)

    return name2ID

def gene2HPO(mapping_file):
    """
    parses the Entrez-Gene-ID to HPO mapping as dictionary.
    {'entrezID':[HPO_id1, HPO_id2 ...] }
    """
    gene2hpo = {}

    for line in open(mapping_file):

        if not line.startswith('#'):

            sp = line.strip().split('\t')
            # sp[0] is the EntrezID
            # sp[3] is the HPO ID

            if not gene2hpo.has_key(sp[0]):

                gene2hpo[sp[0]] = [sp[3]]

            else:

                gene2hpo[sp[0]].append(sp[3])

    return gene2hpo

def parse_top_down(self, obo_file, id2alt, alt2id):
    """
    returns a dict with the mapping to each direct child term.
    {"termID":[childID, childID, ...], term2ID:[...], ...}
    Takes alternative IDs of parents and children into account.
    """
    term2child = {}
    for line in open(obo_file):

        if line.startswith("[Typedef]"):
            break

        if line.startswith("id:"):

            if len(self.id_filter) > 0:
                flag = False
                for fid in self.id_filter:
                    if line.startswith("id: " + fid + ":"):
                        flag = True
                        break

                if not flag:
                    continue

            id = re.findall('id: (.*?:.*?)\s', line)[0]
            term_IDs = set([id])

            # add alternative IDs
            if id in id2alt:
                term_IDs.update(id2alt[id])

            # initialize empty sets for leaves
            for cID in term_IDs:
                if not cID in term2child:
                    term2child[cID] = set()

        if line.startswith("is_a:"):

            if 'term_IDs' not in locals():
                continue

            pID = re.findall('is_a: (.*?:.*?)\s', line)[0]
            parent_terms = set([pID])

            # get alternative ID for parent
            if pID in alt2id:
                parent_terms.update(alt2id[pID])
            if pID in id2alt:
                parent_terms.update(id2alt[pID])

            # update term2child dict with relations for all alternative combinations:
            for parent in parent_terms:

                for child in term_IDs:

                    if not parent in term2child:
                        term2child[parent] = set()

                    term2child[parent].add(child)

    return term2child


def gene2Uber(mapping_file):
    """
    parses the Entrez-Gene-ID to Uberpheno term mapping as dictionary.
    in the form {'entrezID':[UPO_id1, UPO_id2 ...] }
    from a file like e.g. HPO/crossSpeciesPheno_2_HSgenes.txt
    """
    gene2upo = {}

    for line in open(mapping_file):

        if not line.startswith('#'):

            sp = line.strip().split(';')

            # sp[0] contains the term ID
            # sp[2] is the EntrezID
            tID = sp[0]
            gene = sp[2].split(',')[0]

            if not gene2upo.has_key(gene):

                gene2upo[gene] = [tID]

            else:

                gene2upo[gene].append(tID)

    return gene2upo


def main():
    pro = Ontology(id_filter=['PR'], human_filter=True)
    print(len(pro.id2name))
    print(len(pro.name2ID))

    print(pro.id2name["PR:P04259"])
    print(len(pro.name2ID))
    print(len(pro.id2name))



if __name__ == "__main__":
    main()
