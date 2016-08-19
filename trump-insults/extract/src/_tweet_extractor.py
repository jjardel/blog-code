from lw import get_logger
from util import get_path

# third party modules
import tweepy

import pandas as pd
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

        self.api = tweepy.API(auth)

    def load(self):

        pass






if __name__ == '__main__':

    twex = TweetExtractor()