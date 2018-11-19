The PheneBank Project
=====================

PheneBank aims at automatic extraction and validation of a database of human phenotype-disease associations in the
scientific literature. This package provides code, data, and models for the following three purposes:

## 1. Named Entity Recognition (Tagging)
The model is trained to support 9 categories of entities:
* Phenotype
* Disease 
* Anatomy
* Cell
* Cell_line
* GPR
* Gene_variant
* Molecule
* Pathway


## 2. Harmonisation (Grounding)

Map an entity to its corresponding concept in any of the following 5 ontologies:

* [SNOMED](https://www.snomed.org/snomed-ct) (Phenotype, Disease, GPR, Anatomy, Molecule, Cell, Cell_line, Gene_variant)
* [HPO](https://hpo.jax.org/app/) (Phenotype, Disease)
* [MESH](https://www.nlm.nih.gov/mesh/) (Phenotype, Disease)
* [FMA](http://si.washington.edu/projects/fma) (Anatomy)
* [PRO](https://www.ebi.ac.uk/ols/ontologies/pr) (GPR)


## 3. Tagging and Grounding
------------------------

Given an input text, extract its entities and map each to its corresponding concept in the ontologies (a pipeline containing both previous stages).



Online demo
============
* To be activated soon!

Data
====
Download the followings:
* [embeddings.zip](http://mws-02485.mws3.csx.cam.ac.uk/embeddings.zip) (around 1.1GB)
* [data.zip](http://mws-02485.mws3.csx.cam.ac.uk/) (around 200MB)


Getting Started:
================

To get started with the pipeline, first obtain the required ```data``` and decompress them in the project directory.
Then, import ```pipeline``` into your project:

```python
from pipeline import pipe
pp = pipe()
input_text = "Risk factors for recurrent respiratory infections in preschool children in China."
```

Find entities in an input text:
```python
pp.tag(input_text)
```

The output will look like the following (formatted for clarity). Lists of tuples, one tuple per sentence. Each tuple contains two lists: words and their corresponding tags.  
```
[
(['Risk', 'factors', 'for', 'recurrent', 'respiratory', 'infections', 'in', 'China.'],
['O', 'O', 'O', 'B-Phenotype', 'I-Phenotype', 'I-Phenotype', 'O', 'O'])
]
```

Find entities in the text and harmonise (map) them to their corresponding ontologies:

```python
pp.tag_harmonise(input_text)
```

The output will have each sentence as a list of tuples. Each tuple has three parts: word, tag (Null if not an entity), (the list of) corresponding concept IDs ([] if no mapping was found).
```
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
```

Updaing ontology embeddings:
============================

1. Place the new ontology file (eg, hp.obo) under the ```data``` directory.
2. Fix the corresponding path in ```utils/project_config.py```.
3. Use the ```ontology_embedding.py``` script under grounding to create a new semantic embedding.

You can use the following command in the "embeddings" directory to binarise the ontology embedding:

```cmd
$ ./convertvec txt2bin [embedding.txt] [embedding.bin]
```

(convertvec script from https://github.com/marekrei/convertvec)


Dependencies
============

The tagging stage relies on Anago, a Bidirectional LSTM-CRF for Sequence Labeling:
https://github.com/Hironsan/anago

