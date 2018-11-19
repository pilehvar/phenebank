from __future__ import print_function
import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.getcwd())
from tagging.anago import tagger as tgger
from grounding import grounding
import tagging.abbreviations
from nltk import word_tokenize, sent_tokenize
from utils.entity import EntityType
from tagging.anago.config import ModelConfig
from utils.project_config import ProjectConfig
from tagging.anago.data.preprocess import WordPreprocessor

import pickle

class pipe():

    def __init__(self):
        config = ProjectConfig()

        self.gnd = grounding.grounding()
        p = WordPreprocessor()

        with open(config.phenebank_data_tag_vocab, 'rb') as handle:
            p.vocab_tag = pickle.load(handle)

        with open(config.phenebank_data_word_vocab, 'rb') as handle:
            p.vocab_word = pickle.load(handle)

        with open(config.phenebank_data_char_vocab, 'rb') as handle:
            p.vocab_char = pickle.load(handle)

        model_config = ModelConfig()
        model_config.vocab_size = len(p.vocab_word)
        model_config.char_vocab_size = len(p.vocab_char)

        self.main_anago_tagger = tgger.Tagger(model_config, config.anago_model, save_path=config.anago_models_dir, preprocessor=p)


    def get_abbrevs(self, inp):
        try:     
            return tagging.abbreviations.get_abbrevs(inp)
        except:
            return []

    def phrase_it(self, inputs):
        outputs = []

        for input in inputs:
            out_tokens = []
            out_predicted = []

            current_pred = []
            current_tok = []

            tokens = input[0]
            preds = input[1]

            for i, p in enumerate(preds):
                predicted = preds[i]
                token = tokens[i]

                if len(predicted) == 0:
                    out_tokens.append('')
                    out_predicted.append('')
                if predicted.startswith("O"):
                    if len(current_tok) == 0:
                        out_tokens.append(token)
                        out_predicted.append(predicted)
                    else:
                        out_tokens.append(" ".join(current_tok))
                        out_predicted.append(current_pred[0].split("-")[1])
                        current_pred = []
                        current_gold = []
                        current_tok = []
                        out_tokens.append(token)
                        out_predicted.append(predicted)

                if predicted.startswith("B"):
                    if len(current_tok) == 0:
                        current_tok.append(token)
                        current_pred.append(predicted)
                    else:
                        out_tokens.append(" ".join(current_tok))
                        out_predicted.append(current_pred[0].split("-")[1])
                        current_pred = []
                        current_tok = []
                        current_tok.append(token)
                        current_pred.append(predicted)

                if predicted.startswith("I"):
                    current_tok.append(token)
                    current_pred.append(predicted)

            if len(current_tok) > 0:
                out_tokens.append(" ".join(current_tok))
                out_predicted.append(current_pred[0].split("-")[1])

            outputs.append((out_tokens, out_predicted))

        return outputs


    def tag(self, input_text, skip_nl=False):
        tokenized_input = []
        for sent in sent_tokenize(input_text):
            tokenized_input.append(word_tokenize(sent))

        res = self.tag_anago(tokenized_input, skip_nl=skip_nl)
        return res


    def tag_anago(self, tokenized_sents, skip_nl=True):

        y_preds = []
        if len(tokenized_sents) == 0 or len(tokenized_sents[0]) < 2:
            return y_preds

        for sent in tokenized_sents:
            predictions = self.main_anago_tagger.predict(sent)
            y_preds.append((sent, predictions))

        return y_preds


    def ground_it(self, word, type, topn=1, enhanced=True, keep_id=False):
        return self.gnd.get_closests_match(word, type, topn=topn, keep_id=keep_id)


    def tag_harmonise(self, a):

        if len(a.strip().split(" ")) < 2:
            return {}

        abbreviations = self.get_abbrevs(a)
        paragraphs = [p for p in a.split('\n')]

        ais = []
        for paragraph in paragraphs:
            ais.append(" ".join(word_tokenize(paragraph)))

        lstm_reses = []
        for ai in ais:
            lstm_o = self.tag(ai)
            lstm_reses.append(self.phrase_it(lstm_o))

        outss = []
        for lstm_res in lstm_reses:
            outs =[]
            for r in lstm_res:
                for i, w in enumerate(r[0]):
                    tg = str(r[1][i])
                    if tg is not "O":
                        tag = EntityType.get_type(tg)

                        if w in abbreviations:
                            closest = self.ground_it(abbreviations.get(w), tag)
                        else:
                            closest = self.ground_it(w, tag)

                        outs.append((w, tag.name, closest))

                    else:
                        outs.append((str(w),"O","NA"))
            outss.append(outs)

        return outss


if __name__ == '__main__':

    pp = pipe()

    output = pp.tag("Risk factors for recurrent respiratory infections in preschool children in China.\n Oculomotor apraxia (OMA) associated with cerebellar ataxia was first noted by Boder and Sedgwick.")
    for sentence in output:
        words, tags = sentence
        for w,t in zip(words, tags):
            print(w,"\t",t)


    print("\n")
    output = pp.tag_harmonise("Risk factors for recurrent respiratory infections in preschool children in China.\n Oculomotor apraxia (OMA) associated with cerebellar ataxia was first noted by Boder and Sedgwick.")
    for sentence in output:
        for word in sentence:
            if word[1] == 'Null':
                continue
            print(word)
