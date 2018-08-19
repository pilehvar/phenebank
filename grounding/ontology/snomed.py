from __future__ import print_function
import re
import sys

sys.path.append('../..')
from utils.project_config import ProjectConfig

"""
Use this to parse XML from MeSH (Medical Subject Headings). More information
on the format at: http://www.ncbi.nlm.nih.gov/mesh

End users will primarily want to call the `parse_mesh` function and do something
with the output.
"""

class Ontology:

    name = 'snomed'
    IDinit = 'SCTID'

    def __init__(self, remove_parentheses=True, keep_only=[], discard_stop_concepts=True, prune=False):
        self.id2name = {}
        self.name2ID = {}

        config = ProjectConfig()
        file = config.snomed_data_path
 
        self.active_IDs = self.get_active_IDs(config.snomed_active_concepts)
        if prune:
            keeps = config.snomed_filtered_branches
            self.keepIDs = self.get_keep_IDs(config.snomed_filtered_concepts_path, keeps)

        self.parse_data(file, remove_parentheses=True, keep_only=keep_only, discard_inactive=discard_stop_concepts, prune=prune)

    def get_keep_IDs(self, path, keeps):
       keepIDs = set() 
       with open(path) as ifile:
            for line in ifile:
                comps = line.strip().split("\t")
                if comps[0] in keeps:
                   keepIDs.add(comps[2])
       return keepIDs

    
    def get_active_IDs(self, path):
        id_set = set()
        with open(path) as ifile:
            for line in ifile:
                id_set.add(line.strip())
        return id_set


    def in_stoplist(self, title):
        if title.startswith("[x]") \
                or title.startswith("[d]") \
                or title.startswith("h/o") \
                or title.startswith("o/e") \
                or title.startswith("c/o") \
                or title.startswith("on examination -") \
                or title.startswith("history of -") \
                or title == "or" \
                or title == "or or" \
                or title == "or or or" \
                or title == "and"\
                or len(title) == 0:
            return True
        else:
            return False


    def parse_data(self, path, discard_inactive, remove_parentheses=True, keep_only=[], prune=False):
        sys.stdout.write("Loading Snomed ")

        lcounter = 0
        sys.stdout.write("%s" % (" " * 12))
        sys.stdout.flush()
        sys.stdout.write("\b" * (11+1))

        with open(path) as ifile:
            for line in ifile:
                if line.startswith("#"):
                    continue

                flag = True
                if len(keep_only) > 0:
                    flag = False
                    for ko in keep_only:
                        if "("+ko+")" in line:
                            flag = True
                            break

                if not flag:
                    continue

                comps = line.strip().split("\t")

                lcounter += 1
                if lcounter % 200000 == 0:
                    sys.stdout.write("#")
                    sys.stdout.flush()

                if prune:
                    #if the lexicalization is inactive
                    if comps[1] == "0":
                        continue
                    if comps[2] not in self.keepIDs:
                        continue

                title = re.sub(r'\([^)]*\)', '', comps[3]).strip()
                title = re.sub(r'\(.*\)', '', title).strip()
                title = re.sub(r'\)', '', title).strip()
                title = re.sub(r'\(', '', title).strip()
                #title = re.sub(r'[a-z]\/[a-z] -','', title).strip()
                title = ' '.join(title.split())

                if discard_inactive:
                    if comps[2] not in self.active_IDs:                   
                        continue
                    if not self.in_stoplist(title):
                        self.name2ID[title] = set()
                        self.id2name["SCTID:" + comps[2]] = set()


        with open(path) as ifile:
            lcounter = 1
            for line in ifile:
                if line.startswith("#"):
                    continue

                flag = True
                if len(keep_only) > 0:
                    flag = False
                    for ko in keep_only:
                        if "(" + ko + ")" in line:
                            flag = True
                            break

                if not flag:
                    continue

                comps = line.strip().split("\t")

                if len(comps) > 1:
                    id = comps[2]
                    
                    if prune:
                        #if the lexicalization is inactive
                        if comps[1] == "0":
                            continue
                        if id not in self.keepIDs:
                            continue

                    id = "SCTID:"+id

                    title = comps[3].strip()
                    if remove_parentheses:
                        title = re.sub(r'\([^)]*\)', '', title).strip()
                        title = re.sub(r'\(.*\)', '', title).strip()
                        title = re.sub(r'\)', '', title).strip()
                        title = re.sub(r'\(', '', title).strip()
			#title = re.sub(r'[a-z]\/[a-z] -','', title).strip()
                        title = ' '.join(title.split())

                    if discard_inactive:
                        if id.split("SCTID:")[1] not in self.active_IDs:
                            continue
                        if not self.in_stoplist(title):
                            self.name2ID[title].add(id)
                            self.id2name[id].add(title)

                        if not title.lower() in self.name2ID:
                            self.name2ID[title.lower()] = set()
                            self.name2ID[title.lower()].add(id)

                    lcounter += 1
                    if lcounter % 200000 == 0:
                        sys.stdout.write("#")
                        sys.stdout.flush()
        print("")
     

if __name__ == "__main__":
    #snomed = Ontology(keep_only=["disorder"])
    config = ProjectConfig()
    snomed = Ontology(config, prune=False)
    print ("Size of id2name:",len(snomed.id2name))
    print ("Size of name2id:",len(snomed.name2ID))

    print(snomed.id2name["SCTID:132105001"])
    print(snomed.id2name["SCTID:19030005"])
    print(snomed.id2name["SCTID:89293008"])
    print( snomed.name2ID["HIV-1"])
    print( snomed.name2ID["chondrodysplasia punctata"])
    print(len(snomed.id2name.keys()))
    print(len(snomed.name2ID.keys()))
