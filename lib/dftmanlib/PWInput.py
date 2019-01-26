import hashlib

from collections import OrderedDict

from pymatgen.io.pwscf import PWInput as PWInputPMG

# TODO: figure out where sort_recursive and hash_dict should _actually_ go

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

def hash_dict(dict_):
    sorted_dict = sort_recursive(dict_)
    hash_string = bytes(str(sorted_dict).encode())
    sha256_hash = hashlib.sha256()
    sha256_hash.update(hash_string)
    return sha256_hash.hexdigest()[:6]


class PWInput(PWInputPMG):
    '''
    Subclass of pymatgen's PWInput which adds:
        * PWInput.as_dict() for storing a PWInput object as a dictionary
        * PWInput.from_dict(pwinput_dict) for restoring a PWInput object
              from a dictionary
    :param structure: pymatgen Structure object
    :param pseudo: pseudopotential dictionary where keys are elements / species
        and values are the paths to the pseudopotentials for writing in the
        pw.x input
    :param control: dictionary of the parameters in the CONTROL card of pw.x
    :param system: dictionary of the parameters in the SYSTEM card of pw.x
    :param electrons: dictionary of the parameters in the ELECTRONS card of pw.x
    :param ions: dictionary of the parameters in the IONS card of pw.x
    :param cell: dictionary of the parameters in the CELL card of pw.x
    :param kpoints_mode: string of the type of kpoints to be provided
    :param kpoints_grid: tuple of kpoints in the b1, b2, and b3 directions
    :param kpoints_shift: tuple of kpoints offset along b1, b2, and b3 directions
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def key(self):
        return hash_dict(self.as_dict())