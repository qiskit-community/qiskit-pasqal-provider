"""set some global behaviors during tests"""

import numpy as np

# set reproducibility
np.random.seed(42)

NUM_ATOMS = 12
ATOM_ORDER = tuple(f"q{k}" for k in range(0, NUM_ATOMS))


def _gen_dict_result() -> dict:
    """generate a dictionary result"""
    _res = {}
    _res[np.binary_repr(9, NUM_ATOMS)] = 50
    _res[np.binary_repr(11, NUM_ATOMS)] = 25
    return _res


DEFAULT_DICT_RESULT = _gen_dict_result()
