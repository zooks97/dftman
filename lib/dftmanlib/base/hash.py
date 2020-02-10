# TODO: rename hash to uuid
import hashlib
from collections import OrderedDict

def sort_recursive(var0):
    '''
    Sort a dictionary recursively into a nested
        set of tuples which is relatively deterministic
        and good for hashing uniquely
    :param var0: dictionary to sort recursivley
    :return: nested structure of sorted tuples
    '''
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
    '''
    Hash function for DFTman
    :param bytes_: bytes to hash
    :return: 32-byte blake2b hex hash digest
    '''
    blake2b_hash = hashlib.blake2b(digest_size=32, salt=b'htdft')
    blake2b_hash.update(bytes_)
    return str(blake2b_hash.hexdigest())

def hash_dict(dict_):
    '''
    Hash a dictionary relatively determinstically
        by sorting it recursively (using sort_recursive)
        then hashing it using blake2b (using dftman_hash)
    :param dict_: dictionary to hash
    :return: 32-byte blake2b hex hash digest from dftma_hash
    '''
    sorted_dict = sort_recursive(dict_)
    hash_bytes = bytes(str(sorted_dict).encode())
    return dftman_hash(hash_bytes)