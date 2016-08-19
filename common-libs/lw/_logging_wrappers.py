#!/home/jjardel/fb/pkgs/envs/etl/bin/python

import logging as lg
import datetime as dt

DEBUG = lg.DEBUG
INFO = lg.INFO
CRITICAL = lg.CRITICAL


def get_root_logger(console_verbosity=lg.DEBUG):
    """
    Get the top-level logger.

    :return: logger
    :rtype: lg.Logger
    """

    logger = lg.getLogger()
    logger.setLevel(lg.DEBUG)

    fmt = lg.Formatter('%(asctime)s - %(name)s - %(lineno)d -  %(levelname)s - %(message)s')

    # Stream handler
    strm_hndlr = lg.StreamHandler()
    strm_hndlr.setFormatter(fmt)
    strm_hndlr.setLevel(console_verbosity)

    logger.addHandler(strm_hndlr)

    return logger


def get_logger(namespace):
    """
    Get non top-level logger

    :param namespace: namespace of module
    :return: Logger
    """

    return lg.getLogger(namespace)


def get_header(logger, name):
    """Get a standard header for log files

    :param logger: Logger
    :type logger: lg.Logger
    :param name: Heading of log file
    :type name: str
    """

    logger.info('\n{0}'.format('*'*120))
    logger.info(name)
    logger.info('Today is: {0}'.format(dt.datetime.today().strftime('%c')))
    logger.info('\n{0}\n'.format('*'*120))