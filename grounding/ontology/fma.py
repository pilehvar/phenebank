from __future__ import print_function
"""
Use this to parse XML from MeSH (Medical Subject Headings). More information
on the format at: http://www.ncbi.nlm.nih.gov/mesh

End users will primarily want to call the `parse_mesh` function and do something
with the output.
"""
import sys
sys.path.append('../..')
from utils.project_config import ProjectConfig

class Ontology:

    name = 'fma'

    config = ProjectConfig()

    def __init__(self, file=config.fma_data_path):
        """ initializes the ontology instance by reading an obo_file """
        self.id2name = {}
        self.name2ID = {}

        self.parse_data(file)


    def parse_data(self, path):

        with open(path) as ifile:
            for line in ifile:
                if line.startswith("#"):
                    continue

                comps = line.strip().split(",")
                if len(comps) < 3:
                    continue
                id = comps[0].split("/")[-1]
                if 'fma' not in id:
                    continue

                title = comps[1]

                self.name2ID[title] = set([id])
                self.id2name[id] = set([title])

                for syn in comps[2].split("|"):
                    if len(syn) > 0 and len(id) > 0:
                        if syn not in self.name2ID:
                            self.name2ID[syn]= set()
                        self.name2ID[syn].add(id)
                        self.id2name[id].add(syn)


if __name__ == "__main__":
    fma = Ontology()

    print(fma.id2name["fma65470"])
    print(fma.name2ID["Anatomical line of large intestine"])
