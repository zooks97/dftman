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

PBSJOBS_DIRECTORY = os.path.join(os.getcwd(), 'PBSJobs')

class PBSJob(Mapping, base.Job):
    
    def __init__(self, calculation, command,
                 walltime='01:00:00', nnodes=1,
                 ppn=16, np=1, queue='standby',
                 runname=None, headertext='',
                 footertext='', parent_directory=None,
                 metadata=None,
                 directory=None, pbs_id=None,
                 status={}, submission_time=None,
                 submitted=False, doc_id=None, hash=None):
        self.calculation = calculation
        self.command = command
        self.walltime = walltime
        self.nnodes = nnodes
        self.ppn = ppn
        self.np = np
        self.queue = queue
        self.runname = runname
        self.headertext = headertext
        self.footertext = footertext
        self.parent_directory = parent_directory
        self.metadata = metadata
        
        self.pbs_id = pbs_id
        if status:
            self.status = status
        else:
            self.status = {'pbs_id': pbs_id,
                           'username': None,
                           'queue': None,
                           'runname': runname,
                           'session_id': None,
                           'nnodes': nnodes,
                           'np': np,
                           'reqd_memory': None,
                           'walltime': walltime,
                           'status': None,
                           'elapsed_time': None,
                           'submission_time': submission_time,
                           'doc_id': doc_id,
                           'hash': self.hash}
        self.submission_time = submission_time
        self.submitted = submitted
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
                self.directory = os.path.join(PBSJOBS_DIRECTORY,
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
        # print('Updated Job {hash:s} in database with doc_id {doc_id:d}'\
        #       .format(hash=self.hash, doc_id=self.doc_id))
        return self.doc_id
    
    def write_input(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        return self.calculation.write_input(name=self.input_name,
                                            directory=self.directory)
    
    def write_script(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        script = '#!/bin/bash\n'\
                 '#PBS -l walltime={walltime:s}\n'\
                 '#PBS -l nodes={nnodes:d}:ppn={ppn:d}\n'\
                 '#PBS -q {queue:s}\n'\
                 '#PBS -N {runname:s}\n'\
                 '{headertext:s}\n'\
                 '{run_command:s}\n'\
                 '{footertext:s}\n'.format(
                     walltime=self.walltime,
                     nnodes=self.nnodes,
                     ppn=self.ppn,
                     queue=self.queue,
                     runname=self.runname,
                     headertext=self.headertext,
                     np=self.np,
                     run_command=self.run_command,
                     footertext=self.footertext).strip()
        with open(self.script_path, 'w') as f:
            f.write(script)
            
    def parse_output(self):
        output = self.calculation.parse_output(name=self.output_name,
                                               directory=self.directory)
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
            self.write_script()
            process = subprocess.Popen(self.pbs_command,
                                       cwd=self.calculation.directory,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            self.process = process
        stdout = process.stdout.peek().decode('utf-8')
        stderr = process.stderr.peek().decode('utf-8')
        try:
            self.pbs_id = int(stdout.split('.')[0])
            self.status = {'status': 'Submitted', 'pbs_id': self.pbs_id}
            self.submitted = True
            self.submission_time = time.asctime(time.gmtime())
            self.update()
        except:
            raise ValueError('Could not find id. Didn\'t submit?\n'\
                             'stdout: {}\nstderr: {}'.format(stdout, stderr))
        return self.doc_id
    
    def check_status(self):
        if not self.pbs_id:
            raise ValueError('Job must have a PBS ID')
        
        status_codes = {'C': 'Complete',
                        'E': 'Exiting',
                        'H': 'Held',
                        'Q': 'Queued',
                        'R': 'Running',
                        'T': 'Moving',
                        'W': 'Waiting'
                     }

        qstat = subprocess.Popen(['qstat', '-u', getpass.getuser(),
                                  str(self.pbs_id)],
                                 cwd=self.calculation.directory,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        qstat_stdout = qstat.stdout.read().decode('utf-8')
        qstat_line = qstat_stdout.strip().split('\n')[-1]
        try:
            pbs_id, username, queue, runname, session_id,\
            nnodes, np, reqd_memory, walltime, status, elapsed_time = qstat_line.split()
            self.status = {'pbs_id': pbs_id,
                           'username': username,
                           'queue': queue,
                           'runname': runname,
                           'session_id': session_id,
                           'nnodes': nnodes,
                           'np': np,
                           'reqd_memory': reqd_memory,
                           'walltime': walltime,
                           'status': status_codes[status],
                           'elapsed_time': elapsed_time,
                           'submission_time': self.submission_time,
                           'doc_id': self.doc_id,
                           'hash': self.hash
                          }
        except:
            self.status['status'] = 'Complete'
        
        self.update()
        pretty_status = {'PBS ID': self.status.get('pbs_id'),
                         'Run Name': self.status.get('runname'),
                         'Status': self.status.get('status'),
                         'Elapsed Time': self.status.get('elapsed_time'),
                         'Walltime': self.status.get('walltime'),
                         'Queue': self.status.get('queue'),
                         'Doc ID': self.doc_id}             
        return pretty_status
    
    def kill(self):
        process = subprocess.run(['qdel', str(self.pbs_id)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
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
        return 'mpirun -np {np:d} {command:s}'.format(np=self.np,
            command=command)
    
    @property
    def pbs_command(self):
        return shlex.split('qsub "{script_path:s}"'.format(
            script_path=self.script_path))
    
    @property
    def input_name(self):
        return self.calculation.input_name
    
    @property
    def input_path(self):
        return os.path.join(self.directory,
                            self.calculation.input_name)
    
    @property
    def script_path(self):
        return os.path.join(self.directory,
                            'pbs_runscript.sh')
    
    @property
    def output_name(self):
        return self.calculation.output_name
    
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
            'command': self.command,
            'walltime': self.walltime,
            'nnodes': self.nnodes,
            'ppn': self.ppn,
            'np': self.np,
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
