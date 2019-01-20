import subprocess
import shlex
import time
import random
import re
import os

# TODO: fix output_path for pw calculations
#    the pw input needs to know the output file name
class SubmitJob():
    
    def __init__(self, calculation, code,
                 walltime='01:00:00', ncpus=1, runname=None):
        self.calculation = calculation
        self.code = code
        self.walltime = walltime# self._walltime_to_seconds(walltime)
        self.ncpus = ncpus
        if runname:
            self.runname = runname
        else:
            self.runname = str(random.randint(1000, 1000000))
        self.id = None
        self.status = None
        self.location = None
        self.submission_time = None
        self.run = False
    
    def submit(self, block_if_run=True):
        if block_if_run and self.run:
            print('Already run, not submitting')
            return
        else:
            process = subprocess.Popen(shlex.split(self.command),
                                       cwd=self.calculation.directory,
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
        return process
    
    def attach(self):
        process = subprocess.Popen(['submit', '--attach', str(self.id)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        return process
    
    def check_status(self):
        stdout = subprocess.check_output(['submit', '--status',
                                          str(self.id)]).decode('utf-8')
        if stdout:
            stdout_lines = stdout.strip().split('\n')
            if len(stdout_lines) > 1:
                info_line = stdout_lines[-1]
                runname, id_, instance, status, location = info_line.split()
                id_, instance = int(id_), int(instance)
                self.status = status
        else:
            if os.path.exists(self.output_path):
                self.status = 'Complete'
                
        return self.status
    
    # TODO: add cleaning option to delete directory and/or files
    def kill(self):
        process = subprocess.Run(['submit', '--kill', str(self.id)])
        
    @property
    def input_path(self):
        return os.path.join(self.calculation.directory, self.calculation.input_name)
    
    @property
    def output_path(self):
        if self.calculation.output_name:
            return os.path.join(self.calculation.directory,
                                self.calculation.output_name)
        else:
            return os.path.join(self.calculation.directory,
                                str(self.id)+'.stdout')

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
        self.calculation.write_input()
        input_name = self.calculation.input_name
        
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
            'input_name': input_name
        }
        
        command = base_command.format(**submit_data)
        return command
    
    def _walltime_to_seconds(walltime):
        ftr = [3600,60,1]
        return sum([a*b for a,b in zip(ftr, map(int,walltime.split(':')))])
    
    def as_dict(self):
        dict_ = {
            'calculation': self.calculation.as_dict(),
            'code': self.code,
            'walltime': self.walltime,
            'ncpus': self.ncpus,
            'runname': self.runname,
            'id': self.id,
            'status': self.status,
            'location': self.location,
            'submission_time': self.submission_time,
        }
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        return cls(**dict_)