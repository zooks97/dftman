import subprocess
import shlex
import time
import random
import re
import os
import os.path
import pprint
import shutil
import json

from collections.abc import Mapping

from monty.json import MontyEncoder, MontyDecoder

from ..db import load_db, MSONStorage
from .. import base

from tinydb import Query

SUBMITJOBS_DIRECTORY = os.path.join(os.getcwd(), 'SubmitJobs')

# TODO: adding subclass PwSubmitJob could fix the PwCalculation dependence
#           of SubmitJob
# TODO: rename all pw.x classes => PwClassName instead of PWClassName

class SubmitJob(Mapping, base.Job):
    '''
    Persistent class which represents a submit job on nanoHUB
    :param calculation:
    :param code:
    :param walltime:
    :param ncpus:
    :param runname:
    :param directory: parent directory for job directory
    :param id:
    :param status:
    :param location:
    :param submission_time:
    :param run:
    '''
    
    
    def __init__(self, calculation, code,
                 walltime='01:00:00', ncpus=1,
                 runname=None, parent_directory=None,
                 metadata=None,
                 directory=None, submit_id=None,
                 status=None, location=None,
                 submission_time=None, submitted=False,
                 doc_id=None, hash=None):
        self.calculation = calculation
        self.code = code
        self.walltime = walltime
        self.metadata = metadata
        self.ncpus = ncpus
        
        self.submit_id = submit_id
        self.status = status
        self.location = location
        self.submission_time = submission_time
        self.submitted = submitted
        self.process = None
        self.doc_id = doc_id
        
        
        if runname:
            self.runname = runname
        else:
            self.runname = 'dftman{}'.format(random.randint(1000,999999))
        
        if directory:
            self.directory = directory
        elif parent_directory:
            self.directory = os.path.join(parent_directory, self.hash)
        else:
            self.directory = os.path.join(SUBMITJOBS_DIRECTORY,
                                          '{}_{}'.format(self.runname,
                                                         self.hash))
            
        self.input_name = self.calculation.input_name
        self.output_name = str(self.runname)+'.stdout'


    def __repr__(self):
        dict_ = {
            '@module': self.__class__.__module__,
            '@class': self.__class__.__name__,
            'calculation': self.calculation,
            'code': self.code,
            'walltime': self.walltime,
            'ncpus': self.ncpus,
            'runname': self.runname,
            'submit_id': self.submit_id,
            'status': self.status,
            'location': self.location,
            'submission_time': self.submission_time,
            'metadata': self.metadata,
            'directory': self.directory,
            'hash': self.hash,
            'doc_id': self.doc_id,
            'submitted': self.submitted
        }
        return pprint.pformat(dict_)
    
    def __getitem__(self, item):
        return self.as_dict()[item]
    
    def __iter__(self):
        return self.as_dict().__iter__()
    
    def __len__(self):
        return len(self.as_dict())
    
    @property
    def hash(self):
        return self.calculation.hash


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
    
    # TODO: fix so that entries with the same hash aren't all updated
    #       i.e. fix querying by doc_id
    def update(self):
        db = load_db()
        table = db.table(self.__class__.__name__)
        query = Query()
        self.doc_id = table.write_back([self], doc_ids=[self.doc_id])[0]
        print('Updated Job {} in database with doc_id {}'
              .format(self.hash, self.doc_id))
        return self.doc_id
    
    
    def _submit(self, report=True):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.calculation.write_input(name=self.runname+'.in',
                                     directory=self.directory)

        process = subprocess.Popen(shlex.split(self.command),
                                   cwd=self.directory,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        self.process = process
        
        self.submitted = True
        
        stdout = process.stdout.peek().decode('utf-8')
        stderr = process.stderr.peek().decode('utf-8')
        
        id_re = re.compile(r'Check run status with the command: submit'\
                            ' --status (\d+)')
        id_match = re.search(id_re, stdout)
        
        try:
            self.submit_id = int(id_match.group(1))
        except:
            raise ValueError('Could not find id. Didn\'t submit?')
        
        self.status = 'Submitted'
        self.submission_time = time.asctime(time.gmtime())
        
        print('Submitted job runname {} hash {} submit id {}'.format(self.runname,
                                                                     self.hash,
                                                                     self.submit_id))
        return


    def run(self, report=True, block_if_submitted=True,
            block_if_stored=True):
        if block_if_submitted and self.submitted:
            print('Already run, not running.')
            return
        self.doc_id = self.insert(block_if_stored)
        self._submit(report)
        self.doc_id = self.update()
        return self.doc_id
        
    
    def attach(self):
        process = subprocess.Popen(['submit', '--attach', str(self.submit_id)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        return process
    
    
    def kill(self, clean=True):
        process = subprocess.run(['submit', '--kill', str(self.submit_id)])
        self.status = 'Killed'
        if clean:
            shutil.rmtree(self.directory)
        self.doc_id = self.update()
    
    
    # TODO: update this to be similar to PBSJob
    def check_status(self):
        if self.status == 'Complete':
            return self.status_dict
        
        stdout = subprocess.check_output(['submit', '--status',
                                          str(self.submit_id)]).decode('utf-8')
        if stdout and self.runname in stdout:
            stdout_lines = stdout.strip().split('\n')
            if len(stdout_lines) > 1:
                info_line = stdout_lines[-1]
                runname, id_, instance, status, location = info_line.split()
                id_, instance = int(id_), int(instance)
                if runname == self.runname:
                    self.status = status
                    self.location = location
#                 else:
#                     for line in stdout_lines[1:]:
#                         runname, id_, instance, status, location = \
#                             info_line.split()
#                         if runname == self.runname:
#                             self.submit_id = id_
#                             self.status = status
#                             self.location = location

        if os.path.exists(self.output_path):
            self.status = 'Complete'
            self.attach()
            
        self.doc_id = self.update()
        
        return self.status_dict
    
    
    def write_input(self):
        return self.calculation.write_input(name=self.input_name,
                                            directory=self.directory)
    
    
    def parse_output(self):
        output = self.calculation.parse_output(name=self.output_name,
                                             directory=self.directory)
        self.update()
        return output
    
    @property
    def status_dict(self):
        status_dict = {
            'Status': self.status,
            'ID': self.submit_id,
            'Run Name': self.runname,
            'Location': self.location,
            'Submission Time': self.submission_time,
            'Hash': self.hash,
            'Doc ID': self.doc_id,
        }
        return status_dict
        
    @property
    def input_path(self):
        return os.path.join(self.directory,
                            self.calculation.input_name)
    
    @property
    def output_path(self):
            return os.path.join(self.directory,
                                self.output_name)

    @property
    def stdout(self):
        stdout_path = os.path.join(self.calculation.directory,
                                   str(self.submit_id)+'.stdout')
        if os.path.exists(stdout_path):
            with open(stdout_path, 'r') as f:
                stdout = f.read()
        else:
            stdout = None
        return stdout
    
    
    @property
    def stderr(self):
        stderr_path = os.path.join(self.calculation.directory,
                                   str(self.submit_id)+'.stdout')
        if os.path.exists(stderr_path):
            with open(stderr_path, 'r') as f:
                stderr = f.read()
        else:
            stderr = None
        return stderr
    
    
    @property
    def input(self):
        return self.calculation.input
    
    
    @property
    def output(self):
        return self.calculation.output
    
    
    @property
    def command(self):
        base_command = 'submit --detach -n {ncpus:d} -w {walltime:s}'\
                       ' {runname:s} {additional_inputs:s}'\
                       ' {code:s} -in {input_name:s}'
        
        if self.runname:
            runname_string = '--runName="{:s}"'.format(self.runname)
        else:
            runname_string = ''
        if self.calculation.additional_inputs:
            additional_inputs = ' -i '.join(self.calculation.additional_inputs)
            additional_inputs_string = '-i {:s}'.format(additional_inputs)
        else:
            additional_inputs_string = ''
            
        
        submit_data = {
            'ncpus': self.ncpus,
            'walltime': self.walltime,
            'runname': runname_string,
            'additional_inputs': additional_inputs_string,
            'code': self.code,
            'input_name': self.calculation.input_name
        }
        
        command = base_command.format(**submit_data)
        return command
    
    
    def _walltime_to_seconds(walltime):
        ftr = [3600,60,1]
        return sum([a*b for a,b in zip(ftr, map(int,walltime.split(':')))])
    
    
    def as_dict(self):
        calculation_dict = self.calculation.as_dict()
        if calculation_dict.get('output'):
            if calculation_dict['output'].get('stdout_string'):
                del calculation_dict['output']['stdout_string']
        dict_ = {
            '@module': self.__class__.__module__,
            '@class': self.__class__.__name__,
            'calculation': self.calculation.as_dict(),
            'code': self.code,
            'walltime': self.walltime,
            'ncpus': self.ncpus,
            'runname': self.runname,
            'submit_id': self.submit_id,
            'status': self.status,
            'location': self.location,
            'submission_time': self.submission_time,
            'metadata': self.metadata,
            'directory': self.directory,
            'hash': self.hash,
            'doc_id': self.doc_id,
            'submitted': self.submitted
        }
        return dict_
    
        
    def to_json(self):
        return json.dumps(self, cls=MontyEncoder)
    
    
    @classmethod
    def from_dict(cls, dict_):
        decoded = {key: MontyDecoder().process_decoded(value)
                   for key, value in dict_.items()
                   if not key.startswith("@")}
        return cls(**decoded)
