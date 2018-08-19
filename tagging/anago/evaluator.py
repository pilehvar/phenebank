import os

from anago.models import SeqLabeling

from CRF.anago.data import F1score
from CRF.anago.data import batch_iter


class Evaluator(object):

    def __init__(self,
                 config,
                 weights,
                 save_path='',
                 preprocessor=None):

        self.config = config
        self.weights = weights
        self.save_path = save_path
        self.preprocessor = preprocessor

    def eval(self, x_test, y_test):

        # Prepare test data(steps, generator)
        train_steps, train_batches = batch_iter(
            list(zip(x_test, y_test)), self.config.batch_size, preprocessor=self.preprocessor)

        # Build the model
        model = SeqLabeling(self.config, ntags=len(self.preprocessor.vocab_tag))
        model.load(filepath=os.path.join(self.save_path, self.weights))

        # Build the evaluator and evaluate the model
        f1score = F1score(train_steps, train_batches, self.preprocessor)
        f1score.model = model
        f1score.on_epoch_end(epoch=-1)  # epoch takes any integer.
