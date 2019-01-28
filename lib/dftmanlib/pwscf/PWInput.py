from pymatgen.io.pwscf import PWInput as PWInputPMG

import persistent

from .__init__ import hash_dict

class PWInput(persistent.Persistent, PWInputPMG):
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
    
    def write_input(self, filename):
        self.write_file(filename)