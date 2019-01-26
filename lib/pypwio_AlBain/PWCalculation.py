import pprint
import os.path

import persistent

from PWInput import PWInput

from PWOutput import PWOutput
# from pymatgen.io.pwscf import PWInput

class PWCalculation(persistent.Persistent):
    '''
    Data and information necessary to run a pw.x calculation
    :param input: PWInput object
    :param output: PWOutput object
    '''
    def __init__(self, input_, output=None,
                 input_name=None, directory='./',
                 additional_inputs=None, output_type=None):
        self.input = input_
        self.output = output
        self.input_name = input_name
        self.output_name = None
        self.output_type = output_type
        self.directory = directory
        
        prefix = self.input.sections['control'].get('prefix')
        if not self.input_name:
            self.input_name = '{}.in'.format(prefix)
        self.additional_inputs = additional_inputs
        return

    def __repr__(self):
#         return 'INPUT:\n"""\n{}\n"""\n\nOUTPUT:\n{}\n'.format(
#             self.input, self.output)
        dict_ = self.as_dict()
        del dict_['output']['stdout_string']
        print(dict_['output'].keys())
        return pprint.pformat(dict_)
    
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
            output = PWOutput(stdout_string=text,
                              stdout_path=output_path)
            self.output = output
            self.output_type = output_type
        elif output_type == 'xml':
            with open(outputl_path, 'r') as f:
                text = f.read()
            output = PWXML(xml_string=text,
                           xml_name=output_path)
            self.output = output
            self.output_type = output_type
        return self.output

    def as_dict(self):
        dict_ = {
            'additional_inputs': self.additional_inputs,
            'directory': self.directory,
            'input_name': self.input_name,
            'input': self.input.as_dict(),
            'output_name': self.output_name,
            'output_type': self.output_type,
            'output': self.output.as_dict() if self.output else None,
        }
        return dict_

    @property
    def key(self):
        return self.input.key
    
    @classmethod
    def from_dict(cls, dict_):
        input_ = PWInput.from_dict(dict_['input'])
        if dict_['output']:
            if dict_['output_type'] == 'stdout':
                output = PWOutput.from_dict(dict_['output'])
            elif dict_['output_type'] == 'xml':
                output = PWXML.from_dict(dict_['output'])
        else:
            output = dict_['output']
        calculation = cls(input_, output,
                          input_name=dict_['input_name'],
                          output_name=dict_['output_name'],
                          additional_inputs=dict_['additional_inputs'],
                          directory=dict_['directory'])
        return calculation
