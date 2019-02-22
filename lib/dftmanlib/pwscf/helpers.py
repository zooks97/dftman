from .pwscf import *

def pseudo_helper(structure, pseudo_family, pseudo_table_path):
    '''
    Helper function for constructing an appropriate pseudopotential
        dictionary for PWscf from a structure, pseudopotential family,
        and pseudopotential table
    :param structure: structure to find pseudopotentials for
    :type structure: pymatgen.core.Structure
    :param pseudo_family: pseudopotential family to use
    :type pseudo_family: str
    :param pseudo_table_path: path to a pseudopotential table in JSON
        format. The JSON should store a dictionary with the following
        structure:
            {'FAMILY1':
                {'ELEMENT_SYMBOL1': 'FILENAME1',
                 'ELEMENT_SYMBOL2': 'FILENAME2',
                 ...},
             'FAMILY2':
                {'ELEMENT_SYMBOL1': 'FILENAME1',
                 ...},
              ...
            }
        This represents the following directory structure:
        pseudo_dir/
            pseudo_table.json
            FAMILY1/
                FILENAME1
                FILENAME2
                ...
            FAMILY2/
                FILENAME1
                ...
            ...
    :type pseudo_table_path: str    
    '''
    if isinstance(structure, dict):
        structure = Structure.from_dict(structure)
    
    with open(pseudo_table_path, 'r') as f:
        pseudo_table = json.load(f)
    
    pseudo_family_table = pseudo_table[pseudo_family]
    
    species = {site.specie.symbol for site in structure.sites}
    pseudos = {specie: pseudo_family_table[specie]['path']
               for specie in species}
   
    return pseudos

def pwinput_helper(structure, pseudo, control={}, system={},
                   electrons={}, ions={}, cell={}, kpoints_mode='automatic',
                   kpoints_grid=(1, 1, 1), kpoints_shift=(0, 0, 0),
                   job_type=None):
    '''
    Helper function for constructing a PWInput object representing
        the input to a PWscf calculation
    See pymatgen.io.pwscf.PWInput for a description of the inputs
    :param job_type: Implemented: 'submit'
        Type of Job with which the PWInput is intened to run.
        This is used to do any special preparation necessary for certain
        types of jobs, like converting pseudopotential paths to pure
        file names for Submit jobs on nanoHUB
    :type job_type: str
    '''
    if isinstance(structure, dict):
        structure = Structure.from_dict(structure)
    
    if not control.get('calculation'):
        control['calculation'] = 'scf'
    if not control.get('restart_mode'):
        control['restart_mode'] = 'from_scratch'
    if control.get('outdir'):
        del control['outdir'] # = './' 
    if not control.get('prefix'):
        control['prefix'] = 'pwscf'
    if not control.get('disk_io'):
        if control['calculation'] == 'scf':
            control['disk_io'] = 'low'
        else:
            control['disk_io'] = 'medium'
    
    # QE requires pseudo_dir + pseudo file names
    for element in pseudo:
        pseudo_dir = pathlib.Path(pseudo[element]).parent
        pseudo[element] = pathlib.Path(pseudo[element]).name
        
    control['pseudo_dir'] = str(pseudo_dir)
    
    # Clean for pymatgen.io.pwscf.PWInput
    for key in ['nat', 'ntyp']:
        if system.get(key):
            del system[key]
    
    if job_type == 'submit':
        # Make pseudos appropriate for submit
        # Submit specific
        for key, value in {'prefix': 'pwscf',
                           'outdir': './',
                           'pseudo_dir': './'}.items():
            control[key] = value
        
    return PWInput(structure=structure, pseudo=pseudo,
                   control=control, system=system,
                   electrons=electrons, ions=ions, cell=cell,
                   kpoints_mode=kpoints_mode,
                   kpoints_grid=kpoints_grid,
                   kpoints_shift=kpoints_shift)
    
def pwcalculation_helper(**kwargs):
    '''
    Helper function for constructing a PWCalculation object
        representing a PWscf calculation's inputs and outputs
    See pymatgen.io.pwscf.PWInput for the majority of inputs.
    See dftmanlib.pwscf.helpers.pwinput_helper for DFTman specific inputs.
    :param additional_inputs: Additional inputs necessary for the calculation
        to run. Intended for listing pseudopotential files for Submit on
        nanoHUB
    '''
    if 'additional_inputs' in kwargs:
        additional_inputs = kwargs.pop('additional_inputs')
    else:
        additional_inputs = []
    pwinput = pwinput_helper(**kwargs)
    pwoutput = PWOutput()
    return PWCalculation(pwinput, output=pwoutput,
                         additional_inputs=additional_inputs)