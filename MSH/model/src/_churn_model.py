
# python standard packages
from collections import defaultdict

# my common_libs code
from common_libs.lw import get_header, get_root_logger, get_logger
from common_libs.db_conn import DBConn
from common_libs.util import get_path

# 3rd party packages
from lazy_property import LazyProperty
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split

import numpy as np

class ChurnModel(object):
    """
    docs go here
    """

    def __init__(self):

        self.logger = get_logger(__name__)
        self.loc = get_path(__file__) + '/{0}'

        self.table = 'clean.customer_attributes'  # bring this into constructor args if needed

        # metadata about features/labels
        self.categorical_vars = ['x2', 'x3', 'x4', 'x5']
        self.numerical_vars = ['days_since_signup', 'x1', 'x6', 'x7', 'x8']
        self.label_var = 'status'

    @LazyProperty
    def data(self):

        self.logger.info('Retreiving data from {table}'.format(table=self.table))
        schema, table = self.table.split('.')

        conn = DBConn(self.loc.format('../../credentials.json'))
        data = conn.export(table, schema=schema, index_col='customer_id')

        return data

    def _custom_preprocessing(self):
        """
        Rransformations that happen outside of sklearn's Pipeline go here
        e.g. label encoding, one-hot encoding

        :return: X (n x m) matrix of features
        :rtype: ndarray
        :return y vector of length n containing labels
        :rtype ndarray
        """

        raw_data = self.data

        # map categorical variables (and labels) to integers, and save the mappings
        self.label_encodings = defaultdict(LabelEncoder)

        # apply a LabelEncoder to all categorical vars + the category labels
        labels_df = raw_data[self.categorical_vars + [self.label_var]].\
            apply(lambda x: self.label_encodings[x.name].fit_transform(x))

        raw_data.update(labels_df)

        # apply a one-hot encoding transformation to the categorical features
        self.one_hot_encoding = OneHotEncoder()
        X_cat = self.one_hot_encoding.fit_transform(raw_data[self.categorical_vars]).toarray()

        # stack categorical + numerical features
        X_num = raw_data[self.numerical_vars].values
        X = np.hstack((X_cat, X_num))

        y = raw_data[self.label_var].values

        return X, y

    def train(self):

        X, y = self._custom_preprocessing()

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)



        print("breakpoint")













if __name__ == '__main__':

    logger = get_root_logger()
    _ = get_header(logger, 'Building a model to predict customer retention')
    model = ChurnModel()

    model.train()

    print('breakpoint for testing')