=====================
The PheneBank Project
=====================

PheneBank aims at automatic extraction and validation of a database of human phenotype-disease associations in the
scientific literature

This package provides code and data for

1. Named Entity Recognition (Tagging)
-------------------------------------

The model is trained to support 9 categories of entities:
Phenotype, Disease, Anatomy, Cell, Cell_line, GPR, Gene_variant, Molecule, Pathway


2. Harmonisation (Grounding)
----------------------------

Map an entity to its corresponding concept in any of the following 5 ontologies:

* SNOMED (Phenotype, Disease, GPR, Anatomy, Molecule, Cell, Cell_line, Gene_variant)
* HPO (Phenotype, Disease)
* MESH (Phenotype, Disease)
* FMA (Anatomy)
* PRO (GPR)


3. Tagging and Grounding
------------------------

Given an input text, extract its entities and map each to its corresponding concept in the ontologies.


For more information, please see: http://pilehvar.github.io/phenebank/

The tagging stage relies on Anago, a Bidirectional LSTM-CRF for Sequence Labeling:
https://github.com/Hironsan/anago


Getting Started:
================

To get started with the pipeline:

>>> from pipeline import pipe

>>> input_text = "Risk factors for recurrent respiratory infections in preschool children in China"

Find entities in an input text:

>>> pp.tag(input_text)

[
(['Risk', 'factors', 'for', 'recurrent', 'respiratory', 'infections', 'in', 'China.'],
['O', 'O', 'O', 'B-Phenotype', 'I-Phenotype', 'I-Phenotype', 'O', 'O'])
]

>>> pp.tag_harmonise(input_text)

[
[
('Risk', 'Null', []),
('factors', 'Null', []),
('for', 'Null', []),
('recurrent respiratory infections', 'Phenotype', [('HP:0002205', 1.0)]),
('in', 'Null', []),
('China', 'Null', [])
]
]


Updaing ontology embeddings:
============================

1. Place the new ontology file (eg, hp.obo) under the ontology/data directory.
2. Fix the corresponding path in utils/project_config.py.
3. Use the ontology_embedding.py script under grounding to create a new semantic embedding.

You can use the following command in the "embeddings" directory to binarise the ontology embedding:

$ ./convertvec txt2bin [embedding.txt] [embedding.bin]

(convertvec script from https://github.com/marekrei/convertvec)


