import os


def get_path(f):
    """
    get the fully specified path to a file
    """
    loc = os.path.abspath(os.path.dirname(f))
    return loc