import copy
import os.path

import numpy as np
import pandas as pd

from pymatgen import Structure
from pymatgen.analysis.eos import EOS

from ..pwscf import pwcalculation_helper
from ...job import SubmitJob
from ... import base
from ... import db


class EOSWorkflow(base.Workflow):

    def __init__(self, structure, pseudo, base_inputs, root,
                 min_strain=-0.05, max_strain=0.15, n_strains=8,
                 job_class=SubmitJob, code='espresso-6.2.1_pw'):
        self.structure = structure
        self.pseudo = pseudo
        self.base_inputs = base_inputs
        self.root = root
        self.min_strain = min_strain
        self.max_strain = max_strain
        self.n_strains = n_strains
        self.strains = np.linspace(self.min_strain,
                                   self.max_strain,
                                   self.n_strains)
        self.directory = os.path.join('./EOSWorkflows/', self.key)
        self.job_class = job_class
        self.code = code
        self.job_keys = [job.key for job in self.make_jobs()]
        self.stored = False
        self.jobs_stored = False
    
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
        jobs = self.get_jobs()
        for job in jobs:
            job.submit()
        self.jobs_stored = True
        return
        
    def check_status(self):
        statuses = []
        for job in self.get_jobs():
            statuses.append(job.check_status())
        return pd.DataFrame(statuses) 
    
    def make_jobs(self):
        jobs = []
        for strain in self.strains:
            structure = copy.deepcopy(self.structure)
            inputs = copy.deepcopy(self.base_inputs)
            
            structure.apply_strain(strain)
            inputs['structure'] = structure
            
            calculation = pwcalculation_helper(
                **inputs, additional_inputs = list(self.pseudo.values()))
            
            job = self.job_class(calculation, runname=calculation.key,
                                 directory=self.directory, code=self.code,
                                 metadata={'strain': strain})
            
            jobs.append(job)
        
        return jobs
    
    def get_jobs(self):
        if self.jobs_stored:
            jobs = [self.root.Jobs[key] for key in self.job_keys]
        else:
            jobs = self.make_jobs()
        return jobs
    
    @property
    def input(self):
        pass
    
    @property
    def output(self):
        data = []
        for job in self.jobs:
            job_data = {
                'strain': job.metadata['strain'],
                'energy': job.output.final_total_energy,  # eV
                'volume': job.input.structure.volume  # A^3
            }
            data.append(job_data)
        data_df = pd.DataFrame(data)
        equations = ['murnaghan', 'birch', 'vinet',
                     'birch_murnaghan', 'pourier_tarantola',
                     'deltafactor', 'numerical_eos']
        eos_fits = {}
        for equation in equations:
            eos = EOS(equation)
            eos_fits[equation] = eos(df['volumes'], df['energies'])
        return eos_fits
            
    def as_dict(self):
        pass 
        
    @classmethod
    def from_dict(cls, dict_):
        if dict_['id']:
            del dict_['id']
        decoded = {key: MontyDecoder().process_decoded(value)
                   for key, value in dict_.items()
                   if not key.startswith("@")}
        return cls(**decoded)
        
    
