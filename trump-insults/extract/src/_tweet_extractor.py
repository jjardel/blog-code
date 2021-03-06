from lw import get_logger
from util import get_path

# third party modules
import tweepy

from pandas import read_csv
from pandas.io.json import json_normalize
import json


class TweetExtractor(object):

    def __init__(self):

        self.loc = get_path(__file__) + '/../{0}'
        self.logger = get_logger(__name__)
        self._initialize_api()

    def _initialize_api(self):

        with open(self.loc.format('data/twitter_creds.json')) as fp:
            config = json.load(fp)

        auth = tweepy.OAuthHandler(config['consumer_token'], config['consumer_secret'])
        auth.set_access_token(config['access_token'], config['access_secret'])
        self.logger.info('Successfully Authenticated to Twitter API')

        self.api = tweepy.API(auth)

    def extract_insult_tweets(self):

        try:
            insults_df = read_csv(self.loc.format('data/insults.csv'))
        except FileNotFoundError:
            self.logger.critical('Insults file not found.  extract_insults.py must be run first')

        # get the schema of a Tweet
        tweets_df = json_normalize(self.api.get_status(insults_df.loc[0, 'tweet_id'])._json)
        tweets_df.drop(0, inplace=True)  # delete the data

        # build a DF of tweet data for each tweet in insults data
        # iterate in chunks so we can use twitter's GET statuses endpoint for bulk search

        n_insults = len(insults_df)
        chunksize = 100

        cursor = 0
        while cursor < n_insults:

            cursor_end_pos = min([cursor + chunksize - 1, n_insults - 1])
            self.logger.debug('Loading tweets {0}-{1}'.format(cursor, cursor_end_pos))

            tweet_ids = insults_df.ix[cursor: cursor_end_pos, 'tweet_id'].tolist()
            res = self.api.statuses_lookup(tweet_ids)
            for item in res:
                tweet = json_normalize(item._json)
                tweets_df = tweets_df.append(tweet)

            cursor += chunksize

        self.insult_tweets_df = tweets_df

    def extract_all_tweets(self, batch_size=200, num_tweets=4000):

        user = 'realdonaldtrump'
        res = []

        self.logger.info('Collecting the last {0} Trump tweets'.format(num_tweets))
        cursor = 0
        page = 1
        while cursor <= num_tweets:
            res += self.api.user_timeline(user, count=batch_size, page=page)
            page += 1
            cursor += batch_size

        # pick off the schema from the first tweet
        df = json_normalize(res[0]._json)
        df.drop(0, inplace=True)

        for tweet in res:
            df = df.append(json_normalize(tweet._json))

        self.all_tweets_df = df

    def export_to_csv(self, path_base):

        self.logger.info('Writing insult tweets to {0}'.format(path_base) + 'insult_tweets.csv')
        self.insult_tweets_df.to_csv(path_base + 'insult_tweets.csv')

        self.logger.info('Writing all tweets to {0}'.format(path_base) + 'all_tweets.csv')
        self.all_tweets_df.to_csv(path_base + 'all_tweets.csv')


if __name__ == '__main__':

    # for testing
    twex = TweetExtractor()
    twex.extract_insult_tweets()
