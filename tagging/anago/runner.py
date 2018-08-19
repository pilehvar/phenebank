import os

from anago.config import ModelConfig, TrainingConfig

import anago
from CRF.anago.data import load_data_and_labels, load_word_embeddings
from CRF.anago.data import prepare_preprocessor

DATA_ROOT = 'data/conll2003/en/tagging'
SAVE_ROOT = './models'  # trained model
LOG_ROOT = './logs'     # checkpoint, tensorboard
embedding_path = '/home/pilehvar/taher/embeddings/glove.6B.100d.txt'
model_config = ModelConfig()
training_config = TrainingConfig()


train_path = os.path.join(DATA_ROOT, 'train.txt')
valid_path = os.path.join(DATA_ROOT, 'valid.txt')
test_path = os.path.join(DATA_ROOT, 'test.txt')
x_train, y_train = load_data_and_labels(train_path)
x_valid, y_valid = load_data_and_labels(valid_path)
x_test, y_test = load_data_and_labels(test_path)


p = prepare_preprocessor(x_train, y_train)
embeddings = load_word_embeddings(p.vocab_word, embedding_path, model_config.word_embedding_size)
model_config.vocab_size = len(p.vocab_word)
model_config.char_vocab_size = len(p.vocab_char)

trainer = anago.Trainer(model_config, training_config, checkpoint_path=LOG_ROOT, save_path=SAVE_ROOT,
                        preprocessor=p, embeddings=embeddings)
trainer.train(x_train, y_train, x_valid, y_valid)

