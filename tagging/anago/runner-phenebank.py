import os
import anago
from anago.data.reader import load_data_and_labels, load_word_embeddings
from anago.data.preprocess import prepare_preprocessor
from anago.config import ModelConfig, TrainingConfig

#DATA_ROOT = 'data/phenebank/'
DATA_ROOT = 'data/phenebank/original/'
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

def evaluate():
   test_path = "data/phenebank/original/test.txt"
   #out_path = "data/phenebank/test.out"
   out_path = "data/phenebank/test.out"


   #weights = 'model_weights.h5'
   weights = 'model_weights.h5'
   tagger = anago.Tagger(model_config, weights, save_path=SAVE_ROOT, preprocessor=p)

   with open(test_path) as ifile:
      this_sentence = []
      this_gold = []
      all_gold = []
      all_sentences = []
      this_output = []
      all_outputs = []
      for line in ifile:
          line = line.strip()
          if len(line) == 0:
              if len(this_sentence) == 0:
                  continue
              this_output = tagger.predict(this_sentence)
              all_outputs.append(this_output)
              all_gold.append(this_gold)
              this_sentence = []
              this_gold = []
              this_output = []
          else:
              this_sentence.append(line.split("\t")[0])
	      this_gold.append(line.split("\t")[1])

   with open(out_path, 'w') as ofile:
       for i, g in enumerate(all_gold):
           for j, gi in enumerate(g):
               ofile.write(gi+"\t"+all_outputs[i][j]+"\n")

#trainer = anago.Trainer(model_config, training_config, checkpoint_path=LOG_ROOT, save_path=SAVE_ROOT, preprocessor=p, embeddings=embeddings)
#trainer.train(x_train, y_train, x_valid, y_valid)

evaluate()
