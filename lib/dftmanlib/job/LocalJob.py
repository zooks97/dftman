import subprocess
import shlex
import time
import random
import re
import os
import pprint
import textwrap
import getpass

from collections.abc import Mapping

from tinydb import Query
from monty.json import MontyDecoder, MontyEncoder

from ..db import load_db
from .. import base

LOCALJOBS_DIRECTORY = os.path.join(os.getcwd(), 'LocalJobs')

class LocalJob(Mapping, base.Job):
    '''
    Class for running and storing jobs using the Torque
        queue system
    :param calculation: Calculation object for the job to run
    :type calculation: dftmanlib.base.Calculation
    :param command: Command used to run the job calculation within the
        Torque shell script, i.e. the shell command used to run the calculation
        Command supports curly-brace format notation for the following
        variables:
            input_path (str): full path to the job's input file
            output_path (str): full path to the job's output file
            additional_inputs (list): list of additional inputs from job's calculation
        e.g. to echo additional_inputs into the output_path, the command string might be:
            'echo {additional_inputs} > {output_path:s}'
    :type command: str
    :param np: number of processors to use
    :type np: int
    :param parent_directory: parent directory for the job (may create child directories within
    :type parent_directory: str
    :param metadata: any additional data used to e.g. tag the job, useful for querying from
        the database
    '''
    def __init__(self, calculation, command,
                 walltime='01:00:00', np=1,
                 mpi=False, wait=False, runname=None,
                 parent_directory=None, metadata=None,
                 directory=None, pid=None,
                 status={}, submission_time=None,
                 submitted=False, doc_id=None, hash=None):
        self.calculation = calculation
        self.command = command
        self.np = np
        self.mpi = mpi
        self.wait = wait
        self.parent_directory = parent_directory
        self.metadata = metadata
        
        self.submission_time = submission_time
        self.submitted = submitted
        self.status = status
        self.pid = pid
        self.doc_id = doc_id
        
        if runname:
            self.runname = runname
        else:
            self.runname = 'dftman_{}'.format(random.randint(1000,999999))
        
        if directory:
            self.directory = directory
        else:
            if parent_directory:
                self.directory = os.path.join(parent_directory, self.hash)
            else:
                self.directory = os.path.join(LOCALJOBS_DIRECTORY,
                                              '{runname:s}_{hash:s}'\
                                              .format(runname=self.runname,
                                                      hash=self.hash))
            if os.path.exists(self.directory):
                i = 1
                tmp_dir = self.directory+'_{}'
                while os.path.exists(self.directory):
                    self.directory = tmp_dir.format(i)
                    i += 1
        
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
        print('Inserted Job {hash:s} into database with doc_id {doc_id:d}'\
              .format(hash=self.hash, doc_id=self.doc_id))
        return self.doc_id
    
    def update(self):
        db = load_db()
        table = db.table(self.__class__.__name__)
        query = Query()
        self.doc_id = table.write_back([self], doc_ids=[self.doc_id])[0]
        return self.doc_id
    
    def write_input(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        return self.calculation.write_input(name=self.input_name,
                                            directory=self.directory)
            
    def parse_output(self, update_to_db=False):
        output = self.calculation.parse_output(name=self.output_name,
                                               directory=self.directory)
        if update_to_db:
            self.update()
        return output
    
    def run(self, block_if_run=True):
        if not self.doc_id:
            self.insert()
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        if block_if_run and self.submitted:
            print('Already run, not submitting')
            return
        else:
            self.write_input()
            if self.wait:
                with open(self.output_path, 'w') as output_handle:
                    process = subprocess.run(self.run_command,
                                             cwd=self.calculation.directory,
                                             stdout=output_handle,
                                             stderr=subprocess.PIPE)
                    stderr = process.stderr.decode('utf-8')
                    self.submitted = True
                    self.status['status'] = 'Complete'
            else:
                with open(self.output_path, 'w') as output_handle:
                    process = subprocess.Popen(self.run_command,
                                               cwd=self.calculation.directory,
                                               stdout=output_handle,
                                               stderr=subprocess.PIPE)
                self.process = process
                self.pid = process.pid
                self.status['status'] = 'Running'
                self.submitted = True
        # stdout = process.stdout.peek().decode('utf-8')
        # stderr = process.stderr.peek().decode('utf-8')
        return self.doc_id
    
    def check_status(self, update_in_db=False):
        if self.process:
            status = self.process.poll()
            if status is None:
                self.status['status'] = 'Running'
            elif status == 0:
                self.status['status'] = 'Complete'
            else:
                self.status['status'] = 'Error'
            return self.status
        else:
            return self.status
    
    def kill(self):
        self.process.kill()
        return process
    
    @property
    def hash(self):
        return self.calculation.hash
    
    @property
    def run_command(self):
        command = self.command.format(input_path=self.input_path,
                                      output_path=self.output_path,
                                      additional_inputs=\
                                      self.calculation.additional_inputs)
        if self.mpi:
            command = 'mpirun -np {np:d} {command:s}'.format(np=self.np,
                command=command)
        return shlex.split(command)
    
    @property
    def input_name(self):
        return self.calculation.input_name
    
    @property
    def input_path(self):
        return os.path.abspath(os.path.join(self.directory,
                               self.calculation.input_name))
    
    @property
    def output_name(self):
        return self.calculation.output_name
    
    @property
    def output_path(self):
        return os.path.abspath(os.path.join(self.directory,
                               self.calculation.output_name))
    
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
            'command': self.command,
            'mpi': self.mpi,
            'np': self.np,
            'wait': self.wait,
            'parent_directory': self.parent_directory,
            'metadata': self.metadata,
            'directory': self.directory,
            'status': self.status,
            'pid': self.pid,
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
