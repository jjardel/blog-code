from MSH.model import ChurnModel

from common_libs.lw import get_header, get_root_logger, DEBUG
from common_libs.util import get_path


def main():

    model = ChurnModel('clean.customer_attributes_clipped')
    model.train()
    model.predict()

if __name__ == '__main__':

    loc = get_path(__file__) + '/{0}'
    lg = get_root_logger(filename=loc.format('log/log.log'), console_verbosity=DEBUG)
    _ = get_header(lg, name='Building a model to predict customer retention')

    main()
