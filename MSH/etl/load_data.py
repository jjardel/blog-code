from common_libs.db_conn import DBConn
from common_libs.lw import get_root_logger, get_header

import os
from pandas import read_csv


def main():

    MSH = os.getenv('MSH') + '/{0}'

    conn = DBConn(MSH.format('credentials.json'))
    df = read_csv(MSH.format('data/data-science-project.csv'))

    conn.load(df, 'customer_attributes', schema='raw', if_exists='replace')

if __name__ == '__main__':
    logger = get_root_logger()
    get_header(logger, 'Loading data into DB')

    main()

