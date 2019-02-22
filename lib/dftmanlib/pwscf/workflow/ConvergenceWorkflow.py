import copy
import sys
import os.path

import numpy as np
import pandas as pd

from collections.abc import Mapping

from pymatgen import Structure

from monty.json import MontyDecoder

from tinydb import Query

from .. import pwcalculation_helper
from ...job import SubmitJob, PBSJob, LocalJob
from ... import base
from ...db import load_db

CONVWORKFLOWS_DIRECTORY = os.path.join(os.getcwd(), 'ConvergenceWorkflows')

class ConvergenceWorkflow(Mapping, base.Workflow):
    def __init__(self, structure, pseudo, base_inputs,
                 convergence_parameter='kgrid',
                 convergence_values=[(4, 4, 4), (8, 8, 8),
                                     (12, 12, 12), (16, 16, 16),
                                     (20, 20, 20), (24, 24, 24)],
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
        
        self.convergence_parameter = convergence_parameter
        self.convergence_values = convergence_values
        
        self.job_type = job_type
        self.job_class = getattr(sys.modules[__name__], job_type)
        self.job_kwargs = job_kwargs
        
        self.metadata = metadata
        
        self.stored = stored 
        self.doc_id = doc_id
        self.jobs_stored = jobs_stored
        self.job_ids = job_ids
        
        self._jobs = None
        
        self.directory = os.path.join(CONVWORKFLOWS_DIRECTORY, self.hash)
    
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
        print('Inserted ConvergenceWorkflow {} into database with doc_id {}'
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
            'convergence_parameter': self.convergence_parameter,
            'convergence_values': self.convergence_values
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
        
    def check_status(self, update_to_db=False):
        statuses = []
        jobs = self.jobs
        for job in jobs:
            statuses.append(job.check_status())
        if update_to_db:
            db = load_db()
            table = db.table(job.__class__.__name__)
            table.write_back(jobs, doc_ids=[job.doc_id for job in jobs])
        status_df = pd.DataFrame(statuses)
        return status_df
    
    def _make_jobs(self):
        jobs = []
        for value in self.convergence_values:
            inputs = copy.deepcopy(self.base_inputs)
            if self.convergence_parameter == 'kpoints_grid':
                inputs['kpoints_grid'] = value
            elif self.convergence_parameter == 'kpra':
                evenize = lambda x: x+1 if (x%2) else x
                inputs['kpoints_grid'] = (
                    evenize(int(np.ceil(value * 1/self.structure.lattice.a))),
                    evenize(int(np.ceil(value * 1/self.structure.lattice.b))),
                    evenize(int(np.ceil(value * 1/self.structure.lattice.c)))
                )
            elif self.convergence_parameter == 'ecutwfc':
                inputs['system']['ecutwfc'] = value
                
            inputs['structure'] = self.structure
            # inputs['pseudo'] = self.pseudo
            
            calculation = pwcalculation_helper(
                **inputs, additional_inputs = list(self.pseudo.values()))
            
            job = self.job_class(calculation, runname=calculation.hash,
                                 parent_directory=self.directory,
                                 **self.job_kwargs,
                                 metadata={'parameter': value})
            
            jobs.append(job)
        
        return jobs
         
    @property
    def jobs(self):
        if self._jobs:
            return self._jobs
        elif self.jobs_stored:
            db = load_db()
            table = db.table(self.job_type)
            self._jobs = table.get_multiple(doc_ids=self.job_ids)
            return self._jobs
        else:
            self._jobs = self._make_jobs()
            return self._jobs
    
    @property
    def input(self):
        return {
            'structure': self.structure,
            'pseudo': self.pseudo,
            'base_inputs': self.base_inputs,
            'convergence_parameter': self.convergence_parameter,
            'convergence_values': self.convergence_values
        }
    
    def parse_output(self, update_to_db=False):
        jobs = self.jobs
        
        data = []
        for job in jobs:
            if job.status['status'] == 'Complete':
                job.parse_output(update_to_db=False)
                job_data = {
                    'parameter': job.metadata['parameter'],
                    'energy': job.output.final_energy,  # eV
                    'volume': job.input.structure.volume  # A^3
                }
                data.append(job_data)
        data_df = pd.DataFrame(data)
        
        if update_to_db:
            db = load_db()
            table = db.table(jobs[0].__class__.__name__)
            table.write_back(jobs, doc_ids=[job.doc_id for job in jobs])
        
        return data_df
        
    @property
    def output(self):
        return self.parse_output()
            
    def as_dict(self):
        dict_ = {
            'structure': self.structure.as_dict(),
            'pseudo': self.pseudo,
            'base_inputs': self.base_inputs,
            'convergence_parameter': self.convergence_parameter,
            'convergence_values': self.convergence_values,
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
        
    
