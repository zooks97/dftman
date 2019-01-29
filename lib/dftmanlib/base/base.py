from abc import *


class Input(ABC):
    
    @property
    @abstractmethod
    def write_input(self):
        pass

class Output(ABC):
    
    @property
    @abstractmethod
    def parse_output(self):
        pass

class Calculation(ABC):
    
    @property
    @abstractmethod
    def input(self):
        pass
    
    @property
    @abstractmethod
    def output(self):
        pass
    
    @abstractmethod
    def write_input(self):
        pass
    
    @abstractmethod
    def parse_output(self):
        pass
    
    @property
    @abstractmethod
    def directory(self):
        pass
    
    @property
    @abstractmethod
    def input_name(self):
        pass
    
    @property
    @abstractmethod
    def output_name(self):
        pass

class Job(ABC):
    
    @abstractmethod
    def submit(self, report=True, block_if_run=True,
               commit_transaction=True):
        pass
    
    @abstractmethod
    def kill(self, clean=True, commit_transaction=True):
        pass
    
    @abstractmethod
    def check_status(self, commit_transaction=True):
        pass
    
    @abstractmethod
    def write_input(self):
        pass
    
    @abstractmethod
    def parse_output(self):
        pass
    
    @property
    @abstractmethod
    def key(self):
        pass

    @property
    @abstractmethod
    def input_path(self):
        pass
    
    @property
    @abstractmethod
    def output_path(self):
        pass
    
    @property
    @abstractmethod
    def input(self):
        pass
    
    @property
    @abstractmethod
    def output(self):
        pass
    
    

class Workflow(ABC):
    
    @abstractmethod
    def run(self):
        pass
    
    @property
    @abstractmethod
    def key(self):
        pass
    
    @property
    @abstractmethod
    def jobs(self):
        pass
    
    @property
    @abstractmethod
    def output(self):
        pass
    