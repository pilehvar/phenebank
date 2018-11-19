import os

class ProjectConfig(object):

    def __init__(self):
        """Sets the default model hyperparameters."""

        ##### Grounding

        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.base_embedding_path = project_path+'/embeddings/PubMed-2016.fasttext.50d.vec.bin'
        self.ontology_embedding_path = project_path+'/embeddings/###.v4.name.embedding.50d.bin'

        self.hpo_data_path = project_path+"/data/hp.obo"
        self.fma_data_path = project_path+"/data/FMA.csv"
        self.mesh_data_path = project_path+"/data/mesh-desc2017.xml"
        self.mesh_concepts = project_path+"/data/mappings/MeSH.tab"
        self.mesh_filtered_synsets = project_path+"/data/mappings/strictersynset.tab"
        self.pro_data_path = project_path+"/data/pro_reasoned.obo"
        self.omim_data_path = project_path+"/data/mimTitles.txt"

        #self.snomed_data_path = project_path+"/data/sct2_Description_Full-en_INT_20170131.modified.txt"
        self.snomed_data_path = project_path+"/data/sct2_Description_Full-en_INT_20180731.modified.txt"
        self.snomed_active_concepts = project_path+"/data/snomed_active.txt"
        self.snomed_filtered_branches = ["123037004","404684003","105590001","363787002","373873005","272379006","410607006"] #organisms was added by Taher
        self.snomed_filtered_concepts_path = project_path+"/data/snomed_categories.tab"



        ##### NER

        self.anago_models_dir = project_path+"/tagging/models/"
        self.anago_model = "model_weights.h5"
        self.phenebank_data_word_vocab = project_path + "/tagging/data/vocab_words.pkl"
        self.phenebank_data_char_vocab = project_path + "/tagging/data/vocab_chars.pkl"
        self.phenebank_data_tag_vocab = project_path + "/tagging/data/vocab_tags.pkl"
