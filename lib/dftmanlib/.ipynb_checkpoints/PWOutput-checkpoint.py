import warnings
from pymatgen import Structure

A_PER_BOHR = 0.52917720859
A3_PER_BOHR3 = A_PER_BOHR ** 3
EV_PER_RY = 13.6056917253

class PWOutput():
    '''
    Class which parses pw.x standard output into useful physical and 
        simulation properties
    :param stdout_string: python string (decoded) of the standard output from a pw.x simulation
    :param stdout_path: string describing the path to the standard output file from pw.x,
        used for bookkeeping
    '''
    def __init__(self, stdout_string, stdout_path=None):
        self.stdout_path = stdout_path
        self.stdout_lines = stdout_string.split('\n')
        self.critical_warnings = {'job_done': self.check_job_done(),
                                  'electronically_converged': self.check_electronic_convergence(),
                                  'cpu_time_exceeded': self.check_cpu_time(),
                                  'max_steps_reached': self.check_max_steps(),
                                  'max_wentzcovitch_iterations': self.check_wentzcovitch(),
                                  'eigenvalues_converged': self.check_eigenvalues(),
                                  'general_error': self.check_general_error(),
                                 }
        self.minor_warnings = {'general_warning': self.check_general_warning(),
                               'used_deprecated': self.check_deprecated(),
                               'incommensurate_fft_grid': self.check_fft_grid(),
                               'large_scf_correction': self.check_scf_correction(),
                              }
        self.success = self.check_success()
        return

    def __repr__(self):
        # success = str(self.check_success())
        # structure = 
        # energy = 
        # stress = 
        # forces = 
        pass 
                          
    ## CRITICAL WARNINGS ##
    def check_job_done(self):
        text = ''.join(self.stdout_lines)
        if 'JOB DONE' in text:
            return True
        else:
            warnings.warn('Not marked "JOB DONE"')
            return False

    def check_electronic_convergence(self):
        text = ''.join(self.stdout_lines)
        if 'convergence NOT' in text:
            warnings.warn('SCF convergence NOT achieved.')
            return False
        else:
            return True

    def check_cpu_time(self):
        text = ''.join(self.stdout_lines)
        if 'Maximum CPU time exceeded' in text:
            warnings.warn('Maximum CPU time exceeded.')
            return True
        else:
            return False

    def check_max_steps(self):
        text = ''.join(self.stdout_lines)
        if 'The maximum number of steps has been reached.' in text:
            warnings.warn('The maximum number of ionic/electronic relaxation steps has been reached.')
            return True
        else:
            return False
        
    def check_wentzcovitch(self):
        text = ''.join(self.stdout_lines)
        if 'iterations completed, stopping' in text:
            warnings.warn('The maximum number of iterations was reached in Wentzcovitch Damped Dynamics.')
            return True
        else:
            return False
        
    def check_eigenvalues(self):
        # not sure if this is critical? AZ
        for line in self.stdout_lines:
            if 'c_bands' in line and 'eigenvalues not converged' in line:
                warnings.warn('The eigenvalues are not converged')
                return False
            else:
                return True
        
    def check_general_error(self):
        text = ''.join(self.stdout_lines)
        if '%%%%%%%%%%%%%%' in text:
            warnings.warn('Something probably went very wrong, an error occurred.')
            return True
        else:
            return False
        
    ## MINOR WARNINGS ##
    def check_general_warning(self):
        text = ''.join(self.stdout_lines)
        if 'Warning' in text:
            warnings.warn('Something probably went kind of wrong, a warning was given.')
            return True
        else:
            return False
        
    def check_deprecated(self):
        text = ''.join(self.stdout_lines)
        if 'DEPRECATED' in text:
            warnings.warn('You used a deprecated feature, try not to do that in the future.')
            return True
        else:
            return False
        
    def check_fft_grid(self):
        text = ''.join(self.stdout_lines)
        if 'incommensurate with FFT grid' in text:
            warnings.warn('The FFT grid is incommensurate, so some symmetries may be lost.')
            return True
        else:
            return False
        
    def check_scf_correction(self):
        text = ''.join(self.stdout_lines)
        if 'SCF correction compared to forces is too large, reduce conv_thr' in text:
            warnings.warn('The forces are inaccurate (SCF correction is too large): reduce conv_thr')
            return True
        else:
            return False

    ## ERROR / COMPLETION SUMMARY ##
    def check_success(self):
        if any([self.critical_warnings['cpu_time_exceeded'],
                self.critical_warnings['max_steps_reached'],
                self.critical_warnings['max_wentzcovitch_iterations'],
                self.critical_warnings['general_error'],
                not self.critical_warnings['job_done'],
                not self.critical_warnings['electronically_converged'],
                not self.critical_warnings['eigenvalues_converged']]):
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
        for line in self.stdout_lines:
            if 'bravais-lattice index' in line:
                bravais_index = int(line.split()[-1])
                return bravais_index
    
    @property
    def n_electrons(self):
        for line in self.stdout_lines:
            if 'number of electrons' in line:
                n_electrons = float(line.split()[-1])
                return n_electrons
            
    @property
    def ke_cutoff(self):
        for line in self.stdout_lines:
            if 'kinetic-energy cutoff' in line:
                # ke_cutoff_units = line.split()[-1]
                ke_cutoff = float(line.split()[-2])
                return ke_cutoff
            
    @property
    def convergence_threshold(self):
        for line in self.stdout_lines:
            if 'convergence threshold' in line:
                convergence_threshold = float(line.split('=')[-1])
                return convergence_threshold
    
    @property
    def mixing_beta(self):
        for line in self.stdout_lines:
            if 'mixing beta' in line:
                mixing_beta = float(line.split('=')[-1])
                return mixing_beta
    
    @property
    def number_of_iterations_used(self):
        for line in self.stdout_lines:
            if 'number of iterations used' in line:
                number_of_iterations_used = int(line.split('=')[-1].split()[0])
                return number_of_iterations_used
    
    @property
    def exchange_correlation(self):
        for line in self.stdout_lines:
            if 'Exchange-correlation' in line:
                exchange_correlation = line.split('=')[-1].split('(')[0].strip()
                return exchange_correlation
    
    @property
    def n_steps(self):
        for line in self.stdout_lines:
            if 'nstep' in line:
                n_steps= int(line.split('=')[-1])
                return n_steps
            
    @property
    def rho_cutoff(self):
        for line in self.stdout_lines:
            if 'charge density cutoff' in line:
                # rho_cutoff_units = line.split()[-1]
                rho_cutoff = float(line.split()[-2])
                return rho_cutoff
            
    @property
    def n_atoms(self):
        for line in self.stdout_lines:
            if 'number of atoms/cell' in line:
                n_atoms = int(line.split()[-1])
                return n_atoms

    @property
    def n_species(self):
        for line in self.stdout_lines:
            if 'number of atomic types' in line:
                n_species = int(line.split()[-1])
                return n_species
            
    @property
    def n_bands(self):
        for line in self.stdout_lines:
            if 'number of Kohn-Sham states' in line:
                nbnd = int(line.split('=')[1])
                return nbnd

    @property
    def n_kpoints(self):
        for line in self.stdout_lines:
            if 'number of k points' in line:
                nk = int(line.split('=')[1].split()[0])
                # if spin-polarized, QE counts twice
                if self.spin_polarized:
                    nk /= 2
                return nk
            
    @property
    def vdw_correction(self):
        for line in self.stdout_lines:
            if 'Carrying out vdW-DF run using the following parameters:' in line:
                vdw_correction = True
                return vdw_correction
        vdw_correction = False
        return vdw_correction
             
    ## INITIAL PROPERTIES ##      
    @property
    def initial_alat(self):
        for line in self.stdout_lines:
            if 'lattice parameter (alat)' in line:
                alat = float(line.split('=')[1].split('a.u')[0])
                return alat        
    
    @property
    def initial_volume(self):
        for line in self.stdout_lines:
            if 'unit-cell volume' in line:
                initial_volume_bohr = float(line.split()[-2])
                initial_volume_angstrom = initial_volume_bohr * A3_PER_BOHR3
                return initial_volume_angstrom

    @property
    def initial_unit_cell(self):
        for l, line in enumerate(self.stdout_lines):
            if 'crystal axes: (cart. coord. in units of alat)' in line:
                initial_unit_cell = []
                i = l + 1
                while self.stdout_lines[i].strip():
                    tmp = self.stdout_lines[i].strip().split()[3:-1]
                    tmp = [float(j) * self.initial_alat for j in tmp]
                    initial_unit_cell.append(tmp)
                    i += 1
                return initial_unit_cell

    @property
    def initial_atomic_positions(self):
        for l, line in enumerate(self.stdout_lines):
            if 'site n.     atom                  positions (cryst. coord.)' in line:
                initial_atomic_positions = []
                i = l + 1
                while self.stdout_lines[i].strip():
                    tmp = self.stdout_lines[i].strip().split()
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
        for line in self.stdout_lines:
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
        for l, line in enumerate(self.stdout_lines):
            # The header says Ry/bohr**3, but the values are collected
            # from the kbar side of the output
            if 'total   stress  (Ry/bohr**3)' in line:
                pressure_tensor = []
                i = l + 1
                while self.stdout_lines[i].strip():
                    tmp = self.stdout_lines[i].strip().split()[3:]  # kbar
                    tmp = [float(j) / 10 for j in tmp]  # GPa
                    pressure_tensor.append(tmp)
                    i += 1
                return pressure_tensor
        return None


    @property
    def initial_total_energy(self):
        for line in self.stdout_lines:
            if '!    total energy' in line:
                energy_ry = float(line.split()[-2])  # Ry/cell
                energy_ev = energy_ry * EV_PER_RY  # eV/cell
                return energy_ev
        return None


    @property
    def initial_enthalpy(self):
        enthalpy_ev = None
        for line in self.stdout_lines:
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
        text = ''.join(self.stdout_lines)
        reversed_stdout_lines = list(reversed(self.stdout_lines))
        if 'Begin final coordinates' in text:
            for l, line in enumerate(reversed_stdout_lines):
                if 'End final coordinates' in line:
                    # end_l = l
                    i = l
                    while 'Begin final coordinates' not in reversed_stdout_lines[i]:
                        i += 1
                    # begin_l = i
                    return list(reversed(reversed_stdout_lines[l:i+1]))
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
            warnings.warn('{} has no FINAL volume. Returning LAST volume.'.format(self.stdout_path))
            reversed_stdout_lines = list(reversed(self.stdout_lines))
            for l, line in enumerate(reversed_stdout_lines):
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
                            final_unit_cell.append([float(j) for j in tmp_line.strip().split()])
                            i += 1
                        i += 1
                        return final_unit_cell
            else:
                return None
        else:
            # NEW
            warnings.warn('{} has no FINAL unit cell. Returning LAST unit cell.'.format(self.stdout_path))
            reversed_stdout_lines = list(reversed(self.stdout_lines))
            for l, line in enumerate(reversed_stdout_lines):
                if 'CELL_PARAMETERS' in line:
                    i = l - 1
                    final_unit_cell = []
                    while reversed_stdout_lines[i].strip():
                        tmp_line = reversed_stdout_lines[i]
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
            warnings.warn('{} has no FINAL atomic positions. Returning LAST atomic positions.'.format(self.stdout_path))
            reversed_stdout_lines = list(reversed(self.stdout_lines))
            for l, line in enumerate(reversed_stdout_lines):
                if 'ATOMIC_POSITIONS' in line:
                    i = l - 1
                    final_atomic_positions = []
                    while reversed_stdout_lines[i].strip():
                        tmp = reversed_stdout_lines[i].strip().split()
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
        for line in reversed(self.stdout_lines):
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
        reversed_stdout_lines = list(reversed(self.stdout_lines))
        for l, line in enumerate(reversed_stdout_lines):
            # The header says Ry/bohr**3, but the values are collected
            # from the kbar side of the output
            if 'total   stress  (Ry/bohr**3)' in line:
                pressure_tensor = []
                i = l - 1
                while reversed_stdout_lines[i].strip():
                    tmp = reversed_stdout_lines[i].strip().split()[3:]  # kbar
                    tmp = [float(j) / 10 for j in tmp]  # GPa
                    pressure_tensor.append(tmp)
                    i -= 1
                return pressure_tensor
        return None

    @property
    def final_total_energy(self):
        for line in reversed(self.stdout_lines):
            if '!    total energy' in line:
                energy_ry = float(line.split()[-2])  # Ry/cell
                energy_ev = energy_ry * EV_PER_RY  # eV/cell
                return energy_ev
        return None

    @property
    def final_enthalpy(self):
        text = ''.join(self.stdout_lines)
        if 'Final enthalpy' in text:
            for line in reversed(self.stdout_lines):
                if 'Final enthalpy' in line:
                    final_enthalpy_ry = float(line.split()[-2])  # Ry/cell
                    final_enthalpy_ev = final_enthalpy_ry * EV_PER_RY  # eV/cell
                    return final_enthalpy_ev
        else:
            enthalpy_ev = None
            for line in reversed(self.stdout_lines):
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
        for line in reversed(self.stdout_lines):
            if 'total magnetization' in line:
                total_mag = float(line.split()[-3])  # Bohr mag/cell
                return total_mag
        return None

    @property
    def final_absolute_magnetization(self):
        for line in reversed(self.stdout_lines):
            if 'absolute magnetization' in line:
                abs_mag = float(line.split()[-3])  # Bohr mag/cell
                return abs_mag
        return None

    @property
    def final_fermi_energy(self):
        for line in reversed(self.stdout_lines):
            if 'the Fermi energy is' in line:
                fermi_energy_ev = float(line.split()[-2])
                return fermi_energy_ev
        return None
    
    @property
    def final_energy(self):
        text = ''.join(self.stdout_lines)
        if 'Final energy' in text:
            for line in reversed(self.stdout_lines):
                if 'Final energy' in line:
                    energy_ry = float(line.split()[-2])  # Ry/cell
                    energy_ev = energy_ry * EV_PER_RY  # eV/cell
                    return energy_ev
        else:
            return None

    # @property
    # def relax_steps(self):
    #     pass
    #     text = ''.join(self.stdout_lines)
    #     step_texts = text.split('Self-consistent Calculation')[1:]
    #     step_lines = [step_text.split('\n') for step_text in step_texts]

    #     for lines in step_lines:
    #         step = {}
    #         for l, line in enumerate(lines):

   
    ## COMPLETION PROPERTIES AND STATS ##
    @property
    def walltime(self):
        for line in reversed(self.stdout_lines):
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
    def as_dict(self):
        dict_ = {'stdout_lines': self.stdout_lines,
                 'stdout_path': self.stdout_path}
        return dict_

    # TODO: explicitly return all parsed output parameters
    @classmethod
    def from_dict(cls, dict_):
         return cls('\n'.join(pwout_dict['stdout_lines']),
                    pwout_dict['stdout_path'])
    
    @classmethod
    def from_file(cls, stdout_path):
        stdout_path = stdout_path
        with open(stdout_path, 'r') as f:
            stdout_lines = f.readstdout_lines()
        return cls(stdout_lines, stdout_path)
