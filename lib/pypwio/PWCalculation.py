import pprint
import os.path

from PWOutput import PWOutput
# from PWXML import PWXML
from pymatgen.io.pwscf import PWInput
# from .PWOutput import PWOutput
# from .PWXML import PWXML
# from .PWInput import PWInput

class PWCalculation():
    '''
    Data and information necessary to run a pw.x calculation
    :param input: PWInput object
    :param output: PWOutput object
    '''
    def __init__(self, input_, output=None,
                 input_name=None, output_name=None,
                 directory='./'):
        self.input = input_
        self.output = output
        self.input_name = input_name
        self.output_name = output_name
        self.directory = directory
        
        prefix = self.input.sections['control'].get('prefix')
        if not self.input_name:
            self.input_name = '{}.in'.format(prefix)
        if not self.output_name:
            self.output_name = '{}.out'.format(prefix)
        self.additional_inputs = [os.path.basename(pseudo)\
                                  for pseudo in self.input.pseudo.values()]
        return

    def __repr__(self):
        return 'INPUT:\n"""\n{}\n"""\n\nOUTPUT:\n{}\n'.format(
            self.input, self.output)
    
    def write_input(self, name=None, directory=None):
        if name:
            self.input_name = name
        if directory:
            self.directory = directory
        self.input.write_file(os.path.join(self.directory,
                                             self.input_name))
        return self.input_name

    def parse_output(self, name=None, directory=None,
                     output_type='stdout'):
        if name:
            self.output_name = name
        if directory:
            self.directory = directory
        output_path = os.path.join(self.directory,
                                   self.output_name)
        if output_type == 'stdout':
            with open(output_path, 'r') as f:
                text = f.read()
            self.output = PWOutput(stdout_string=text,
                                   stdout_name=output_path)
        elif output_type == 'xml':
            with open(outputl_path, 'r') as f:
                text = f.read()
            self.output = PWXML(xml_string=text,
                               xml_name=output_path)            
        return self.output

    def as_dict(self):
        if self.output:
            output = self.output.as_dict()
        else:
            output = None
        dict_ = {
            'input': self.input.as_dict(),
            'output': output,
            'input_name': self.input_name,
            'output_name': self.output_name,
            'directory': self.directory
        }
        return dict_

    @classmethod
    def from_dict(cls, dict_):
        input_ = PWInput.from_dict(dict_['input'])
        if pwdict['output']:
            output = PWOutput.from_dict(pwdict_['output'])
        else:
            output = dict_['output']
        calculation = cls(input_, output, xml,
                          dict_['input_name'], dict_['output_name'],
                          dict_['directory'])
        return calculation
