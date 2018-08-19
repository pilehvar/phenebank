"""
HPO import script for serveral tasks
"""
import re,sys   # regular expression module
sys.path.append('../..')
from utils import project_config

class Ontology:
    """A class for an ontology instance to work with the HPO data """

    name = 'hpo'
    IDinit = 'HP'

    config = project_config.ProjectConfig()

    def __init__(self, obo_file=config.hpo_data_path):
        """ initializes the ontology instance by reading an obo_file """
        print("Loading HP ontology...")

        # mapps each alternative ID to ist original ID
        self.alt2id = altID2ID(obo_file)

        # mapps each ID to its alternative IDs
        self.id2alt = ID2altID(obo_file)

        # mapps each term ID  to its parent(s)
        self.id2par = is_a_mapping(obo_file)

        # maps each term ID to its name:
        self.id2name = id2name(obo_file)

        # mapps each synonym and names to the termID
        self.name2ID = name_synonym2ID(obo_file)

        # maps each term ID to its child terms
        self.term2child = parse_top_down(obo_file, self.id2alt, self.alt2id)

        # initialiize id2root_path dict, that maps each term to its set of terms in the path to the root
        self.id2root_path = {}

        self.word_freqs = get_frequencies(self.name2ID.keys())

        # calculate for each term the path to root
        for termID in self.id2par.keys():

            self.id2root_path[termID] = self.collect_terms_to_root(termID, set([termID]) )

        # initialize dict that maps each term to all its descendants
        self.id2descendants = {}

        for termID in self.id2par.keys():

            # get alternative IDs if available:
            alt_set = set([termID])
            if termID in self.id2alt:
                alt_set.update(self.id2alt[termID])

            # for each term in the path to root
            for pID in self.id2root_path[termID]:

                if not pID in self.id2descendants:
                    self.id2descendants[pID] = set()

                self.id2descendants[pID].update(alt_set)


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

    with open(ldd2hpo_mapping_file) as ifile:
        for line in ifile:

            if not line.startswith("LNDB"):

                # read columns and strip semicolons
                sp = [col.strip('"') for col in line.strip('\n').split('\t')]

                # check mapping status in col 4
                if sp[4] != "no-mapping":
                    hpo = sp[2]

                    # include mapping terms:
                    ldd2hpo[sp[1]] = set([hpo])

    return ldd2hpo

def is_a_mapping(obo_file):
    """ returns a dict with the mapping from each term to its parent """
    id2par = {}

    with open(obo_file) as ifile:
        for line in ifile:

            if line.startswith("id:"):

                id = re.findall('id: (.*?:.*?)\s', line)[0]
                # initialize empty set
                id2par[id] = set()

            elif line.startswith("is_a:"):

                par = re.findall('is_a: (.*?:.*?)\s', line)[0]
                # add parent term for id
                id2par[id].add(par)

    return id2par

def altID2ID(hpo_file):
    """
    returns a dictionary for alt_id to id mapping for the Human Pheontype Ontology (in .obo format)
    """
    alt2id = {}

    with open(hpo_file) as ifile:
        for line in ifile:
            if line.startswith("id:"):

                id = re.findall('id: (.*?:.*?)\s', line)[0]

            if line.startswith("alt_id:"):

                alt_id = re.findall('alt_id: (.*?:.*?)\s', line)[0]

                if not alt_id in alt2id:
                    alt2id[alt_id] = set()

                # add mapping
                alt2id[alt_id].add(id)

    return alt2id

def ID2altID(obo_file):
    """returns a dict {term_id:set(alt_id1, alt_id2, ...), ...}. """

    id2alt = {}

    with open(obo_file) as ifile:
        for line in ifile:

            if line.startswith("id:"):

                id = re.findall('id: (.*?:.*?)\s', line)[0]

            elif line.startswith("alt_id:"):

                alt = re.findall('alt_id: (.*?:.*?)\s', line)[0]

                if id not in id2alt:
                    id2alt[id] = set()

                id2alt[id].add(alt)

    return id2alt

def id2name(hpo_file):
    """ returns a dict for the mapping from id to name"""
    id2name = {}

    with open(hpo_file) as ifile:
        for line in ifile:

            if line.startswith("id:"):
                id = re.findall('id: (.*?:.*?)\s', line)[0]
            if line.startswith("name:"):
                name = line.strip().split("name: ")[1]
                if id not in id2name:
                    id2name[id] = set()

                id2name[id].add(name)

            # synonsym tag:
            if line.startswith("synonym:"):
                # find phenotype string by regular expression search
                syn_str = re.findall('^synonym: "(.*?)"', line)[0]

                id2name[id].add(syn_str)

    return id2name


def get_frequencies(phrases):
    freqs = {}
    for phrase in phrases:
        for w in phrase.split(" "):
            if w not in freqs:
                freqs[w] = 0
            freqs[w] += 1
    return freqs


def name_synonym2ID(hpo_file):
    """
    returns a dictionary for each name or synonym tag, that mapps to its HPO term ID.
    """

    name2ID = {}

    id = ""     # HPO term ID
    names = []  # list of names and synonyms that map to a given ID

    with open(hpo_file) as ifile:
        for line in ifile:

            # check if IDs are alreadsy readed:
            if line.startswith("[Term]") and id and names:

                # update mapping with all readed names/synonyms
                for name in names:
                    if not name.lower() in name2ID:
                        name2ID[name.lower()] = set()
                    name2ID[name.lower()].add(id)

                # delete names and id
                id = ""
                names = []


            # id tag:
            if line.startswith("id:"):

                # grep for HPO term ID:
                id = re.findall('id: (.*?:.*?)\s', line)[0]

            # name tag:
            if line.startswith("name: "):

                names.append(line.strip().split("name: ")[1])

            # synonsym tag:
            if line.startswith("synonym:"):
                # find phenotype string by regular expression search
                syn_str = re.findall('^synonym: "(.*?)"', line)[0]

                names.append(syn_str)

    # handle last entry:
    for name in names:
        if not name.lower() in name2ID:
            name2ID[name.lower()] = set()
        name2ID[name.lower()].add(id)

    return name2ID

def gene2HPO(mapping_file):
    """
    parses the Entrez-Gene-ID to HPO mapping as dictionary.
    {'entrezID':[HPO_id1, HPO_id2 ...] }
    """
    gene2hpo = {}

    with open(mapping_file) as ifile:
        for line in ifile:

            if not line.startswith('#'):

                sp = line.strip().split('\t')
                # sp[0] is the EntrezID
                # sp[3] is the HPO ID

                if not gene2hpo.has_key(sp[0]):

                    gene2hpo[sp[0]] = [sp[3]]

                else:

                    gene2hpo[sp[0]].append(sp[3])

    return gene2hpo

def parse_top_down(obo_file, id2alt, alt2id):
    """
    returns a dict with the mapping to each direct child term.
    {"termID":[childID, childID, ...], term2ID:[...], ...}
    Takes alternative IDs of parents and children into account.
    """
    term2child = {}
    with open(obo_file) as ifile:
        for line in ifile:

            if line.startswith("id:"):
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

    with open(mapping_file) as ifile:
        for line in ifile:

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
    hpo = Ontology()

    print(hpo.id2name["HP:0004941"])
    print(len(hpo.name2ID))
    print(len(hpo.id2name))



if __name__ == "__main__":
    main()
