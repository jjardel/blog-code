from util import get_path
from lw import get_logger, get_root_logger, get_header

import pandas as pd


class TweetAnalysis(object):

    def __init__(self):

        self.loc = get_path(__file__) + '/../{0}'
        self.logger = get_logger(__name__)

    def load_data(self):
        # load tweets & insult data

        self.insults = pd.read_csv(self.loc.format('../extract/data/insults.csv'))
        self.insult_tweets = pd.read_csv(self.loc.format('../extract/data/insult_tweets.csv'))
        self.all_tweets = pd.read_csv(self.loc.format('../extract/data/all_tweets.csv'))

    def transform(self):

        # filter by device
        for df in [self.insult_tweets, self.all_tweets]:
            # regex to pick out device
            device = df.source.str.extract(r'\<a .*\>(.*)\<\/a\>')

            column_map = {
                "Twitter for Android": "android",
                "Twitter Web Client": "web",
                "Twitter for iPhone": "iphone",
                "Twitter for BlackBerry": "blackberry"
            }

            df['device'] = device.apply(
                lambda x: column_map[x] if x in column_map.keys() else 'NULL'
            )

            df.ix[df.device == 'android', 'trump'] = 1
            df.ix[df.device == 'iphone', 'campaign'] = 1

            df.fillna(0, inplace=True)

        insult_tweets = pd.merge(
            self.insults,
            self.insult_tweets,
            left_on='tweet_id',
            right_on='id',
            how='inner'
        ).loc[:, ['name', 'text_x', 'id_x', 'trump', 'campaign', 'created_at']].drop_duplicates()

        # index by time
        insult_tweets['created_at'] = pd.to_datetime(insult_tweets['created_at'])
        insult_tweets.set_index('created_at', inplace=True)

        # resample to daily + take rolling 7-day avg
        insult_tweets = insult_tweets.resample('D').sum()
        insult_tweets_avg = insult_tweets.rolling(window=7, min_periods=1).mean()

        




        print('break')



if __name__ == '__main__':

    logger = get_root_logger()
    logger = get_header(logger, 'Running Tweet Analysis')

    ta = TweetAnalysis()
    ta.load_data()
    ta.transform()