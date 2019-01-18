from pymatgen import Structure
from pymatgen.io.pwscf import PWInput as PWInputPMG

class PWInput(PWInputPMG):
    '''
    Subclass of pymatgen's PWInput which adds:
        * PWInput.as_dict() for storing a PWInput object as a dictionary
        * PWInput.from_dict(pwinput_dict) for restoring a PWInput object from a dictionary
    :param structure: pymatgen Structure object
    :param pseudo: pseudopotential dictionary where keys are elements / species
        and values are the paths to the pseudopotentials for writing in the pw.x input
    :param control: dictionary of the parameters in the CONTROL card of pw.x
    :param system: dictionary of the parameters in the SYSTEM card of pw.x
    :param electrons: dictionary of the parameters in the ELECTRONS card of pw.x
    :param ions: dictionary of the parameters in the IONS card of pw.x
    :param cell: dictionary of the parameters in the CELL card of pw.x
    :param kpoints_mode: string of the type of kpoints to be provided
    :param kpoints_grid: tuple of kpoints in the b1, b2, and b3 directions
    :param kpoints_shift: tuple of kpoints offset along b1, b2, and b3 directions
    '''
    def __init__(self, structure, pseudo, control={}, system={},
                 electrons={}, ions={}, cell={}, kpoints_mode="automatic",
                 kpoints_grid=(1, 1, 1), kpoints_shift=(0, 0, 0)):

        self.pseudo = pseudo      
        self.structure = structure
        self.sections = {'control': control,
                         'system': system,
                         'electrons': electrons,
                         'ions': ions,
                         'cell': cell}
        
        self.pseudo = pseudo
        self.kpoints_mode = kpoints_mode
        self.kpoints_grid = kpoints_grid
        self.kpoints_shift = kpoints_shift
                
        super(PWInput, self).__init__(self.structure, self.pseudo,
                self.sections['control'], self.sections['system'],
                self.sections['electrons'], self.sections['ions'], self.sections['cell'],
                self.kpoints_mode, self.kpoints_grid, self.kpoints_shift)
        return

    def __repr__(self):
        return str(self)
        
    def as_dict(self):
        dict_ = {'structure': self.structure.as_dict(),
                 'pseudo': self.pseudo,
                 'sections': self.sections,
                 'kpoints_mode': self.kpoints_mode,
                 'kpoints_grid': self.kpoints_grid,
                 'kpoints_shift': self.kpoints_shift}
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        return cls(structure=Structure.from_dict(dict_['structure']),
                   pseudo=dict_['pseudo'],
                   control=dict_['sections']['control'],
                   system=dict_['sections']['system'],
                   electrons=dict_['sections']['electrons'],
                   ions=dict_['sections']['ions'],
                   cell=dict_['sections']['cell'],
                   kpoints_mode=dict_['kpoints_mode'],
                   kpoints_grid=dict_['kpoints_grid'],
                   kpoints_shift=dict_['kpoints_shift'])
