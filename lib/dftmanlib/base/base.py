from abc import *


class Input(ABC):
    
    @property
    @abstractmethod
    def write_input(self):
        pass

    @abstractmethod
    def as_dict(self):
        pass
    
    @abstractclassmethod
    def from_dict(cls, dict_):
        pass


class Output(ABC):
    
    @property
    @abstractmethod
    def parse_output(self):
        pass

    @abstractmethod
    def as_dict(self):
        pass
    
    @abstractclassmethod
    def from_dict(cls, dict_):
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
        
    @abstractmethod
    def as_dict(self):
        pass
    
    @abstractclassmethod
    def from_dict(cls, dict_):
        pass


class Job(ABC):
    
    @abstractmethod
    def hash(self):
        pass
    
    @abstractmethod
    def run(self):
        pass
    
    @abstractmethod
    def kill(self):
        pass
    
    @abstractmethod
    def check_status(self):
        pass
    
    @abstractmethod
    def write_input(self):
        pass
    
    @abstractmethod
    def parse_output(self):
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
    
    @abstractmethod
    def as_dict(self):
        pass
    
    @abstractclassmethod
    def from_dict(cls, dict_):
        pass
    

class Workflow(ABC):
    
    @property
    @abstractmethod
    def hash(self):
        pass
    
    @abstractmethod
    def run(self):
        pass
    
    @property
    @abstractmethod
    def jobs(self):
        pass
    
    @property
    @abstractmethod
    def output(self):
        pass
    
    @abstractmethod
    def as_dict(self):
        pass
    
    @abstractclassmethod
    def from_dict(cls, dict_):
        pass
