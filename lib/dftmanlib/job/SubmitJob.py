# TODO: add scheduler_stderr.txt and scheduler_stdout.txt support

import subprocess
import shlex
import time
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

class SubmitJob(Mapping, base.Job):
    '''
    Representation of a submit job on nanoHUB
    :param calculation: Calculation object which is a subclass of
        the dftmanlib.base.Calculation abstract base class
    :type calculation: dftmanlib.base.Calculation
    :param code: The code to run on nanoHUB, must be a valid sumbit
        code which you have access to, or submission to nanoHUB will fail
    :type code: str
    :param walltime: Walltime in hh:mm:ss format
    :type walltime: str
    :param ncpus: Number of CPUs requested
    :type ncpus: int
    :param parent_directory: parent directory for job directory
    :type parent_directory: str
    :param metadata: any additional data used to e.g. tag the job, useful for
        querying from the database
    '''
    
    def __init__(self, calculation, code,
                 walltime='01:00:00', ncpus=1,
                 parent_directory=None,
                 metadata=None,
                 directory=None, submit_id=None,
                 status=None, submission_time=None,
                 submitted=False,
                 doc_id=None, hash=None):
        self.calculation = calculation
        self.code = code
        self.walltime = walltime
        self.metadata = metadata
        self.ncpus = ncpus
        
        self.submit_id = submit_id
        self.submission_time = submission_time
        self.submitted = submitted
        self.doc_id = doc_id

        if status:
            self.status = status
        else:
            self.status = {
                'submit_id': submit_id,
                'instance': None,
                'status': None,
                'location': None,
                'submission_time': submission_time,
                'doc_id': doc_id,
                'hash': self.hash
            }
        
        if directory:
            self.directory = directory
        elif parent_directory:
            self.directory = os.path.join(parent_directory, self.hash)
        else:
            self.directory = os.path.join(SUBMITJOBS_DIRECTORY, '{}'.format(self.hash))
            
        self.input_name = self.calculation.input_name
        self.output_name = 'dftman.stdout'

    def __repr__(self):
        dict_ = {
            '@module': self.__class__.__module__,
            '@class': self.__class__.__name__,
            'calculation': self.calculation,
            'code': self.code,
            'walltime': self.walltime,
            'ncpus': self.ncpus,
            'submit_id': self.submit_id,
            'status': self.status,
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

    def insert(self, block_if_stored=False):
        db = load_db()
        table = db.table(self.__class__.__name__)
        if self.doc_id:
            raise ValueError('Already have a doc_id, cannot insert existing entry.')
        self.doc_id = table.insert(self, block_if_stored)
        doc_ids = table.write_back([self], doc_ids=[self.doc_id])
        print('Inserted Job {} into database with doc_id {}'.format(self.hash, self.doc_id))
        return self.doc_id
    
    def update(self):
        db = load_db()
        table = db.table(self.__class__.__name__)
        query = Query()
        self.doc_id = table.write_back([self], doc_ids=[self.doc_id])[0]
        print('Updated Job {} in database with doc_id {}'.format(self.hash, self.doc_id))
        return self.doc_id
    
    def _submit(self, report=True):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self.calculation.write_input(name='dftman.in', directory=self.directory)

        process = subprocess.Popen(shlex.split(self.command), cwd=self.directory, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.wait()
        
        if process.returncode == 0:
            self.submitted = True
        else:
            raise subprocess.CalledProcessError
        
        stdout = process.stdout.peek().decode('utf-8')
        stderr = process.stderr.peek().decode('utf-8')
        
        with open(os.path.join(self.directory, 'scheduler_stdout.txt'), 'w') as f:
            f.write(stdout)
        with open(os.path.join(self.directory, 'scheduler_stderr.txt'), 'w') as f:
            f.write(stderr)

        id_re = re.compile(r'Check run status with the command: submit --status (\d+)')
        id_match = re.search(id_re, stdout)
        
        try:
            self.submit_id = int(id_match.group(1))
        except:
            raise ValueError('Could not find id. Didn\'t submit?')
        
        # For now, delete all local copies of the transferred files automatically to save storage space
        shutil.rmtree(os.path.join(self.directory, '{}_transfer'.format(self.submit_id)))

        self.status['status'] = 'Submitted'
        self.submission_time = time.asctime(time.gmtime())
        
        print('Submitted job hash {} submit id {}'.format(self.hash, self.submit_id))
        return

    def run(self, report=True, block_if_submitted=False,
            block_if_stored=False):
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
        self.status['status'] = 'Killed'
        if clean:
            shutil.rmtree(self.directory)
        self.doc_id = self.update()
    
    def check_status(self, update_in_db=False):
        if not self.submit_id:
            raise ValueError('Job must have a Submit ID')
        if self.status['status'] == 'Complete':
            pretty_status = {'Submit ID': self.submit_id,
                             'Status': self.status.get('status'),
                             'Instance': self.status.get('instance'),
                             'Location': self.status.get('location'),
                             'Doc ID': self.doc_id}
            return pretty_status
        
        stdout = subprocess.check_output(['submit', '--status', str(self.submit_id)]).decode('utf-8')
        if stdout and self.submit_id in stdout:
            stdout_lines = stdout.strip().split('\n')
            if len(stdout_lines) > 1:
                info_line = stdout_lines[-1]
                runname, id_, instance, status, location = info_line.split()
                id_, instance = int(id_), int(instance)
                if id_ == self.submit_id:
                    self.status = {
                        'submit_id': id_,
                        'instance': instance,
                        'status': status,
                        'location': location,
                        'submission_time': self.submission_time,
                        'doc_id': self.doc_id,
                        'hash': self.hash
                    }
                    
        if os.path.exists(self.output_path):
            self.status['status'] = 'Complete'
            self.attach()
            
        if update_in_db:
            self.doc_id = self.update()
            
        pretty_status = {'Submit ID': self.submit_id,
                         'Status': self.status.get('status'),
                         'Instance': self.status.get('instance'),
                         'Location': self.status.get('location'),
                         'Doc ID': self.doc_id}
        return pretty_status
    
    def write_input(self):
        return self.calculation.write_input(name=self.input_name, directory=self.directory)
    
    def parse_output(self, **kwargs):
        output = self.calculation.parse_output(name=self.output_name, directory=self.directory, **kwargs)
        self.update()
        return output
        
    @property
    def input_path(self):
        return os.path.join(self.directory, self.calculation.input_name)

    @property
    def output_path(self):
            return os.path.join(self.directory, self.output_name)

    @property
    def stdout(self):
        stdout_path = os.path.join(self.calculation.directory, str(self.submit_id)+'.stdout')
        if os.path.exists(stdout_path):
            with open(stdout_path, 'r') as f:
                stdout = f.read()
        else:
            stdout = None
        return stdout
    
    @property
    def stderr(self):
        stderr_path = os.path.join(self.calculation.directory, str(self.submit_id)+'.stdout')
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
        base_command = 'submit --detach -n {ncpus:d} -w {walltime:s} --runName=dftman {additional_inputs:s} {code:s} -in {input_name:s}'
        
        if self.calculation.additional_inputs:
            additional_inputs = ' -i '.join(self.calculation.additional_inputs)
            additional_inputs_string = '-i {:s}'.format(additional_inputs)
        else:
            additional_inputs_string = ''
            
        
        submit_data = {
            'ncpus': self.ncpus,
            'walltime': self.walltime,
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
            'submit_id': self.submit_id,
            'status': self.status,
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
        decoded = {key: MontyDecoder().process_decoded(value) for key, value in dict_.items()
                   if not key.startswith("@")}
        return cls(**decoded)
