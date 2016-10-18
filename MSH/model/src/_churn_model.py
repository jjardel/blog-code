
# python standard packages
from collections import defaultdict
from pandas import DataFrame, get_dummies
import pickle
import numpy as np
import json
from copy import deepcopy


# my common_libs code
from common_libs.lw import get_header, get_root_logger, get_logger
from common_libs.db_conn import DBConn
from common_libs.util import get_path

from ._util import CustomJSONEncoder

# 3rd party packages
from lazy_property import LazyProperty
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, Imputer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, roc_curve
import matplotlib.pyplot as plt

RANDOM_STATE = 42  # the answer is 42


class ChurnModel(object):
    """
    Model customer status based on a table of masked attributes.
    Find which features are important in the classification.
    """

    def __init__(self, data_table):
        """

        :param data_table:  Name of database table where data is stored
        :type data_table: str
        """

        self.logger = get_logger(__name__)
        self.loc = get_path(__file__) + '/../{0}'

        self.table = data_table

        # metadata about features/labels
        self.categorical_vars = ['x2', 'x3', 'x4', 'x5']
        self.numerical_vars = ['x1', 'x6', 'x7', 'x8']
        self.label_var = 'status'
        self.cols_to_drop = ['signup_date', 'cancel_date', 'days_since_signup']

    @LazyProperty
    def data(self):

        self.logger.info('Retreiving data from {table}'.format(table=self.table))
        schema, table = self.table.split('.')

        self.conn = DBConn(self.loc.format('../credentials.json'))
        data = self.conn.export(table, schema=schema, index_col='customer_id')

        return data

    def _custom_preprocessing(self):
        """
        Transformations that happen outside of sklearn's Pipeline go here
        (e.g. label encoding, one-hot encoding).  Output is tranformed feature/label vectors

        :return: X (n x m) matrix of features
        :rtype: ndarray
        :return y vector of length n containing labels
        :rtype ndarray
        """

        raw_data = deepcopy(self.data)

        # binarize labels
        y = raw_data['status'].apply(lambda x: 1 if x == 'canceled' else 0).values
        raw_data.drop('status', axis=1, inplace=True)

        # 1-hot encoding
        self.data_processed = get_dummies(raw_data)
        self.label_encodings = {
            1: 'canceled',
            0: 'active'
        }
        self.label_encodings_inv = {
            'canceled': 1,
            'active': 0
        }

        # drop unwanted columns
        self.data_processed.drop(self.cols_to_drop, axis=1, inplace=True)
        X = self.data_processed.values

        return X, y

    def _save_model(self):

        with open(self.loc.format('output/model.pkl'), 'wb') as fp:
            pickle.dump(self.model, fp)

    def _evaluate(self, x_train, x_test, y_train, y_test):

        self.logger.info('Evalulating model fit from held out data')

        preds = self.model.predict(x_test)
        pred_scores = self.model.predict_proba(x_test)

        self.logger.info(classification_report(y_test,
                                               preds,
                                               target_names=['active', 'canceled']
        ))

        fpr, tpr, _ = roc_curve(y_test,
                                pred_scores[:, self.label_encodings_inv['canceled']],
                                pos_label=self.label_encodings_inv['canceled']
        )

        auc = roc_auc_score(y_test, pred_scores[:, self.label_encodings_inv['canceled']])
        self.logger.info('ROC AUC= %0.2f' % auc)

        # plot ROC curve
        plt.clf()
        plt.plot(fpr, tpr, 'r', label='ROC curve (area= %0.2f)' % auc)
        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.legend(loc='lower right')
        plt.savefig(self.loc.format('output/roc_curve.png'))

    def train(self):

        X, y = self._custom_preprocessing()

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

        p = Pipeline([
            ('impute_missing_vals', Imputer(strategy='median')),
            ('random_forest', RandomForestClassifier(random_state=RANDOM_STATE))

        ])

        # set hyperparameter ranges for CV
        n_trees = np.logspace(2, 3.3, dtype=int, num=5)
        max_features = ['auto', 'log2', None]
        max_depth = list(np.logspace(0.7, 1.5, dtype=int, num=4)) + [None]
        min_samples_split = [1, 5, 10, 20]
        min_samples_leaf = [1, 5, 10, 20]

        params = {
            'random_forest__n_estimators': n_trees,
            'random_forest__max_features': max_features,
            'random_forest__max_depth': max_depth,
            'random_forest__min_samples_split': min_samples_split,
            'random_forest__min_samples_leaf': min_samples_leaf

        }

        k_folds = 3

        # initialize grid search for model hyperparameters using a grid search
        self.logger.info('Tuning model hyperparameters with Cross Validation')
        n_combs = k_folds
        for k, v in params.items():
            n_combs *= len(v)

        self.logger.info('{0} combinations to be tried'.format(n_combs))

        gs = GridSearchCV(p, params, cv=k_folds, scoring='roc_auc', n_jobs=-1, verbose=1)
        gs.fit(X_train, y_train)

        self.model = gs.best_estimator_
        self.logger.info('Best model parameters: {0}'.format(gs.best_params_))

        # load CV results into DB for analysis/logging
        cv_df = DataFrame(gs.cv_results_)

        # some type conversions... sklearn uses some types that are not JSON serializable
        cv_df = cv_df.apply(lambda x: x.astype(object))
        cv_df.params = cv_df.params.apply(lambda x: json.dumps(x, cls=CustomJSONEncoder))

        self.logger.info("Loading CV results into model.cv_results table")
        self.conn.load(cv_df, 'cv_results', schema='model', if_exists='replace')

        self._evaluate(X_train, X_test, y_train, y_test)

        self._save_model()

    def predict(self):

        if not self.model:
            raise AttributeError("no trained model found.  Either run the train method, or pass a pre-trained modedl")

        # apply all the same transformations to the full data set
        x, y = self._custom_preprocessing()

        preds = self.model.predict(x)
        pred_probs = self.model.predict_proba(x)

        # load predicted labels + class probabilities into DB
        self.data.loc[:, 'predicted_status'] = [self.label_encodings[x] for x in preds]

        self.data.loc[:, 'prob_cancel'] = pred_probs[:, self.label_encodings_inv['canceled']]
        self.data.loc[:, 'prob_active'] = pred_probs[:, self.label_encodings_inv['active']]

        self.logger.info('Loading prediction scores and probabilities into model.results')
        self.conn.load(self.data, 'results', 'model', if_exists='replace', index=True)

        print("breakpoint")

    def load_saved_model(self, model_path):
        """
        Rather than re-train, load a pickled model that was previously trained

        :param model_path:  path to model file
        :type: str
        """

        with open(self.loc.format(model_path), 'rb') as fp:
            self.model = pickle.load(fp)

        self.logger.info('Loaded pre-trained model at {0}'.format(model_path))


if __name__ == '__main__':

    logger = get_root_logger()
    _ = get_header(logger, 'Testing.....')
    model = ChurnModel()

    model.train()

    print('breakpoint for testing')