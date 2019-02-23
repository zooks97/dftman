import pprint
import os.path
import warnings
import tabulate
import pprint
import json
import pathlib
import copy

import re

from collections import (OrderedDict, defaultdict)

import pandas as pd
import numpy as np

from pymatgen import (Structure, Lattice)
from pymatgen.io.pwscf import PWInput as PymatgenPWInput

from monty.json import (MontyEncoder, MontyDecoder)
from monty.io import zopen

from . import pwoutput
from .. import base

A_PER_BOHR = 0.52917720859
A3_PER_BOHR3 = A_PER_BOHR ** 3
EV_PER_RY = 13.6056917253


class PWInput(PymatgenPWInput):
    '''
    Subclass of pymatgen's PWInput which adds:
        * PWInput.as_dict() for storing a PWInput object as a dictionary
        * PWInput.from_dict(pwinput_dict) for restoring a PWInput object
              from a dictionary
    See pymatgen.io.pwscf.PWInput for additional information
    :param structure:
    :type structure: pymatgen.core.Structure
    :param pseudo: pseudopotentials in the format:
        {'ELEMENT': 'PSEUDOPOTENTIAL_PATH'}
    :type pseudo: dict
    :param control: parameters in the CONTROL card of pw.x
    :type control: dict
    :param system: parameters in the SYSTEM card of pw.x
    :type system: dict
    :param electrons: parameters in the ELECTRONS card of
        pw.x
    :type electrons: dict
    :param ions: parameters in the IONS card of pw.x
    :type ions: dict
    :param cell: parameters in the CELL card of pw.x
    :type cell: dict
    :param kpoints_mode: type of kpoints to be provided
    :type kpoints_mode: str
    :param kpoints_grid: kpoints in the b1, b2, and b3 directions
    :type kpoints_grid: typle
    :param kpoints_shift: kpoints offset along b1, b2, and b3
        directions
    :type kpoints_shift: dict
    '''

    def __init__(self, **kwargs):
        super(PWInput, self).__init__(**kwargs)
        
    def __repr__(self):
        return pprint.pformat(self.as_dict())
    
    @property
    def hash(self):
        return base.hash_dict(self.as_dict())
    
    def write_input(self, filename):
        self.write_file(filename)
        
    def as_dict(self):
        dict_ = {
            '@module': self.__class__.__module__, 
            '@class': self.__class__.__name__,
            'structure': self.structure.as_dict(),
            'pseudo': self.pseudo,
            'control': self.sections.get('control'),
            'system': self.sections.get('system'),
            'electrons': self.sections.get('electrons'),
            'ions': self.sections.get('ions'),
            'cell': self.sections.get('cell'),
            'kpoints_mode': self.kpoints_mode,
            'kpoints_grid': self.kpoints_grid,
            'kpoints_shift': self.kpoints_shift
        }
        return dict_
        
    @classmethod
    def from_dict(cls, dict_):
        decoded = {key: MontyDecoder().process_decoded(value)
                   for key, value in dict_.items()
                   if not key.startswith("@")}
        return cls(**decoded)


class PWOutput(base.Output):
    '''
    Object for parsing, representing, and storing the output
        of PWscf calculations. This implementation uses a set
        of regular expressions, flags, and postprocessing functions
        provided by dftmanlib.pwscf.pwoutput
    :param filename: path to the PWscf output file
    :type filename: str
    :param data: dictionary of output data mostly used for restoring
        PWOutput objects from serialized dictionaries
    :type data: dict
    :param patterns: regular expression patterns in the following format:
        {'PROPERTY NAME': {'pattern': r'REGEXP PATTERN',
                           'flags': [re.FLAG1, re.FLAG2, ...],
                           'postprocess': POSTPROCESS_FUNCTION
                          },
         ...}
    :type patterns: dict
    '''
    def __init__(self, filename='', data=defaultdict(list),
                 patterns=pwoutput.patterns):
        self.filename = filename
        self.data = data
        self.patterns = patterns
        if filename:
            self.read_patterns(patterns)
        
    def __repr__(self):
        excluded_properties = ['kpoints_cart', 'kpoints_frac', 'bands_data']
        dict_ = {key: value for key, value in self.data.items()
                 if key not in excluded_properties}
        for key in excluded_properties:
            dict_[key] = 'EXCLUDED FROM PRINTING'
        return pprint.pformat(dict_)
        
    def read_patterns(self, patterns):
        '''
        General pattern reading uses stdlib's re module.
        
        Args:
            patterns (dict): A dict of patterns, e.g.,
                {"energy": {
                    "pattern": r"energy\\(sigma->0\\)\\s+=\\s+([\\d\\-.]+)",
                    "flags": [],
                    "postprocess": str}
                }
                
        Renders accessible:
            Any attribute in patterns. For example, the energy example above
            will set the value of self.data["energy"] = [-1234, -3453, ...],
            to the results from regex and postprocess
        '''
        with zopen(self.filename, 'rt') as file_:
            out = file_.read()
        all_matches = {}
        for key, value in patterns.items():
            pattern = re.compile(value['pattern'], *value['flags'])
            matches = pattern.findall(out)
            matches = [value['postprocess'](match) for match in matches]
            all_matches[key] = matches
        self.data.update(all_matches)
    
    def parse_output(self, filename):
        self.filename = filename
        self.read_patterns()
        return self.data
    
    def get_first(self, property_):
        try:
            return self.data[property_][0]
        except:
            return None
    
    def get_last(self, property_):
        try:
            return self.data[property_][-1]
        except:
            return None
    
    @property
    def structures(self):
        structures = []
        
        # scf step structures
        cells = []
        try:
            lattice_parameter = self.data['lattice_parameter']
            for i, alat in enumerate(lattice_parameter):
                cell = np.array([self.data['a1'][i],
                                 self.data['a2'][i],
                                 self.data['a3'][i]])
                cell = alat * cell
                cells.append(cell)
        except:
            cells = []
        atpos = self.data.get('initial_atomic_positions_frac', [])
        
        for cell, at in zip(cells, atpos):
            species = [a[0] for a in at]
            coords = [a[1] for a in at]
            structure = Structure(cell, species, coords)
            structures.append(structure)

        # relax step structures
        cells = self.data.get('cell_parameters', [])
        atpos = self.data.get('atomic_positions', [])

        for cell, at in zip(cells, atpos):
            species = [a[0] for a in at]
            coords = [a[1] for a in at]
            structure = Structure(cell, species, coords)
            structures.append(structure)

        return structures
    
    # TODO: band structure
    
    # TODO: symmetry operations
        
    @property
    def initial_structure(self):
        try:
            return self.structures[0]
        except:
            return None
        
    @property
    def initial_volume(self):
        return self.get_first('unit_cell_volume')
    
    @property
    def final_energy(self):
        return self.get_last('final_energy')
    
    @property
    def final_stress(self):
        return self.get_last('stress')
    
    @property
    def final_total_stress(self):
        return self.get_last('total_stress')
        
    @property
    def final_force(self):
        return self.get_last('force')
     
    @property
    def final_total_force(self):
        return self.get_last('total_force')
    
    @property
    def final_structure(self):
        try:
            return self.structures[-1]
        except:
            return None
        
    @property
    def fermi_energy(self):
        return self.get_last('fermi_energy')
        
    @property
    def final_volume(self):
        return self.get_last('unit_cell_volume')
    
    @property
    def lattice_type(self):
        return self.data.get('lattice_type')
    
    @property
    def succeeded(self):
        succeeded = True
        failure_reason = []
        # should only occur once
        if self.data.get('cpu_time_exceeeded'):
            succeeded = False
            failure_reason.append('CPU time was exceeded')
        if self.data.get('max_steps_reached'):
            succeeded = False
            failure_reason.append('Maximum ionic/electronic steps reached')
        if self.data.get('wentzcovitch_max_reached'):
            succeeded = False
            failure_reason.append('Maximum Wentzcovitch Damped Dynamics steps reached')
        if self.data.get('not_electronically_converged'):
            succeeded = False
            failure_reason.append('SCF convergence not achieved')
        if self.data.get('eigenvalues_not_converged'):
            succeeded = False
            failure_reason.append('Some eigenvalues were not converged')
        if self.data.get('general_error'):
            succeeded = False
            failure_reason.append('General error(s) given')
        if not self.data.get('job_done'):
            succeeded = False
            failure_reason.append('Job not done')
        
        return succeeded, failure_reason
        
    @property
    def output(self):
        return self.data
    
    def as_dict(self):
        dict_ = {
            '@module': self.__class__.__module__,
            '@class': self.__class__.__name__,
            'filename': self.filename,
            # 'data': self.data,  # data not saved to maintain database performance
        }
        return dict_
    
    @classmethod
    def from_dict(cls, dict_):
        return cls(**dict_)
    
        
class PWCalculation(base.Calculation):
    '''
    Data and information necessary to run a pw.x calculation
    :param input: PWInput object
    :type input: dftmanlib.pwscf.PWInput
    :param output: PWOutput object
    :type output: dftmanlib.pwscf.PWOutput
    :param input_name: input file name
    :type input_name: str
    :param directory: directory in which to run the calculation
    :type directory: str
    :param additional_inputs: list additional input file path strings
        necessary to run the calculation (mostly used for passing to
        submit in nanoHUB)
    :type additional_inputs: list
    '''
    def __init__(self, input_, output=None,
                 input_name=None, directory='./',
                 additional_inputs=None,
                 output_type=None):
        self._input = input_
        self._output = output
        self._input_name = input_name
        self._output_name = None
        self.output_type = output_type
        self._directory = directory
        
        prefix = self.input.sections['control'].get('prefix')
        if not self.input_name:
            self.input_name = '{}.in'.format(prefix)
        if not self.output_name:
            self.output_name = '{}.out'.format(prefix)
        self.additional_inputs = additional_inputs
        return

    def __repr__(self):
        dict_ = {
            'input': self.input,
            'output': self.output,
            'input_name': self.input_name,
            'output_name': self.output_name,
            'output_type': self.output_type,
            'directory': self.directory
        }
        return pprint.pformat(dict_)
    
    @property
    def hash(self):
        return self.input.hash
        
    @property
    def directory(self):
        return self._directory
        
    @directory.setter
    def directory(self, value):
        self._directory = value
        
    @property
    def input(self):
        return self._input
        
    @input.setter
    def input(self, value):
        self._input = value
        
    @property
    def output(self):
        return self._output
        
    @output.setter
    def output(self, value):
        self._output = value
        
    @property
    def input_name(self):
        return self._input_name
        
    @input_name.setter
    def input_name(self, value):
        self._input_name = value
    
    @property
    def output_name(self):
        return self._output_name
        
    @output_name.setter
    def output_name(self, value):
        self._output_name = value
    
    def write_input(self, name=None, directory=None):
        '''
        Write the calculation's input file by calling
            write_file on the input object.
        :param name: string input file name
        :param directory: run directory path as a string
        '''
        if name:
            self.input_name = name
        if directory:
            self.directory = directory
        self.input.write_file(os.path.join(self.directory,
                                             self.input_name))
        return self.input_name

    def parse_output(self, name=None, directory=None,
                     output_type='stdout'):
        '''
        Parse the calculation's output file by creating
            the appropriate output object and using it to
            parse the corresponding output file
        :param name: string output file name
        :param directory: run directory path as a string
        :param output_type: type of output to parse
            'stdout' is supported for pw.x
        :return: PWOutput or PWXML object
        '''
        if name:
            self.output_name = name
        if directory:
            self.directory = directory
        output_path = os.path.join(self.directory,
                                   self.output_name)
        if output_type == 'stdout':
            output = PWOutput(filename=output_path)
            self.output = output
            self.output_type = output_type

        return self.output

    def as_dict(self):
        dict_ = {
            '@module': self.__class__.__module__,
            '@class': self.__class__.__name__,
            'input_': self.input.as_dict(),
            'output': self.output.as_dict(),
            'input_name': self.input_name,
            'directory': self.directory,
            'additional_inputs': self.additional_inputs,
            'output_type': self.output_type,
        }
        return dict_

    @classmethod
    def from_dict(cls, dict_):
        decoded = {key: MontyDecoder().process_decoded(value)
                   for key, value in dict_.items()
                   if not key.startswith("@")}
        return cls(**decoded)