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

    name = 'omim'
    config = ProjectConfig()

    def __init__(self, file=config.omim_data_path):
        """ initializes the ontology instance by reading an obo_file """
        self.id2name = {}
        self.id2abbrv = {}
        self.name2ID = {}
        self.abbr2ID = {}
        self.abbreviations = {}

        self.parse_data(file)


    def parse_data(self, path):
        with open(path) as ifile:
            for line in ifile:
                if line.startswith("#"):
                    continue

                comps = line.strip().split("\t")

                if len(comps) > 1:
                    id = comps[1]
                    id = "OMIM:"+id

                    titles = set()
                    abbrvs = set()

                    for t in comps[2:]:
                        for d in t.split(";;"):
                            if ";" in d:
                                tcomps = d.split(";")
                                title = tcomps[0].strip()
                                titles.add(title)

                                for abbrv in tcomps[1:]:
                                    abbrv = abbrv.strip()
                                    abbrvs.add(abbrv)

                                if abbrv not in self.abbreviations:
                                    self.abbreviations[abbrv] = set()
                                self.abbreviations[abbrv].add(title)

                            else:
                                titles.add(d)

                    self.id2name[id] = titles

                    for title in titles:
                        if title not in self.name2ID:
                            self.name2ID[title] = set()

                        self.name2ID[title].add(id)

                    for abbrv in abbrvs:
                        if abbrv not in self.abbr2ID:
                            self.abbr2ID[abbrv] = set()

                        self.abbr2ID[abbrv].add(title)




if __name__ == "__main__":
    omim = Ontology()
    print(len(omim.id2name))
    print(omim.id2name["OMIM:102610"])
    print(omim.name2ID["ASMA"])

