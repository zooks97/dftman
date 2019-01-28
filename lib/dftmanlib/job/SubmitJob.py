import subprocess
import shlex
import time
import random
import re
import os
import pprint
import shutil

import persistent
import transaction

# TODO: adding subclass PwSubmitJob could fix the PwCalculation dependence of SubmitJob
# TODO: rename all pw.x classes => PwClassName instead of PWClassName

class SubmitJob(persistent.Persistent):
    '''
    Persistent class which represents a submit job on nanoHUB
    :param calculation:
    :param code:
    :param walltime:
    :param ncpus:
    :param runname:
    :param directory:
    :param id:
    :param status:
    :param location:
    :param submission_time:
    :param run:
    '''
    def __init__(self, calculation, code,
                 walltime='01:00:00', ncpus=1,
                 runname=None, directory=None,
                 id=None, status=None, location=None,
                 submission_time=None, run=None,
                 metadata=None):
        self.calculation = calculation
        self.code = code
        self.walltime = walltime
        self.ncpus = ncpus
        if runname:
            if runname.isalnum():
                self.runname = runname
            else:
                raise ValueError('runname must be strictly alphanumeric.')
        else:
            self.runname = str(random.randint(1000, 999999))
        if directory:
            self.directory = directory
        else:
            # TODO: decide what to do with calculation.directory
            self.directory = './jobs/{}_{}/'.format(self.runname, self.key)
        
        self.id = id
        self.status = status
        self.location = location
        self.submission_time = submission_time
        self.run = run
        self.metadata = metadata
    
    def __repr__(self):
        return pprint.pformat(self.as_dict())
    
    def submit(self, report=True, block_if_run=True,
               commit_transaction=True):
        if block_if_run and self.run:
            print('Already run, not submitting')
            return
        else:
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
            self.calculation.write_input(name=self.runname+'.in',
                                         directory=self.directory)
            
            process = subprocess.Popen(shlex.split(self.command),
                                       cwd=self.directory,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        self.run = True
        stdout = process.stdout.peek().decode('utf-8')
        stderr = process.stderr.peek().decode('utf-8')
        id_re = re.compile(r'Check run status with the command: submit --status (\d+)')
        id_match = re.search(id_re, stdout)
        try:
            self.id = int(id_match.group(1))
        except:
            raise ValueError('Could not find id. Didn\'t submit?')
        self.status = 'Submitted'
        self.submission_time = time.asctime(time.gmtime())
        print('Submitted job {} {}'.format(self.runname, self.key))
        if commit_transaction:
            transaction.commit()
        return 
    
    def attach(self):
        process = subprocess.Popen(['submit', '--attach', str(self.id)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        return process
    
    def kill(self, clean=True, commit_transaction=True):
        process = subprocess.run(['submit', '--kill', str(self.id)])
        self.status = 'Killed'
        if clean:
            shutil.rmtree(self.directory)
        if commit_transaction:
            transaction.commit()
    
    def check_status(self, commit_transaction=True):
        if self.status == 'Complete':
            return self.status
        
        stdout = subprocess.check_output(['submit', '--status',
                                          str(self.id)]).decode('utf-8')
        if stdout:
            stdout_lines = stdout.strip().split('\n')
            if len(stdout_lines) > 1:
                info_line = stdout_lines[-1]
                runname, id_, instance, status, location = info_line.split()
                id_, instance = int(id_), int(instance)
                if runname == self.runname:
                    self.status = status
                    self.location = location
                else:
                    for line in stdout_lines[1:]:
                        runname, id_, instance, status, location = info_line.split()
                        if runname == self.runname:
                            self.id = id_
                            self.status = status
                            self.location = location
            else:
                if os.path.exists(self.output_path):
                    self.status = 'Complete'
                    self.attach()
        else:
            if os.path.exists(self.output_path):
                self.status = 'Complete'
                self.attach()
        if commit_transaction:
            transaction.commit()
                
        return self.status
    
    def parse_output(self):
        return self.calculation.parse_output(name=self.output_name,
                                             directory=self.directory)
        
    @property
    def key(self):
        return self.calculation.key
        
    @property
    def input_path(self):
        return os.path.join(self.directory, self.calculation.input_name)
    
    @property
    def output_name(self):
        if self.calculation.output_name:
            return self.calculation.output_name
        else:
            return str(self.runname)+'.stdout'
    
    @property
    def output_path(self):
            return os.path.join(self.directory,
                                self.output_name)

    @property
    def stdout(self):
        stdout_path = os.path.join(self.calculation.directory,
                                   str(self.id)+'.stdout')
        if os.path.exists(stdout_path):
            with open(stdout_path, 'r') as f:
                stdout = f.read()
        else:
            stdout = None
        return stdout
    
    @property
    def stderr(self):
        stderr_path = os.path.join(self.calculation.directory,
                                   str(self.id)+'.stdout')
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
            additional_inputs = ' '.join(self.calculation.additional_inputs)
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
            'calculation': calculation_dict,
            'code': self.code,
            'walltime': self.walltime,
            'ncpus': self.ncpus,
            'runname': self.runname,
            'id': self.id,
            'status': self.status,
            'location': self.location,
            'submission_time': self.submission_time,
            'metadata': self.metadata
        }
        return dict_