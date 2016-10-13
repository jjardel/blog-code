#!/home/jjardel/fb/pkgs/envs/etl/bin/python

from lw import get_logger
from sqlalchemy import create_engine
from pandas import read_sql_table

import json


class DBConn(object):

    def __init__(self, config_path):

        self.logger = get_logger(__name__)
        self.config_path = config_path
        self._load_credentials()
        self._create_engine()

    def _load_credentials(self):
        """
        load DB connection parameters from local enviornment variables
        :return: None
        """

        with open(self.config_path) as fp:
            config = json.load(fp)

        self.db_server = config['db_server']
        self.db_pass = config['db_pass']
        self.db_user = config['db_user']
        self.db_name = config['db_name']

        self.logger.info('Credentials loaded for DB connection')

    def _create_engine(self, flavor='postgresql', port='5432'):

        uri = '{0}://{1}:{2}@{3}:{4}/{5}'.format(flavor,
                                             self.db_user,
                                             self.db_pass,
                                             self.db_server,
                                             port,
                                             self.db_name)

        self.engine = create_engine(uri)

    def load(self, df, table, schema='public', if_exists='fail'):

        # convert column names to lowercase
        df.rename(columns=lambda x: x.lower(), inplace=True)

        # load to DB
        df.to_sql(table, self.engine, schema=schema, if_exists=if_exists, index=False)
        self.logger.info('Successfully loaded {0} lines into {1}.{2}'.format(len(df), schema, table))

    def export(self, table, schema='public', index_col=None):

        self.logger.info('Executing SELECT * FROM {0}.{1}'.format(schema, table))
        df = read_sql_table(table, self.engine, schema=schema, index_col=index_col)

        self.logger.info('Retreived {0} rows from table'.format(len(df)))

        return df
