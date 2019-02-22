from abc import *


class Input(ABC):
    '''
    Abstract base class for Input classes in DFTman
    Input classes must implement:
        write_input: a function to write the input to file
        as_dict: a function to convert the input object into
            a serializable dictionary
        from_dict: a class method to convert a dictionary into
            an Input object
    '''
    
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
    '''
    Abstract base class for Output classes in DFTman
    Output classes must implement:
        output: a property which returns the contents of the Output
        as_dict: a function to convert the object into
            a serializable dictionary
        from_dict: a class method to convert a dictionary into
            an object
    '''
        
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


class Calculation(ABC):
    '''
    Abstract base class for Calculation classes in DFTman
    Calculation classes must implement:
        input: a property which returns the Input object
            of the calculation
        output: a property which returns the Output object
            of the calculation
        write_input: a function to write the input of the
            Input object of the calculation
        parse_output: a function to parse / retrieve the output
            of the Output object of the calculation
        directory: the directory in which the calculation is run
        input_name: the name of the input file
        output_name: the name of the output file
        as_dict: a function to convert the object into
            a serializable dictionary
        from_dict: a class method to convert a dictionary into
            an object
    '''
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
    '''
    Abstract base class for Job classes in DFTman
    Job classes must implement:
        hash: a method to retrieve a hash of the job
        run: a method to run the job
        kill: a method to kill the job if it is running
        check_status: a method to check the status of a running job
        write_input: a method to write the input of the job's
            Calculation
        parse_output: a method to parse the output of the job's
            Calculation
        input_path: path to the job's calculation's input file
        output_path: path to the job's calculation's output file
        input: job's calculation's Input object
        output: job's calculation's Output object
        as_dict: a function to convert the object into
            a serializable dictionary
        from_dict: a class method to convert a dictionary into
            an object
    '''
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
    '''
    Abstract base class Workflow classes in DFTman
    Workflows act as convenient containers for sets of Jobs
        where a specific task is done using Jobs and their outputs
        like calculating an Equation of State using DFT
    Workflow classes must implement:
        hash: function which returns a unique hash of the Workflow,
            often by hashing the combination of the Workflow's Jobs'
            hashes
        run: function which runs the Workflow, often by starting 
            all the associated Jobs
        jobs: property which returns the Workflow's Jobs
        output: property which returns the Workflow's output
        as_dict: a function to convert the object into
            a serializable dictionary
        from_dict: a class method to convert a dictionary into
            an object
    '''
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
