from enum import Enum

class EntityType(Enum):
    Phenotype = "Phenotype"
    Disease = "Disease"
    GPR = "GPR"
    Anatomy = "Anatomy"
    Molecule = "Molecule"
    Cell_line = "Cell_line"
    Cell = "Cell"
    Gene_variant = "Gene_variant"
    Pathway = "Pathway"
    Null = "O"

    @staticmethod
    def get_type(e):
        return EntityType(e)
