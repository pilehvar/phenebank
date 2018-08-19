from utils.project_config import  ProjectConfig

class mapper():
    config = ProjectConfig()

    mesh2umls = {}
    omim2umls = {}
    umls_lexicalizations = {}

    def set_mesh2umls(self, file=config.mesh_concepts):
        print("Setting MeSH to UMLS mappings")
        with open(file) as ifile:
            for line in ifile:
                umlsid, meshid = line.strip().split("\t")
                if meshid not in self.mesh2umls:
                    self.mesh2umls[meshid.strip()] = set()

                self.mesh2umls[meshid.strip()].add(umlsid.strip())


    def get_mesh2umls(self, meshid):
        if len(self.mesh2umls) == 0:
            self.set_mesh2umls()

        if meshid not in self.mesh2umls.keys():
            return set()
        else:
            return self.mesh2umls[meshid]


    def set_umls_lexicalisations(self, restrict_to = [], file=config.mesh_filtered_synsets, discard_commas=True):
        print("Setting UMLS lexicalizations")
        if restrict_to != None:
            print("... restricted to a set of", len(restrict_to), "items")

        counter = 0
        with open(file) as ifile:
            for line in ifile:
                umlsid, lex = line.strip().split("\t")
                if discard_commas:
                    if "," in lex:
                        continue

                print(counter)

                if len(restrict_to) > 0:
                    if umlsid not in restrict_to:
                        continue

                counter += 1

                if umlsid not in self.umls_lexicalizations:
                    self.umls_lexicalizations[umlsid.strip()] = set()

                self.umls_lexicalizations[umlsid.strip()].add(lex.strip())

    def get_umls_lexicalizations(self, id, restrict_to):
        if len(self.umls_lexicalizations) == 0:
            self.set_umls_lexicalisations(restrict_to=restrict_to)

        if id not in self.umls_lexicalizations.keys():
            return set()
        else:
            return self.umls_lexicalizations[id]





