import sys
import qgrid
import copy

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.path.append('../../lib/')
from dftmanlib.pwscf import (pwinput_helper,
                             pwcalculation_helper,
                             pseudo_helper)
from dftmanlib.pwscf.workflow import EOSWorkflow
from dftmanlib.job import SubmitJob, submitjob_statuses, submit_status
from dftmanlib.matproj import mpquery_helper
from dftmanlib.db import init_db, load_db

import tinydb

PSEUDO_TABLE = '/home/azadoks/.local/share/pseudo/pseudo_table.json'
PSEUDO_FAMILY = 'GBRV_US_PBE'
MP_API_KEY = '0WqdPfXxloze6T9N'
# qgrid.enable()

db = load_db()

criteria = {
    'elements': 'Al',
    'nsites': 1,
    'spacegroup.number': 225,
}
properties = []
m = mpquery_helper(criteria, properties, MP_API_KEY)
m.query()

STRUCTURE = m.result[0]['structure']
PSEUDO = pseudo_helper(STRUCTURE, PSEUDO_FAMILY,
                       PSEUDO_TABLE)
base_inputs = {
        'structure': STRUCTURE,

        'control': {
            'calculation': 'scf',
            'verbosity': 'high',
            'disk_io': 'none',
        },
        'system': {
            'ibrav': 0,
            'ecutwfc': 35,
            'occupations': 'smearing',
            'degauss': 0.01,
            'smearing': 'mv',
        },
        'electrons': {
            'electron_maxstep': 500,
            'conv_thr': 1.0e-7,
        },
        'ions': {},
        'cell': {},
        'kpoints_mode': 'automatic',
        'kpoints_grid': (10, 10, 10),
        'kpoints_shift': (0, 0, 0),

        'pseudo': PSEUDO
    }


runname = 'Alkpoint10'
calculation = pwcalculation_helper(**base_inputs,
    additional_inputs=list(PSEUDO.values()))
job = SubmitJob(calculation, 'espresso-6.2.1_pw', runname=runname)

import pdb; pdb.set_trace()
    
doc_id = db.insert(job, block_if_stored=False)
doc = db.get(doc_id=doc_id)

doc.status = 'testing'

doc_id_new = db.write_back([doc])[0]
doc_new = db.get(doc_id=doc_id_new)

print('done')
