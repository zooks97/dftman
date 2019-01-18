import json

from pymatgen.io.pwscf import PWInput

from PWCalculation import PWCalculation
from MPQuery import MPQuery

def pseudo_helper(structure, pseudo_family, pseudo_table_path):
    with open(pseudo_table_path, 'r') as f:
        pseudo_table = json.load(f)
    
    pseudo_family_table = pseudo_table[pseudo_family]
    
    pseudos = []
    for site in structure.sites:
        specie = site.specie.symbol    
        pseudo = pseudo_family_table[specie]['filename']
        pseudos.append(pseudo)
    
    return pseudos

def pwinput_helper(structure, pseudo, control={}, system={},
                   electrons={}, ions={}, cell={}, kpoints_mode='automatic',
                   kpoints_grid=(1, 1, 1), kpoints_shift=(0, 0, 0)):
    if not control.get('calculation'):
        control['calculation'] = 'scf'
    if not control.get('restart_mode'):
        control['restart_mode'] = 'from_scratch'
    if control.get('outdir'):
        control['outdir'] = './' 
    if not control.get('prefix'):
        control['prefix'] = 'pwscf'
    if not control.get('disk_io'):
        if control['calculation'] == 'scf':
            control['disk_io'] = 'low'
        else:
            control['disk_io'] = 'medium'
    # Submit specific
    for key, value in {'title': 'pwscf',
                       'outdir': './',
                       'pseudo_dir': './'}.items():
        control[key] = value
    # Clean for pymatgen.io.pwscf.PWInput
    for key in ['nat', 'ntyp']:
        if system.get(key):
            del system[key]
            
    return PWInput(structure, pseudo, control, system,
                   electrons, ions, cell, kpoints_mode,
                   kpoints_grid, kpoints_shift)
    
def pwcalculation_helper(**kwargs):
    pwinput = pwinput_helper(**kwargs)
    return PWCalculation(pwinput)
    
def mpquery_helper(criteria, properties, API):
        required_properties = ['material_id', 'pretty_formula',
                               'elements', 'structure']
        if properties:
            properties += required_properties
        else:
            properties = required_properties
            
        mpquery = MPQuery(criteria, properties, API)
        return mpquery