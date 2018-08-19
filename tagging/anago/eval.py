import os

from anago.config import ModelConfig
from anago.tagger import Tagger as tag

import anago
from CRF.anago.data import load_data_and_labels
from CRF.anago.data import prepare_preprocessor

DATA_ROOT = 'data/phenebank/'
train_path = os.path.join(DATA_ROOT, 'train.txt')

x_train, y_train = load_data_and_labels(train_path)

p = prepare_preprocessor(x_train, y_train)
model_config = ModelConfig()
SAVE_ROOT = './models'  # trained model
weights = 'model_weights.h5'
tagger = anago.Tagger(model_config, weights, save_path=SAVE_ROOT, preprocessor=p)

test_path = "data/phenebank/test.txt"

with open(test_path) as ifile:
    this_sentence = []
    all_sentences = []
    this_output = []
    all_outputs = []
    for line in ifile:
        line = line.strip()
        if len(line) == 0:
	    this_output = tag.predict(tag, this_sentence)
	    print this_sentence, this_output
	else:
   	    this_sentence.append(line.split("\t")[0])
