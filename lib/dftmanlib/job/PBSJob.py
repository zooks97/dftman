import subprocess
import shlex
import time
import random
import re
import os

from collections.abc import Mapping

from .. import base


class PBSJob(Mapping, base.Job):
    
    def __init__(self, calculation, exec_line,
                 walltime='01:00:00', nnodes=1,
                 ppn=16, queue='standby',
                 runname=None, headertext='#!/bin/bash',
                 footertext='', parent_directory=None,
                 metadata=None,
                 directory=None, pbs_id=None,
                 status=None, submission_time=None,
                 submitted=False, doc_id=None, hash=None):
        self.calculation = calculation
        self.exec_line = exec_line
        self.walltime = walltime
        self.nnodes = nnodes
        self.ppn = ppn
        self.queue = queue
        self.runname = runname
        self.headertext = headertext
        self.footertext = footertext
        self.metadata = metadata
        
        self.pbs_id = pbs_id
        self.status = status
        self.submission_time = submission_time
        self.submitted = submitted
        self.doc_id = doc_id
        
        if runname:
            self.runname = runname
        else:
            self.runname = 'dftman_{}'.format(random.randint(1000,999999))
        
        if directory:
            self.directory = directory
        elif parent_directory:
            self.directory = os.path.join(parent_directory, self.hash)
        else:
            self.directory = os.path.join(JOBS_DIRECTORY,
                                          '{}_{}'.format(self.runname,
                                                         self.hash))
            
        self.input_name = self.calculation.input_name
        self.output_name = str(self.runname)+'.stdout'
        
    def __repr__(self):
        return pprint.pformat(self.as_dict())
    
    def __getitem__(self, item):
        return self.as_dict()[item]
    
    def __iter__(self):
        return self.as_dict().__iter__()
    
    def __len__(self):
        return len(self.as_dict())
    
    def insert(self, block_if_stored=True):
        db = load_db()
        table = db.table(self.__class__.__name__)
        if self.doc_id:
            raise 
        self.doc_id = table.insert(self, block_if_stored)
        doc_ids = table.write_back([self], doc_ids=[self.doc_id])
        print('Inserted Job {} into database with doc_id {}'
              .format(self.hash, self.doc_id))
        return self.doc_id
    
    def update(self):
        db = load_db()
        table = db.table(self.__class__.__name__)
        query = Query()
        self.doc_id = table.write_back([self], doc_ids=[self.doc_id])[0]
        print('Updated Job {} in database with doc_id {}'
              .format(self.hash, self.doc_id))
        return self.doc_id
    
    def write_input(self):
        return self.calculation.write_input(name=self.input_name,
                                            directory=self.directory)
    
    def write_script(self):
        pass
    
    def parse_output(self):
        output = self.calculation.parse_output(name=self.output_name,
                                             directory=self.directory)
        self.update()
        return output
    
    def run(self):
        if block_if_run and self.submitted:
            print('Already run, not submitting')
            return
        else:
            self.write_input()
            self.write_script()
            process = subprocess.Popen(shlex.split(self.command),
                                       cwd=self.calculation.directory,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        stdout = process.stdout.peek().decode('utf-8')
        try:
            self.pbs_id = int(stdout.split('.')[0])
            self.status = 'Submitted'
            self.submitted = True
            self.submission_time = time.asctime(time.gmtime())
        except:
            raise ValueError('Could not find id. Didn\'t submit?')
        return self.pbs_id
    
    def check_status(self):
        pass
    
    def kill(self):
        process = subprocess.run(['qdel', str(self.pbs_id)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        return process
    
    @property
    def hash(self):
        return self.calculation.hash
    
    @property
    def command(self):
        return ['qsub', '{}_run_script.sh'.format(self.runname)]
    
    @property
    def input_path(self):
        return os.path.join(self.directory,
                            self.calculation.input_name)
    
    @property
    def output_path(self):
            return os.path.join(self.directory,
                                self.calculation.output_name)
    
    @property
    def input(self):
        return self.calculation.input
    
    @property
    def output(self):
        return self.calculation.output
    
    def as_dict(self):
        dict_ = {
            '@module': self.__class__.__module__,
            '@class': self.__class__.__name__,
            'calculation': self.calculation.as_dict(),
            'exec_line': self.exec_line,
            'walltime': self.walltime,
            'nnodes': self.nnodes,
            'ppn': self.ppn,
            'queue': self.queue,
            'runname': self.runname,
            'headertext': self.headertext,
            'footertext': self.footertext,
            'parent_directory': self.parent_directory,
            'metadata': self.metadata,
            'directory': self.directory,
            'pbs_id': self.pbs_id,
            'status': self.status,
            'submission_time': self.submission_time,
            'submitted': self.submitted,
            'doc_id': self.doc_id
        }
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        decoded = {key: MontyDecoder().process_decoded(value)
                   for key, value in dict_.items()
                   if not key.startswith("@")}
        return cls(**decoded)
