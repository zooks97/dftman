import json
import pathlib
import subprocess
import copy
import hashlib
import os

from collections import OrderedDict

import ZODB
import ZODB.FileStorage
import BTrees.OOBTree
import transaction

import pandas as pd

from pymatgen import Structure
from IPython.display import clear_output

# from PWInput import PWInput
# from PWCalculation import PWCalculation
# from MPQuery import MPQuery
# from SubmitJob import SubmitJob
from . import PWInput
from . import PWCalculation
from . import MPQuery
from . import SubmitJob

def pseudo_helper(structure, pseudo_family, pseudo_table_path):
    if isinstance(structure, dict):
        structure = Structure.from_dict(structure)
    
    with open(pseudo_table_path, 'r') as f:
        pseudo_table = json.load(f)
    
    pseudo_family_table = pseudo_table[pseudo_family]
    
    species = {site.specie.symbol for site in structure.sites}
    pseudos = {specie: pseudo_family_table[specie]['path'] for specie in species}
   
    return pseudos

def pwinput_helper(structure, pseudo, control={}, system={},
                   electrons={}, ions={}, cell={}, kpoints_mode='automatic',
                   kpoints_grid=(1, 1, 1), kpoints_shift=(0, 0, 0)):
    if isinstance(structure, dict):
        structure = Structure.from_dict(structure)
    
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
        
    return PWInput(structure=structure, pseudo=pseudo,
                   control=control, system=system,
                   electrons=electrons, ions=ions, cell=cell,
                   kpoints_mode=kpoints_mode,
                   kpoints_grid=kpoints_grid,
                   kpoints_shift=kpoints_shift)
    
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
            
        mpquery = MPQuery(criteria, sorted(properties), API)
        return mpquery
    
def submit_status():
    status_text = subprocess.check_output(['submit', '--status']).decode('utf-8').strip()
    
    nruns = len(status_text) - 1 if len(status_text) else 0
    if nruns:
        status_dicts = []
        statuses = status_text.strip().split('\n')[1:]
        for status in statuses:
            status = status.strip().split()
            status_dict = {
                'Run Name': status[0],
                'ID': int(status[1]),
                'Instance': int(status[2]),
                'Status': status[3],
                'Location': status[4]
            }
            status_dicts.append(status_dict)
        status_df = pd.DataFrame(status_dicts).set_index('ID')
        status_df = status_df[['Run Name', 'Status', 'Instance', 'Location']]
    else:
        status_df = pd.DataFrame([])
    return status_df

def job_statuses(jobs):
    status_dicts = []
    for job in jobs:
        status_dicts.append({'Run Name': job.runname,
                             'ID': job.id,
                             'Status': job.check_status(),
                             'Location': job.location,
                             'Submission Time': job.submission_time,
                             'Key': job.key})
        df = pd.DataFrame(status_dicts).set_index('Run Name')
        clear_output()
        display(df[['ID', 'Status', 'Location', 'Submission Time', 'Key']])

def init_db(path='./db.fs'):
    if not os.path.exists(path):
        root = load_db(path)
        root.MPQueries = BTrees.OOBTree.BTree()
        # root.PWInputs = BTrees.OOBTree.BTree()
        # root.PWOutputs = BTrees.OOBTree.BTree()
        # root.PWCalculations = BTrees.OOBTree.BTree()
        root.SubmitJobs = BTrees.OOBTree.BTree()
        transaction.commit()
    else:
        print('This database already exists! Loading instead.')
        root = load_db(path)
    return root

def load_db(path='./db.fs'):
    storage = ZODB.FileStorage.FileStorage('db.fs')
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root
    return root

def db_store(object_, root, report=True, overwrite=False):
    if isinstance(object_, SubmitJob):
        tree = root.SubmitJobs
    elif isinstance(object_, MPQuery):
        tree = root.MPQueries
    else:
        raise ValueError('This is an unsupported object.'\
                         ' The database only accepts'\
                         ' SubmitJob and MPQuery.')
    key = object_.key
    if not overwrite and key in list(tree.keys()):
        raise ValueError('This key already exists!'\
                         ' Use the overwrite argument to'
                         ' overwrite the entry.')
    else:
        tree[key] = object_
        transaction.commit()
        print('Added {} to the database'.format(key))
    return key

