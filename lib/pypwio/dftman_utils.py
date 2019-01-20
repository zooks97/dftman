import json
import pathlib
import subprocess

import pandas as pd

from pymatgen.io.pwscf import PWInput

from PWCalculation import PWCalculation
from MPQuery import MPQuery

def pseudo_helper(structure, pseudo_family, pseudo_table_path):
    with open(pseudo_table_path, 'r') as f:
        pseudo_table = json.load(f)
    
    pseudo_family_table = pseudo_table[pseudo_family]
    
    species = {site.specie.symbol for site in structure.sites}
    pseudos = {specie: pseudo_family_table[specie]['path'] for specie in species}
   
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
    for key, value in {'prefix': 'pwscf',
                       'outdir': './',
                       'pseudo_dir': './'}.items():
        control[key] = value
    # Clean for pymatgen.io.pwscf.PWInput
    for key in ['nat', 'ntyp']:
        if system.get(key):
            del system[key]
    # Make pseudos appropriate for submit
    for element in pseudo:
        pseudo[element] = pathlib.Path(pseudo[element]).name
        
    return PWInput(structure, pseudo, control, system,
                   electrons, ions, cell, kpoints_mode,
                   kpoints_grid, kpoints_shift)
    
def pwcalculation_helper(**kwargs):
    if 'additional_inputs' in kwargs:
        additional_inputs = kwargs.pop('additional_inputs')
    pwinput = pwinput_helper(**kwargs)
    return PWCalculation(pwinput, additional_inputs=additional_inputs)
    
def mpquery_helper(criteria, properties, API):
        required_properties = ['material_id', 'pretty_formula',
                               'elements', 'structure']
        if properties:
            properties += required_properties
        else:
            properties = required_properties
            
        mpquery = MPQuery(criteria, properties, API)
        return mpquery
    
def submit_status():
    status_text = subprocess.check_output(['submit', '--status']).decode('utf-8').strip()
    
    nruns = len(status_text) - 1 if len(status_text) else 0
    if nruns:
        status_dicts = []
        statuses = status_text.split('\n')[1:]
        for status in statuses:
            status = status.strip().split()
            status_dict = {
                'runname': status[0],
                'id': int(status[1]),
                'instance': int(status[2]),
                'status': status[3],
                'location': status[4]
            }
            status_dicts.append(status_dict)
        status_df = pd.DataFrame(status_dicts).set_index('id')
    else:
        status_df = pd.DataFrame([])
    
    return status_df
    