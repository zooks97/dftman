import copy
import sys
import os.path

import numpy as np
import pandas as pd

from collections.abc import Mapping

from pymatgen import Structure
from pymatgen.analysis.eos import EOS

from monty.json import MontyDecoder

from tinydb import Query

from ..pwscf import pwcalculation_helper
from ...job import SubmitJob, PBSJob
from ... import base
from ...db import load_db

EOSWORKFLOWS_DIRECTORY = os.path.join(os.getcwd(), 'EOSWorkflows')

class EOSWorkflow(Mapping, base.Workflow):

    def __init__(self, structure, pseudo, base_inputs,
                 min_strain=-0.15, max_strain=0.15, n_strains=8,
                 job_type='SubmitJob', job_kwargs={},
                 metadata={},
                 stored=False, doc_id=None,
                 jobs_stored=False, job_ids=None,
                 hash=None, directory=None):
        
        if not isinstance(structure, Structure):
            structure = Structure.from_dict(structure)
        self.structure = structure
        self.pseudo = pseudo
        self.base_inputs = base_inputs
        
        self.min_strain = min_strain
        self.max_strain = max_strain
        self.n_strains = n_strains
        
        self.job_type = job_type
        self.job_class = getattr(sys.modules[__name__], job_type)
        self.job_kwargs = job_kwargs
        
        self.metadata = metadata
        
        self.strains = np.linspace(self.min_strain,
                                   self.max_strain,
                                   self.n_strains)
        
        self.stored = stored 
        self.doc_id = doc_id
        self.jobs_stored = jobs_stored
        self.job_ids = job_ids
        
        self.directory = os.path.join(EOSWORKFLOWS_DIRECTORY, self.hash)
    
    def __getitem__(self, item):
        return self.as_dict()[item]
    
    def __iter__(self):
        return self.as_dict().__iter__()
    
    def __len__(self):
        return len(self.as_dict())
    
    def insert(self):
        db = load_db()
        table = db.table(self.__class__.__name__)
        self.doc_id = table.insert(self)
        doc_ids = table.write_back([self], doc_ids=[self.doc_id])
        print('Inserted EOSWorkflow {} into database with doc_id {}'
              .format(self.hash, self.doc_id))
        return self.doc_id
        
    def update(self):
        db = load_db()
        table = db.table(self.__class__.__name__)
        query = Query()
        self.doc_id = table.write_back([self], doc_ids=[self.doc_id])[0]
        # print('Updated EOSWorkflow {} in database with doc_id {}'
        #       .format(self.hash, self.doc_id))
        return self.doc_id
    
    @property
    def hash(self):
        if isinstance(self.structure, Structure):
            structure = self.structure.as_dict()
        else:
            structure = self.structure
        key_dict = {
            'structure': structure,
            'pseudo': self.pseudo,
            'base_inputs': self.base_inputs,
            'min_strain': self.min_strain,
            'max_strain': self.max_strain,
            'n_strains': self.n_strains
        }
        return base.hash_dict(key_dict)
    
    def run(self):
        job_ids = []
        for job in self.jobs:
            job_id = job.run(block_if_run=False)
            job_ids.append(job_id)
        self.job_ids = job_ids
        self.jobs_stored = True
        self.doc_id = self.insert()
        self.stored = True
        self.update()
        return self.doc_id
        
    def check_status(self):
        statuses = []
        for job in self.jobs:
            statuses.append(job.check_status())
        status_df = pd.DataFrame(statuses)
        return status_df
    
    def _make_jobs(self):
        jobs = []
        for strain in self.strains:
            structure = copy.deepcopy(self.structure)
            inputs = copy.deepcopy(self.base_inputs)
            
            structure.apply_strain(strain)
            inputs['structure'] = structure
            
            calculation = pwcalculation_helper(
                **inputs, additional_inputs = list(self.pseudo.values()))
            
            job = self.job_class(calculation, runname=calculation.hash,
                                 parent_directory=self.directory,
                                 **self.job_kwargs,
                                 metadata={'strain': strain})
            
            jobs.append(job)
        
        return jobs
    
    def _get_jobs(self):
        if self.jobs_stored:
            db = load_db()
            table = db.table(self.job_type)
            jobs = [table.get(doc_id=job_id) for job_id in self.job_ids]
        else:
            jobs = self._make_jobs()
        return jobs
         
    @property
    def jobs(self):
        return self._get_jobs()
    
    @property
    def input(self):
        return {
            'structure': self.structure,
            'pseudo': self.pseudo,
            'base_inputs': self.base_inputs,
            'min_strain': self.min_strain,
            'max_strain': self.max_strain,
            'n_strains': self.n_strains
        }
    
    @property
    def output(self):
        data = []
        for job in self.jobs:
            if job.status['status'] == 'Complete':
                job.parse_output()
                job_data = {
                    'strain': job.metadata['strain'],
                    'energy': job.output.final_total_energy,  # eV
                    'volume': job.input.structure.volume  # A^3
                }
                data.append(job_data)
        data_df = pd.DataFrame(data)
        if not data_df.empty:
            equations = ['murnaghan', 'birch', 'vinet',
                         'birch_murnaghan', 'pourier_tarantola',
                         'deltafactor', 'numerical_eos']
            eos_fits = {}
            for equation in equations:
                eos = EOS(equation)
                eos_fits[equation] = eos.fit(data_df['volume'], data_df['energy'])
            return eos_fits
            
    def as_dict(self):
        dict_ = {
            'structure': self.structure,
            'pseudo': self.pseudo,
            'base_inputs': self.base_inputs,
            'min_strain': self.min_strain,
            'max_strain': self.max_strain,
            'n_strains': self.n_strains,
            'job_type': self.job_type,
            'job_kwargs': self.job_kwargs,
            'stored': self.stored,
            'doc_id': self.doc_id,
            'jobs_stored': self.jobs_stored,
            'job_ids': self.job_ids,
            'directory': self.directory,
            'metadata': self.metadata
        }
        return dict_
        
    @classmethod
    def from_dict(cls, dict_):
        decoded = {key: MontyDecoder().process_decoded(value)
                   for key, value in dict_.items()
                   if not key.startswith("@")}
        return cls(**decoded)
        
    
