import json
import numpy as np


class CustomJSONEncoder(json.JSONEncoder):
    """
    Needed because sklearn uses lots of objects with numpy.int64 data types
    """

    def default(self, o):

        if isinstance(o, np.int64):
            return int(o)
