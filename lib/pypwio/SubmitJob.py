import subprocess
import shlex
import time
import random

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
    
    def submit(self):
        process = subprocess.Popen(shlex.split(self.command),
                                   cwd=self.calculation.directory,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout = process.stdout.peek().decode('utf-8')
        stderr = process.stderr.peek().decode('utf-8')
        id_re = re.compile(r'Check run status with the command: submit --status (\d+)')
        id_match = re.search(id_re, stdout)
        try:
            self.id = int(nanoHUB_id_match.group(1))
        except:
            raise SubmitError(stderr)
        self.status = 'Submitted'
        self.submission_time = time.asctime(time.gmtime())
        return process
    
    def attach(self):
        process = subprocess.Popen(['submit', '--attach', str(self.id)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        return process
    
    def check_status(self):
        process = subprocess.Popen(['submit', '--status', str(self.id)],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        stdout = process.stdout.peek().decode('utf-8')
        if stdout:
            info_line = stdout.split('\n')[-1]
            runname, id_, instance, status, location = info_line.split()
            id_, instance = int(id_), int(instance)
            self.status = status
            self.location = location
        else:
            if os.exists(self.output_path):
                self.status = 'Complete'
                
        return self.status
    
    def kill(self):
        process = subprocess.Popen(['submit', '--kill', str(self.id)])
        
    @property
    def input_path(self):
        return os.join(self.calculation.directory, self.calculation.input_name)
    
    @property
    def output_path(self):
        return os.join(self.calculation.directory, self.calculation.output_name)
    
    @property
    def stdout(self):
        stdout_path = os.join(self.calculation.directory, self.runname+'.stdout')
        if os.exists(stdout_path):
            with open(stdout_path, 'r') as f:
                stdout = f.read()
        else:
            stdout = None
        return stdout
    
    @property
    def stderr(self):
        stderr_path = os.join(self.calculation.directory, self.runname+'.stdout')
        if os.exists(stderr_path):
            with open(stderr_path, 'r') as f:
                stderr = f.read()
        else:
            stdout = None
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
                       ' {runname:s} {additional_inputs}'\
                       ' {code:s} -in {input_name:s}'
        self.calculation.set_run_directory('./')
        self.calculation.set_walltime(self._walltime_to_seconds(self.walltime))
        self.calculation.write_input()
        input_name = self.calculation.input_name
        additional_inputs = self.calculation.additional_inputs
        additional_inputs = ' '.join(additional_inputs)
        
        if self.runname:
            runname_string = '--runName="{:s}"'.format(runname)
        else:
            runname_string = ''
        
        submit_data = {
            'ncpus': self.ncpus,
            'walltime': self.walltime,
            'runname': runname_string,
            'additional_inputs': additional_inputs,
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
            'submission_time': self.submission_time
        }
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        return cls(**dict_)