from lw import get_logger, get_header, get_root_logger

import argparse

from src import TweetExtractor


def main(path):

    twex = TweetExtractor()
    twex.extract_insult_tweets()
    twex.extract_all_tweets()
    twex.export_to_csv(path)


if __name__ == '__main__':

    root_logger = get_root_logger()
    get_header(root_logger, "Extracting all of Trump's insulting Tweets. Lucky Me...")

    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, help='where would you like to extract_insult_tweets to?')

    args = parser.parse_args()

    main(args.path)