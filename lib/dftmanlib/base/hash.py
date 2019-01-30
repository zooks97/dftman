import hashlib
from collections import OrderedDict

def sort_recursive(var0):
    sorted_ = OrderedDict()
    if isinstance(var0, dict):
        for key, value in sorted(var0.items()):
            sorted_[key] = sort_recursive(value)
    elif isinstance(var0, (list, set, tuple)):
        new_var0 = [sort_recursive(item) for item in var0]
        return tuple(new_var0)
    else:
        return var0
    return sorted_

def dftman_hash(bytes_):
    blake2b_hash = hashlib.blake2b(digest_size=6, salt=b'htdft')
    blake2b_hash.update(bytes_)
    return str(blake2b_hash.hexdigest())

def hash_dict(dict_):
    sorted_dict = sort_recursive(dict_)
    hash_bytes = bytes(str(sorted_dict).encode())
    return dftman_hash(hash_bytes)