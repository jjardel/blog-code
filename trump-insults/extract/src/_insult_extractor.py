
# common-libs
from lw import get_logger, get_header, get_root_logger
from util import get_path

# third party modules
from bs4 import BeautifulSoup
from selenium import webdriver

import pandas as pd
import time


class InsultExtractor(object):

    def __init__(self):

        self.logger = get_logger(__name__)
        self.url = 'http://www.nytimes.com/interactive/2016/01/28/upshot/donald-trump-twitter-insults.html?smid=tw-upshotnyt&smtyp=cur'

    def extract(self):

        self.logger.info('Retreiving data from {0}'.format(self.url))
        driver = webdriver.PhantomJS(
            executable_path='/usr/local/bin/phantomjs-2.1.1-macosx/bin/phantomjs'  # why the F did I put it there?
        )

        driver.get(self.url)
        time.sleep(3)  # wait for the AJAX request

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        self.html = soup

    def export_to_csv(self, path):

        entities = self.html.find_all('div', class_='g-entity-item')

        self.logger.info('Parsing the HTML tree')
        df = pd.DataFrame(columns=['id', 'name', 'text', 'links'])
        for e in entities:
            element = e.find('div', class_='g-entity-name')

            e_name = element.contents
            e_id = element['id']

            insults = e.find('div', class_='g-insult-container').find_all('div', class_='g-insult-links-c')
            text = [x.a.contents for x in insults]
            links = [x.a['href'] for x in insults]

            # build a tmp data-frame
            tmp_df = pd.DataFrame(text, columns=['text'])
            tmp_df.loc[:, 'links'] = links
            tmp_df.loc[:, 'id'] = e_id
            tmp_df.loc[:, 'name'] = e_name

            df = df.append(tmp_df, ignore_index=True)

        # strip out tweet id
        regex = r'http[s]?\:\/\/twitter\.com\/.*\/status\/(\d.*)'
        df['tweet_id'] = df.links.str.extract(regex, expand=True)
        df.drop('links', axis=1, inplace=True)

        # write to csv
        df.to_csv(path)

        self.logger.info('Wrote results to {0}'.format(path))


if __name__ == '__main__':

    loc = get_path(__file__) + '/{0}'
    root_logger = get_root_logger()
    get_header(root_logger, "Extracting all of Trump's insults.  This may take a while...")

    insults = InsultExtractor()
    insults.extract()
    insults.export_to_csv(loc.format('../data/insults.csv'))