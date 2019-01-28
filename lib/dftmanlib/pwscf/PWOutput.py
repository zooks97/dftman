import warnings
import tabulate
import pprint

import persistent
import transaction

import pandas as pd

from pymatgen import Structure

A_PER_BOHR = 0.52917720859
A3_PER_BOHR3 = A_PER_BOHR ** 3
EV_PER_RY = 13.6056917253

# TODO: figure out how to communicate units (doc strings?)
# TODO: better differentiate scf, relax, and vc-relax 
# TODO: figure out better names for the outputs

class PWOutput(persistent.Persistent):
    '''
    Class which parses pw.x standard output into useful physical and 
        simulation properties
    :param _string: python string (decoded) of the standard
        output from a pw.x simulation
    :param stdout_path: string describing the path to the standard
        output file from pw.x, used for bookkeeping
    '''
    def __init__(self, string='', path=''):
        self._path = path
        self._string = string
        self._lines = string.split('\n')
        return

    def __repr__(self):
        return pprint.pformat(self.output_dict)
        
    @property
    def string(self):
        return self._string
    
    @string.setter
    def string(self, value, commit_transaction=True):
        if isinstance(value, str):
            self._string = value
            if commit_transaction:
                transaction.commit()
        else:
            raise ValueError('String must be type str')
    
    @property
    def lines(self):
        if self._string:
            return self._string.split('\n')
        else:
            return None
    
    @lines.setter
    def lines(self, value):
        if isinstance(lines, list):
            self._lines = value
            if commit_transaction:
                transaction.commit()
        else:
            raise ValueError('Lines must be type list')

        
    ## CRITICAL WARNINGS ##
    @property
    def job_done(self):
        text = ''.join(self._lines)
        if 'JOB DONE' in text:
            return True
        else:
            warnings.warn('Not marked "JOB DONE"')
            return False
    
    @property
    def electronically_converged(self):
        text = ''.join(self._lines)
        if 'convergence NOT' in text:
            warnings.warn('SCF convergence NOT achieved.')
            return False
        else:
            return True

    @property
    def cpu_time_exceeded(self):
        text = ''.join(self._lines)
        if 'Maximum CPU time exceeded' in text:
            warnings.warn('Maximum CPU time exceeded.')
            return True
        else:
            return False

    @property
    def max_steps_reached(self):
        text = ''.join(self._lines)
        if 'The maximum number of steps has been reached.' in text:
            warnings.warn('The maximum number of ionic/electronic'
                          ' relaxation steps has been reached.')
            return True
        else:
            return False
    
    @property
    def wentzcovitch_max_reached(self):
        text = ''.join(self._lines)
        if 'iterations completed, stopping' in text:
            warnings.warn('The maximum number of iterations was'
                          ' reached in Wentzcovitch Damped Dynamics.')
            return True
        else:
            return False
    
    @property
    def eigenvalues_converged(self):
        # not sure if this is critical? AZ
        for line in self._lines:
            if 'c_bands' in line and 'eigenvalues not converged' in line:
                warnings.warn('The eigenvalues are not converged')
                return False
            else:
                return True
    
    @property
    def general_error(self):
        text = ''.join(self._lines)
        if '%%%%%%%%%%%%%%' in text:
            warnings.warn('Something probably went very wrong, an error occurred.')
            return True
        else:
            return False
        
    ## MINOR WARNINGS ##
    @property
    def general_warning(self):
        text = ''.join(self._lines)
        if 'Warning' in text:
#             warnings.warn('Something may have gone kind of wrong,'
#                           ' a warning was given. Sometimes this happens when'
#                           ' extra cards are given (e.g. in an ION in an scf'
#                           ' calculation).')
            return True
        else:
            return False
        
    @property
    def deprecated_feature_used(self):
        text = ''.join(self._lines)
        if 'DEPRECATED' in text:
            warnings.warn('You used a deprecated feature, try not to do that in the future.')
            return True
        else:
            return False
    
    @property
    def incommensurate_fft_grid(self):
        text = ''.join(self._lines)
        if 'incommensurate with FFT grid' in text:
            warnings.warn('The FFT grid is incommensurate, so some symmetries may be lost.')
            return True
        else:
            return False
        
    @property
    def scf_correction_too_large(self):
        text = ''.join(self._lines)
        if 'SCF correction compared to forces is too large, reduce conv_thr' in text:
            warnings.warn('The forces are inaccurate (SCF correction is too large): reduce conv_thr')
            return True
        else:
            return False

    ## ERROR / COMPLETION SUMMARY ##
    @property
    def succeeded(self):
        if any([self.cpu_time_exceeded,
                self.max_steps_reached,
                self.wentzcovitch_max_reached,
                self.general_error,
                not self.job_done,
                not self.electronically_converged,
                not self.eigenvalues_converged]):
                return False
        else:
            return True

    ## CALCULATION ONELINERS ##    
    @property
    def spin_polarized(self):
        # input property
        pass
        
    @property
    def bravais_index(self):
        for line in self._lines:
            if 'bravais-lattice index' in line:
                bravais_index = int(line.split()[-1])
                return bravais_index
    
    @property
    def n_electrons(self):
        for line in self._lines:
            if 'number of electrons' in line:
                n_electrons = float(line.split()[-1])
                return n_electrons
            
    @property
    def ke_cutoff(self):
        for line in self._lines:
            if 'kinetic-energy cutoff' in line:
                # ke_cutoff_units = line.split()[-1]
                ke_cutoff = float(line.split()[-2])
                return ke_cutoff
            
    @property
    def convergence_threshold(self):
        for line in self._lines:
            if 'convergence threshold' in line:
                convergence_threshold = float(line.split('=')[-1])
                return convergence_threshold
    
    @property
    def mixing_beta(self):
        for line in self._lines:
            if 'mixing beta' in line:
                mixing_beta = float(line.split('=')[-1])
                return mixing_beta
    
    @property
    def number_of_iterations_used(self):
        for line in self._lines:
            if 'number of iterations used' in line:
                number_of_iterations_used = int(line.split('=')[-1].split()[0])
                return number_of_iterations_used
    
    @property
    def exchange_correlation(self):
        for line in self._lines:
            if 'Exchange-correlation' in line:
                exchange_correlation = line.split('=')[-1].split('(')[0].strip()
                return exchange_correlation
    
    @property
    def n_steps(self):
        for line in self._lines:
            if 'nstep' in line:
                n_steps= int(line.split('=')[-1])
                return n_steps
            
    @property
    def rho_cutoff(self):
        for line in self._lines:
            if 'charge density cutoff' in line:
                # rho_cutoff_units = line.split()[-1]
                rho_cutoff = float(line.split()[-2])
                return rho_cutoff
            
    @property
    def n_atoms(self):
        for line in self._lines:
            if 'number of atoms/cell' in line:
                n_atoms = int(line.split()[-1])
                return n_atoms

    @property
    def n_species(self):
        for line in self._lines:
            if 'number of atomic types' in line:
                n_species = int(line.split()[-1])
                return n_species
            
    @property
    def n_bands(self):
        for line in self._lines:
            if 'number of Kohn-Sham states' in line:
                nbnd = int(line.split('=')[1])
                return nbnd

    @property
    def n_kpoints(self):
        for line in self._lines:
            if 'number of k points' in line:
                nk = int(line.split('=')[1].split()[0])
                # if spin-polarized, QE counts twice
                if self.spin_polarized:
                    nk /= 2
                return nk
            
    @property
    def vdw_correction(self):
        for line in self._lines:
            if 'Carrying out vdW-DF run using the following parameters:' in line:
                vdw_correction = True
                return vdw_correction
        vdw_correction = False
        return vdw_correction
             
    ## INITIAL PROPERTIES ##      
    @property
    def initial_alat(self):
        for line in self._lines:
            if 'lattice parameter (alat)' in line:
                alat = float(line.split('=')[1].split('a.u')[0])
                return alat        
    
    @property
    def initial_volume(self):
        for line in self._lines:
            if 'unit-cell volume' in line:
                initial_volume_bohr = float(line.split()[-2])
                initial_volume_angstrom = initial_volume_bohr * A3_PER_BOHR3
                return initial_volume_angstrom

    @property
    def initial_unit_cell(self):
        for l, line in enumerate(self._lines):
            if 'crystal axes: (cart. coord. in units of alat)' in line:
                initial_unit_cell = []
                i = l + 1
                while self._lines[i].strip():
                    tmp = self._lines[i].strip().split()[3:-1]
                    tmp = [float(j) * self.initial_alat for j in tmp]
                    initial_unit_cell.append(tmp)
                    i += 1
                return initial_unit_cell

    @property
    def initial_atomic_positions(self):
        for l, line in enumerate(self._lines):
            if 'site n.     atom                  positions (cryst. coord.)' in line:
                initial_atomic_positions = []
                i = l + 1
                while self._lines[i].strip():
                    tmp = self._lines[i].strip().split()
                    # site = int(tmp[0])
                    species = tmp[1]
                    position = tmp[6:-1]
                    position = [float(j) for j in position]
                    initial_atomic_positions.append((species, position))
                    i += 1
                return initial_atomic_positions

    @property
    def initial_structure(self):
        initial_unit_cell = self.initial_unit_cell
        initial_atomic_positions = self.initial_atomic_positions
        if (initial_unit_cell and initial_atomic_positions):
            species = [''.join([l for l in i[0] if not l.isdigit()]) for i in initial_atomic_positions]
            positions = [j[1] for j in initial_atomic_positions]
            initial_structure = Structure(initial_unit_cell, species, positions)
            return initial_structure.as_dict()
        else:
            return None

    @property
    def initial_pressure(self):
        for line in self._lines:
            # The header says Ry/bohr**3, but the values are collected
            # from the kbar side of the output
            if 'total   stress  (Ry/bohr**3)' in line:
                line = line.strip().replace('=', ' = ').replace('-', ' -')
                pressure_kbar = float(line.split()[-1])  # kbar
                pressure_gpa = pressure_kbar / 10  # GPa
                return pressure_gpa
        return None


    @property
    def initial_pressure_tensor(self):
        for l, line in enumerate(self._lines):
            # The header says Ry/bohr**3, but the values are collected
            # from the kbar side of the output
            if 'total   stress  (Ry/bohr**3)' in line:
                pressure_tensor = []
                i = l + 1
                while self._lines[i].strip():
                    tmp = self._lines[i].strip().split()[3:]  # kbar
                    tmp = [float(j) / 10 for j in tmp]  # GPa
                    pressure_tensor.append(tmp)
                    i += 1
                return pressure_tensor
        return None


    @property
    def initial_total_energy(self):
        for line in self._lines:
            if '!    total energy' in line:
                energy_ry = float(line.split()[-2])  # Ry/cell
                energy_ev = energy_ry * EV_PER_RY  # eV/cell
                return energy_ev
        return None


    @property
    def initial_enthalpy(self):
        enthalpy_ev = None
        for line in self._lines:
            if 'enthalpy old' in line:
                enthalpy_ry =  float(line.strip().split()[3])  # Ry/cell
                enthalpy_ev = enthalpy_ry * EV_PER_RY  # eV/cell
            if 'enthalpy new' in line:
                enthalpy_ry =  float(line.strip().split()[3])  # Ry/cell
                enthalpy_ev = enthalpy_ry * EV_PER_RY  # eV/cell
            if enthalpy_ev:
                return enthalpy_ev
        return None

    ## FINAL OR LAST PRINTED PROPERTIES ##
    @property
    def final_coordinates_section(self):
        text = ''.join(self._lines)
        reversed__lines = list(reversed(self._lines))
        if 'Begin final coordinates' in text:
            for l, line in enumerate(reversed__lines):
                if 'End final coordinates' in line:
                    # end_l = l
                    i = l
                    while 'Begin final coordinates' not in reversed__lines[i]:
                        i += 1
                    # begin_l = i
                    return list(reversed(reversed__lines[l:i+1]))
        else:
            return None

    @property
    def final_volume(self):
        if self.final_coordinates_section:
            fcs_text = ''.join(self.final_coordinates_section)
            if 'volume' in fcs_text:
                for l, line in enumerate(self.final_coordinates_section):
                    if 'Begin final coordinates' in line:
                        # final_volume_bohr = float(self.final_coordinates_section[l+1].split()[-6])
                        final_volume_angstrom = float(self.final_coordinates_section[l+1].split()[-3])
                        return final_volume_angstrom
            else:
                return None
        else:
            # NEW
            # warnings.warn('{} has no FINAL volume. Returning LAST volume.'.format(self.stdout_path))
            reversed__lines = list(reversed(self._lines))
            for l, line in enumerate(reversed__lines):
                if 'new unit-cell volume' in line:
                    # final_volume_bohr = float(line.strip().split()[-6])
                    final_volume_angstrom = float(line.strip().split()[-3])
                    return final_volume_angstrom
            return None

    @property
    def final_unit_cell(self):
        if self.final_coordinates_section:
            fcs_text = ''.join(self.final_coordinates_section)
            if 'CELL_PARAMETERS' in fcs_text:
                for l, line in enumerate(self.final_coordinates_section):
                    if 'CELL_PARAMETERS' in line:
                        i = l + 1
                        final_unit_cell = []
                        while self.final_coordinates_section[i].strip():
                            tmp_line = self.final_coordinates_section[i]
                            # Angstrom
                            final_unit_cell.append([float(j) for j in   tmp_line.strip().split()])
                            i += 1
                        i += 1
                        return final_unit_cell
            else:
                return None
        else:
            # NEW
            # warnings.warn('{} has no FINAL unit cell. Returning LAST unit cell.'.format(self.stdout_path))
            reversed__lines = list(reversed(self._lines))
            for l, line in enumerate(reversed__lines):
                if 'CELL_PARAMETERS' in line:
                    i = l - 1
                    final_unit_cell = []
                    while reversed__lines[i].strip():
                        tmp_line = reversed__lines[i]
                        final_unit_cell.append([float(j) for j in tmp_line.strip().split()])
                        i -= 1
                    return final_unit_cell
            return None

    @property
    def final_atomic_positions(self):
        if self.final_coordinates_section:
            fcs_text = ''.join(self.final_coordinates_section)
            if 'ATOMIC_POSITIONS' in fcs_text:
                for l, line in enumerate(self.final_coordinates_section):
                    if 'ATOMIC_POSITIONS' in line:
                        i = l+1
                        final_atomic_positions = []
                        while 'End final coordinates' not in self.final_coordinates_section[i]:
                            tmp = self.final_coordinates_section[i].strip().split()
                            species = tmp.pop(0)
                            position = tmp
                            position = [float(j) for j in position]  # crystal (fractional) coords.
                            final_atomic_positions.append((species, position))
                            i += 1
                        return final_atomic_positions
            else:
                return None
        else:
            # NEW
            # warnings.warn('{} has no FINAL atomic positions. Returning LAST atomic positions.'.format(self.stdout_path))
            reversed__lines = list(reversed(self._lines))
            for l, line in enumerate(reversed__lines):
                if 'ATOMIC_POSITIONS' in line:
                    i = l - 1
                    final_atomic_positions = []
                    while reversed__lines[i].strip():
                        tmp = reversed__lines[i].strip().split()
                        species = tmp.pop(0)
                        position = tmp
                        position = [float(j) for j in position]
                        final_atomic_positions.append((species, position))
                        i -= 1
                    return final_atomic_positions
            return None

    @property
    def final_structure(self):
        final_unit_cell = self.final_unit_cell
        final_atomic_positions = self.final_atomic_positions
        if (final_unit_cell and final_atomic_positions):
            species = [''.join([l for l in i[0] if not l.isdigit()]) for i in final_atomic_positions]
            positions = [j[1] for j in final_atomic_positions]
            final_structure = Structure(final_unit_cell, species, positions)
            return final_structure.as_dict()
        else:
            return None

    @property
    def final_pressure(self):
        for line in reversed(self._lines):
            # The header says Ry/bohr**3, but the values are collected
            # from the kbar side of the output
            if 'total   stress  (Ry/bohr**3)' in line:
                line = line.strip().replace('=', ' = ').replace('-', ' -')
                pressure_kbar = float(line.split()[-1])  # kbar
                pressure_gpa = pressure_kbar / 10  # GPa
                return pressure_gpa
        return None

    @property
    def final_pressure_tensor(self):
        reversed__lines = list(reversed(self._lines))
        for l, line in enumerate(reversed__lines):
            # The header says Ry/bohr**3, but the values are collected
            # from the kbar side of the output
            if 'total   stress  (Ry/bohr**3)' in line:
                pressure_tensor = []
                i = l - 1
                while reversed__lines[i].strip():
                    tmp = reversed__lines[i].strip().split()[3:]  # kbar
                    tmp = [float(j) / 10 for j in tmp]  # GPa
                    pressure_tensor.append(tmp)
                    i -= 1
                return pressure_tensor
        return None

    @property
    def final_total_energy(self):
        for line in reversed(self._lines):
            if '!    total energy' in line:
                energy_ry = float(line.split()[-2])  # Ry/cell
                energy_ev = energy_ry * EV_PER_RY  # eV/cell
                return energy_ev
        return None

    @property
    def final_enthalpy(self):
        text = ''.join(self._lines)
        if 'Final enthalpy' in text:
            for line in reversed(self._lines):
                if 'Final enthalpy' in line:
                    final_enthalpy_ry = float(line.split()[-2])  # Ry/cell
                    final_enthalpy_ev = final_enthalpy_ry * EV_PER_RY  # eV/cell
                    return final_enthalpy_ev
        else:
            enthalpy_ev = None
            for line in reversed(self._lines):
                if 'enthalpy old' in line:
                    enthalpy_ry =  float(line.strip().split()[3])  # Ry/cell
                    enthalpy_ev = enthalpy_ry * EV_PER_RY  # eV/cell
                if 'enthalpy new' in line:
                    enthalpy_ry =  float(line.strip().split()[3])  # Ry/cell
                    enthalpy_ev = enthalpy_ry * EV_PER_RY  # eV/cell
                if enthalpy_ev:
                    return enthalpy_ev
            return None

    @property
    def final_total_magnetization(self):
        for line in reversed(self._lines):
            if 'total magnetization' in line:
                total_mag = float(line.split()[-3])  # Bohr mag/cell
                return total_mag
        return None

    @property
    def final_absolute_magnetization(self):
        for line in reversed(self._lines):
            if 'absolute magnetization' in line:
                abs_mag = float(line.split()[-3])  # Bohr mag/cell
                return abs_mag
        return None

    @property
    def final_fermi_energy(self):
        for line in reversed(self._lines):
            if 'the Fermi energy is' in line:
                fermi_energy_ev = float(line.split()[-2])
                return fermi_energy_ev
        return None
    
    @property
    def final_energy(self):
        text = ''.join(self._lines)
        if 'Final energy' in text:
            for line in reversed(self._lines):
                if 'Final energy' in line:
                    energy_ry = float(line.split()[-2])  # Ry/cell
                    energy_ev = energy_ry * EV_PER_RY  # eV/cell
                    return energy_ev
        elif self.final_total_energy:
            return self.final_total_energy
        else:
            return None

    # @property
    # def relax_steps(self):
    #     pass
    #     text = ''.join(self._lines)
    #     step_texts = text.split('Self-consistent Calculation')[1:]
    #     step_lines = [step_text.split('\n') for step_text in step_texts]

    #     for lines in step_lines:
    #         step = {}
    #         for l, line in enumerate(lines):

   
    ## COMPLETION PROPERTIES AND STATS ##
    @property
    def walltime(self):
        for line in reversed(self._lines):
            if 'PWSCF' and 's CPU' and 's WALL' in line:
                walltime = line.split()[-2]
                time = []
                if 'h' in walltime:
                    hours = float(walltime.split('h')[0])
                    time.append(hours)
                    walltime = ''.join(walltime.split('h')[1:])
                else:
                    time.append(0)
                if 'm' in walltime:
                    minutes = float(walltime.split('m')[0])
                    time.append(minutes)
                    walltime = ''.join(walltime.split('m')[1:])
                else:
                    time.append(0)
                if 's' in walltime:
                    seconds = float(walltime.split('s')[0])
                    time.append(seconds)
                else:
                    time.append(0)
                converter = [60**2, 60, 1]
                total_seconds = sum([t * converter[i] for i, t in enumerate(time)])
                return total_seconds
        return None

    ## PROPERTY CATEGORIES ##


    ## CONVENIENCE AND STORAGE ##
    @property
    def output_dict(self):
        dict_ = {
            'job_done': self.job_done,
            'electronically_converged': self.electronically_converged,
            'cpu_time_exceeded': self.cpu_time_exceeded,
            'max_steps_reached': self.max_steps_reached,
            'wentzcovitch_max_reached': self.wentzcovitch_max_reached,
            'eigenvalues_converged': self.eigenvalues_converged,
            'general_error': self.general_error,
            'general_warning': self.general_warning,
            'deprecated_feature_used': self.deprecated_feature_used,
            'incommensurate_fft_grid': self.incommensurate_fft_grid,
            'succeeded': self.succeeded,
            # 'spin_polarized': self.spin_polarized,
            'bravais_index': self.bravais_index,
            # 'n_electrons': self.n_electrons,
            # 'ke_cutoff': self.ke_cutoff,
            # 'convergence_threshold': self.convergence_threshold,
            # 'mixing_beta': self.mixing_beta,
            'number_of_iterations_used': self.number_of_iterations_used,
            # 'exchange_correlation': self.exchange_correlation,
            # 'n_steps': self.n_steps,
            # 'rho_cutoff': self.rho_cutoff,
            # 'n_atoms': self.n_atoms,
            # 'n_species': self.n_species,
            # 'n_bands': self.n_bands,
            # 'n_kpoints': self.n_kpoints,
            # 'vdw_correction': self.vdw_correction,
            # 'initial_alat': self.initial_alat,
            # 'initial_volume': self.initial_volume,
            # 'initial_unit_cell': self.initial_unit_cell,
            # 'initial_atomic_positions': self.initial_atomic_positions,
            'initial_structure': self.initial_structure,
            'initial_pressure': self.initial_pressure,
            'initial_total_energy': self.initial_total_energy,
            'initial_enthalpy': self.initial_enthalpy,
            # 'final_coordinates_section': self.final_coordinates_section,
            # 'final_volume': self.final_volume,
            # 'final_unit_cell': self.final_unit_cell,
            # 'final_atomic_positions': self.final_atomic_positions,
            'final_structure': self.final_structure,
            'final_pressure': self.final_pressure,
            'final_pressure_tensor': self.final_pressure_tensor,
            'final_total_energy': self.final_total_energy,
            'final_enthalpy': self.final_enthalpy,
            'final_absolute_magnetization': self.final_absolute_magnetization,
            'final_fermi_energy': self.final_fermi_energy,
            'final_energy': self.final_energy,
            # 'walltime': self.walltime,           
        }
        return dict_
    
#     def as_dict(self):      
#         dict_ = {'_string': '\n'.join(self._lines),
#                  'stdout_path': self.stdout_path,
#                  **self.output_dict}
#         return dict_

#     # TODO: explicitly return all parsed output parameters
#     @classmethod
#     def from_dict(cls, dict_):
#          return cls('\n'.join(pwout_dict['_lines']),
#                     pwout_dict['stdout_path'])
    
#     @classmethod
#     def from_file(cls, stdout_path):
#         stdout_path = stdout_path
#         with open(stdout_path, 'r') as f:
#             _lines = f.read_lines()
#         return cls(_lines, stdout_path)
