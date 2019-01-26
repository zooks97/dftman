# #!/bin/bash
# #PBS -l walltime=02:59:00
# #PBS -l nodes=1:ppn=16
# #PBS -N QE
# #PBS -q standby
# #PBS -N BaTiSe3_ortho
# #PBS -m ea
# set echo
# cd $PBS_O_WORKDIR
# module load intel/16.0.1.150 impi/5.1.2.150 espresso/6.0
# mpirun -np 16 pw.x < BaTiSe3_tet_1.pwscf.in > BaTiSe3_tet_1.pwscf.out
import subprocess
import shlex
import time
import random
import re
import os

# TODO: Complete PbsJob implementation

from PWCalculation import PWCalculation

class PbsJob():
    
    def __init__(self, calculation, code,
                 walltime='01:00:00', nnodes=1,
                 ppn=16, queue='standby',
                 runname=None, status=None,
                 id=None, run=None, headertext='',
                 footertext=''):
        self.calculation = calculation
        self.code = code
        self.walltime = walltime
        self.nnodes = nnodes
        self.ppn = ppn
        if runname:
            self.runname = runname
        else:
            self.runname = str(random.randint(1000, 999999))
        self.id = id
        self.status = status
        self.location = location
        self.submission_time = submission_time
        self.run = run
        self.headertext = headertext
        self.footertext = footertext
        
    def submit(self, block_if_run=True):
        if block_if_run and self.run:
            print('Already run, not submitting')
            return
        else:
            self.write_script()
            process = subprocess.Popen(shlex.split(self.command),
                                       cwd=self.calculation.directory,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        self.run = True
        stdout = process.stdout.peek().decode('utf-8')
        try:
            self.id = int(stdout.split('.')[0])
        except:
            raise ValueError('Could not find id. Didn\'t submit?')
        self.status = 'Submitted'
        self.submission_time = time.asctime(time.gmtime())
        return process
    
    def check_status(self):
        pass
    
    def kill(self):
        pass
    
    def write_script(self):
        pass
    
    @property
    def input_path(self):
        pass
    
    @property
    def output_path(self):
        pass
    
    @property
    def input(self):
        return self.calculation.input
    
    @property
    def output(self):
        return self.calculation.output
    
    @property
    def command(self):
        return ['qsub', '{}_run_script.sh'.format(self.runname)]
    
    def as_dict(self):
        dict_ = {
            'calculation': self.calculation.as_dict(),
            'code': self.code,
            'walltime': self.walltime,
            'nnodes': self.nnodes,
            'ppn': self.ppn,
            'runname': self.runname,
            'id': self.id,
            'status': self.status,
            'submission_time': self.submission_time,
        }
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        dict_['calculation'] = PWCalculation.from_dict(dict_['calculation'])
        return cls(**dict_)