from . import qes
import warnings
import pprint
import numpy as np

from pymatgen import Structure, Lattice, Spin
from pymatgen.electronic_structure.bandstructure import BandStructure, BandStructureSymmLine
from pymatgen.symmetry.bandstructure import HighSymmKpath

EV_PER_RY = 13.6056917253
A_PER_BOHR = 0.52917720859
A3_PER_BOHR3 = A_PER_BOHR ** 3
GPA_PER_EV_A3 = 160.21766208

def _string_to_matrix(string):
    lines = string.strip().split('\n')
    matrix = []
    if len(lines) > 1:
        for line in lines:
            matrix.append(list(map(float, line.strip().split())))
    else:
        matrix = list(map(float, string.strip().split()))
    return matrix

class PWXML(object):
    '''
    Object wrapping automatically generated code from generateDS.py which parses pw.x
        XML output into python objects
    :param xml_string: python string (decoded) of the pw.x XML file
    :param xml_path: string describing the path to the pw.x XML file,
        for bookkeeping
    :param encoding: encoding of the xml_string, used to convert xml_string
        to bytes for the generateDS.py parser
    :param silence: boolean value of whether or not to print the XML file
    :param show_warnings: boolean value of whether or not to catch warnings from the
        generateDS.py parser (often generates a lot of warnings about vector representations
        which are annoying)
    '''
    def __init__(self, xml_string, xml_path=None, encoding='utf-8', silence=True, show_warnings=False):
        self.xml_string = xml_string
        self.xml_path = xml_path
        self.encoding=encoding

        if show_warnings:
            espresso = qes.parseString(inString=bytes(xml_string, self.encoding), silence=silence)  # espressoType
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                espresso = qes.parseString(inString=bytes(xml_string, self.encoding), silence=silence)  # espressoType

        self._output = espresso.output  # outputType
        self._input = espresso.input  # inputType
        self._units = espresso.Units  # str
        self._cputime = espresso.cputime  # int
        self._general_info = espresso.general_info  # infoType
        self._parallel_info = espresso.parallel_info  #infoType
        self._status = espresso.status  # int
        self._step = espresso.step  # list of stepType
        return

    def __repr__(self):
        return pprint.pformat({'encoding': self.encoding,
                               'output': self.output,
                               'input': self.input,
                               'units': self.units,
                               'cputime': self.cputime,
                               'general_info': self.general_info,
                               'parallel_info': self.parallel_info,
                               'status': self.status,
                               'step': self.step})

    @property
    def output(self):
        output_dict = {
            'atomic_species': {
                'ntyp' : self._output.atomic_species.ntyp,
                'pseudo_dir' : self._output.atomic_species.pseudo_dir,
                'species' : [{'name': specie.name,
                              'mass': specie.mass, 
                              'pseudo_file': specie.pseudo_file, 
                              'starting_magnetization': specie.starting_magnetization,
                              'spin_theta': specie.get_spin_teta(),
                              'spin_phi': specie.spin_phi} 
                              for specie in self._output.atomic_species.species]
            },
            'atomic_structure': {
                'alat' : self._output.atomic_structure.get_alat(),
                'atomic_positions' : [{'name': atomic_position.name,
                                       'position': _string_to_matrix(atomic_position.valueOf_), 
                                       'index': atomic_position.index} 
                                       for atomic_position in self._output.atomic_structure.atomic_positions.atom],
                'bravais_index' : self._output.atomic_structure.bravais_index,
                'cell' : [[float(i) for i in self._output.atomic_structure.cell.a1],
                          [float(i) for i in self._output.atomic_structure.cell.a2],
                          [float(i) for i in self._output.atomic_structure.cell.a3]]
                         if self._output.atomic_structure.cell else None,
                'crystal_positions' : self._output.atomic_structure.get_crystal_positions(),
                'nat' : self._output.atomic_structure.nat,
                'wyckoff_positions' : self._output.atomic_structure.get_wyckoff_positions(),
            },
            'band_structure': {
                'fermi_energy' : self._output.band_structure.fermi_energy,
                'highest_occupied_level' : self._output.band_structure.highestOccupiedLevel,
                'ks_energies' : [{'npw': ks.npw,
                                'k_point': {'weight': ks.k_point.weight,
                                            'label': ks.k_point.label,
                                            'valueOf_': _string_to_matrix(ks.k_point.valueOf_)},
                                'eigenvalues': _string_to_matrix(ks.eigenvalues.valueOf_),
                                'occupations': _string_to_matrix(ks.occupations.valueOf_)}
                                for ks in self._output.band_structure.ks_energies],
                'band_lsda' : self._output.band_structure.lsda,
                'nbnd' : self._output.band_structure.nbnd,
                'nbnd_dw' : self._output.band_structure.nbnd_dw,
                'nbnd_up' : self._output.band_structure.nbnd_up,
                'nelec ' : self._output.band_structure.nelec,
                'nks' : self._output.band_structure.nks,
                'noncolin' : self._output.band_structure.noncolin,
                'num_of_atomic_wfc' : self._output.band_structure.num_of_atomic_wfc,
                'occupations_kind' : {'spin': self._output.band_structure.occupations_kind.spin,
                                        'valueOf_': self._output.band_structure.occupations_kind.valueOf_},
                'smearing' : self._output.band_structure.smearing.valueOf_,
                'degauss' : self._output.band_structure.smearing.degauss,
                'spinorbit ' : self._output.band_structure.spinorbit,
                'starting_k_points' : {'monkhorst_pack': {'nk': [self._output.band_structure.starting_k_points.monkhorst_pack.nk1,
                                                                 self._output.band_structure.starting_k_points.monkhorst_pack.nk2,
                                                                 self._output.band_structure.starting_k_points.monkhorst_pack.nk3],
                                                          'k': [self._output.band_structure.starting_k_points.monkhorst_pack.k1,
                                                                self._output.band_structure.starting_k_points.monkhorst_pack.k2,
                                                                self._output.band_structure.starting_k_points.monkhorst_pack.k3],
                                                          'valueOf_': self._output.band_structure.starting_k_points.monkhorst_pack.valueOf_}
                                                          if self._output.band_structure.starting_k_points.monkhorst_pack else None,
                                        'nk': self._output.band_structure.starting_k_points.nk,
                                        'k_point': self._output.band_structure.starting_k_points.k_point}
                                        if self._output.band_structure.starting_k_points else None,
                'two_fermi_energies' : self._output.band_structure.two_fermi_energies,
                'wf_collected' : self._output.band_structure.wf_collected,
            },
            'basis_set': {
                'ecutrho' : self._output.basis_set.ecutrho,
                'ecutwfc' : self._output.basis_set.ecutwfc,
                'fft_box' : self._output.basis_set.fft_box,
                'fft_grid' : [self._output.basis_set.fft_grid.nr1,
                              self._output.basis_set.fft_grid.nr2,
                              self._output.basis_set.fft_grid.nr3]
                              if self._output.basis_set.fft_grid else None,
                'fft_smooth' : [self._output.basis_set.fft_smooth.nr1,
                                self._output.basis_set.fft_smooth.nr2,
                                self._output.basis_set.fft_smooth.nr3]
                                if self._output.basis_set.fft_smooth else None,
                'gamma_only' : self._output.basis_set.gamma_only,
                'ngm' : self._output.basis_set.ngm,
                'ngms' : self._output.basis_set.ngms,
                'npwx' : self._output.basis_set.npwx,
                'reciprocal_lattice' : [[float(i) for i in self._output.basis_set.reciprocal_lattice.b1],
                                        [float(i) for i in self._output.basis_set.reciprocal_lattice.b2],
                                        [float(i) for i in self._output.basis_set.reciprocal_lattice.b3]]
                                       if self._output.basis_set.reciprocal_lattice else None
            },
            'boundary_conditions': {

            },
            'convergence_info': {
                'opt_conv' : {
                    'grad_norm': self._output.convergence_info.opt_conv.grad_norm,
                    'n_opt_steps': self._output.convergence_info.opt_conv.n_opt_steps
                },
                'scf_conv' : {
                    'n_scf_steps': self._output.convergence_info.scf_conv.n_scf_steps,
                    'scf_error': self._output.convergence_info.scf_conv.scf_error
                }
            },
            'dft': {
                'dftU' : self._output.dft.dftU,
                'functional' : self._output.dft.functional,
                'hybrid' : self._output.dft.hybrid,
                'vdW' : self._output.dft.vdW,
            },
            'FCP_force': {

            },
            'FCP_tot_charge': {

            },
            'forces': _string_to_matrix(self._output.forces.valueOf_),
            'magnetization': {
                'absolute_magnetization' : self._output.magnetization.absolute,
                'do_magnetization' : self._output.magnetization.do_magnetization,
                'mag_lsda' : self._output.magnetization.lsda,
                'noncolin' : self._output.magnetization.noncolin,
                'spinorbit' : self._output.magnetization.spinorbit,
                'total_magnetization' : self._output.magnetization.total,
            },
            'stress' : _string_to_matrix(self._output.stress.valueOf_),
            'symmetries': {
                'nrot' : self._output.symmetries.nrot,
                'nsym' : self._output.symmetries.nsym,
                'space_group' : self._output.symmetries.space_group,
                'symmetry' : [{'info': {'name': symmetry.info.name,
                                        'time_reversal': symmetry.info.time_reversal,
                                        'valueOf_': symmetry.info.valueOf_},
                               'rotation': _string_to_matrix(symmetry.rotation.valueOf_),
                               'fractional_translation': [float(i) for i in symmetry.fractional_translation] \
                                    if symmetry.fractional_translation else None,
                               'equivalent_atoms': {'nat': symmetry.equivalent_atoms.nat,
                                                    'valueOf_': symmetry.equivalent_atoms.valueOf_} \
                                                   if symmetry.equivalent_atoms else None
                              } for symmetry in self._output.symmetries.symmetry] \
                             if self._output.symmetries.symmetry else None
            },
            'total_energy': {
                'demet' : self._output.total_energy.demet,
                'eband' : self._output.total_energy.eband,
                'efieldcorr' : self._output.total_energy.efieldcorr,
                'ehart' : self._output.total_energy.ehart,
                'etot' : self._output.total_energy.etot,
                'etxc' : self._output.total_energy.etxc,
                'ewald' : self._output.total_energy.ewald,
                'gatefield_contr' : self._output.total_energy.gatefield_contr,
                'potentiostat_contr' : self._output.total_energy.potentiostat_contr,
                'vtxc' : self._output.total_energy.vtxc,
            }

        }

        return output_dict

    @property
    def input(self):
        input_dict = {
            'atomic_constraints': self._input.atomic_constraints,
            'atomic_species': {
                'ntyp': self._input.atomic_species.ntyp,
                'pseudo_dir': self._input.atomic_species.pseudo_dir,
                'species' : [{'name': specie.name,
                              'mass': specie.mass, 
                              'pseudo_file': specie.pseudo_file, 
                              'starting_magnetization': specie.starting_magnetization,
                              'spin_theta': specie.get_spin_teta(),
                              'spin_phi': specie.spin_phi} 
                              for specie in self._output.atomic_species.species]
            },
            'atomic_structure': {
                'alat' : self._input.atomic_structure.get_alat(),
                'atomic_positions' : [{'name': atomic_position.name,
                                       'position': _string_to_matrix(atomic_position.valueOf_), 
                                       'index': atomic_position.index} 
                                       for atomic_position in self._input.atomic_structure.atomic_positions.atom],
                'bravais_index' : self._input.atomic_structure.bravais_index,
                'cell' : [[float(i) for i in self._input.atomic_structure.cell.a1],
                          [float(i) for i in self._input.atomic_structure.cell.a2],
                          [float(i) for i in self._input.atomic_structure.cell.a3]]
                         if self._input.atomic_structure.cell else None,
                'crystal_positions' : self._input.atomic_structure.get_crystal_positions(),
                'nat' : self._input.atomic_structure.nat,
                'wyckoff_positions' : self._input.atomic_structure.get_wyckoff_positions(),
            },
            'bands': {
                'input_occupations': self._input.bands.inputOccupations,
                'nbnd': self._input.bands.nbnd, 
                'occupations': {
                    'spin': self._input.bands.occupations.spin,
                    'valueOf_': self._input.bands.occupations.valueOf_
                },
                'smearing': {
                    'degauss': self._input.bands.smearing.degauss,
                    'valueOf_': self._input.bands.smearing.valueOf_
                },
                'tot_charge': self._input.bands.tot_charge,
                'tot_magnetization': self._input.bands.tot_magnetization
            },
            'basis': {
                'ecutrho' : self._input.basis.ecutrho,
                'ecutwfc' : self._input.basis.ecutwfc,
                'fft_box' : self._input.basis.fft_box,
                'fft_grid' : [self._input.basis.fft_grid.nr1,
                              self._input.basis.fft_grid.nr2]
                             if self._input.basis.fft_grid else None,
                'crystal_positions' : self._input.atomic_structure.get_crystal_positions(),
                'nat' : self._input.atomic_structure.nat,
                'wyckoff_positions' : self._input.atomic_structure.get_wyckoff_positions(),
            },
            'bands': {
                'input_occupations': self._input.bands.inputOccupations,
                'nbnd': self._input.bands.nbnd, 
                'occupations': {
                    'spin': self._input.bands.occupations.spin,
                    'valueOf_': self._input.bands.occupations.valueOf_
                },
                'smearing': {
                    'degauss': self._input.bands.smearing.degauss,
                    'valueOf_': self._input.bands.smearing.valueOf_
                },
                'tot_charge': self._input.bands.tot_charge,
                'tot_magnetization': self._input.bands.tot_magnetization
            },
            'basis': {
                'ecutrho' : self._input.basis.ecutrho,
                'ecutwfc' : self._input.basis.ecutwfc,
                'fft_box' : self._input.basis.fft_box,
                'fft_grid' : [self._input.basis.fft_grid.nr1,
                                self._input.basis.fft_grid.nr2,
                                self._input.basis.fft_grid.nr3]
                              if self._input.basis.fft_grid else None,
                'fft_smooth' : [self._input.basis.fft_smooth.nr1,
                                self._input.basis.fft_smooth.nr2,
                                self._input.basis.fft_smooth.nr3]
                                if self._input.basis.fft_smooth else None,
                'gamma_only' : self._input.basis.gamma_only,
            },
            'boundary_conditions': {

            },
            'cell_control': {
                'cell_dynamics': self._input.cell_control.cell_dynamics,
                'cell_factor': self._input.cell_control.cell_factor,
                'fix_area': self._input.cell_control.fix_area,
                'fix_volume': self._input.cell_control.fix_volume,
                'fix_xy': self._input.cell_control.fix_xy,
                'free_cell': _string_to_matrix(self._input.cell_control.free_cell.valueOf_),
                'isotropic': self._input.cell_control.isotropic,
                'pressure': self._input.cell_control.pressure,
                'wmass': self._input.cell_control.wmass
            },
            'control_variables': {
                'calculation': self._input.control_variables.calculation,
                'disk_io': self._input.control_variables.disk_io, 
                'etot_conv_thr': self._input.control_variables.etot_conv_thr,
                'forc_conv_thr': self._input.control_variables.forc_conv_thr,
                'forces': self._input.control_variables.forces,
                'max_seconds': self._input.control_variables.max_seconds,
                'nstep': self._input.control_variables.nstep,
                'outdir': self._input.control_variables.outdir,
                'prefix': self._input.control_variables.prefix,
                'press_conv_thr': self._input.control_variables.press_conv_thr,
                'print_every': self._input.control_variables.print_every,
                'pseudo_dir': self._input.control_variables.pseudo_dir,
                'restart_mode': self._input.control_variables.restart_mode,
                'stress': self._input.control_variables.stress,
                'title': self._input.control_variables.title,
                'verbosity': self._input.control_variables.verbosity,
                'wf_collect': self._input.control_variables.wf_collect 
            },
            'dft': {
                'dftU' : self._input.dft.dftU,
                'functional' : self._input.dft.functional,
                'hybrid' : self._input.dft.hybrid,
                'vdW' : self._input.dft.vdW,
            },
            'ekin_functional': {

            },
            'electric_field': {

            },
            'electron_control': {
                'conv_thr': self._input.electron_control.conv_thr,
                'diago_cg_maxiter': self._input.electron_control.diago_cg_maxiter,
                'diago_david_ndim': self._input.electron_control.diago_david_ndim,
                'diago_full_acc': self._input.electron_control.diago_full_acc,
                'diago_thr_init': self._input.electron_control.diago_thr_init,
                'diagonalization': self._input.electron_control.diagonalization,
                'max_nstep': self._input.electron_control.max_nstep,
                'mixing_beta': self._input.electron_control.mixing_beta,
                'mixing_mode': self._input.electron_control.mixing_mode,
                'mixing_ndim': self._input.electron_control.mixing_ndim,
                'real_space_q': self._input.electron_control.real_space_q,
                'tbeta_smoothing': self._input.electron_control.tbeta_smoothing,
                'tq_smoothing': self._input.electron_control.tq_smoothing 
            },
            'external_atomic_forces': {

            },
            'free_positions': _string_to_matrix(self._input.free_positions.valueOf_),
            'ion_control': {
                'bfgs': {
                    'ndim': self._input.ion_control.bfgs.ndim,
                    'trust_radius_init': self._input.ion_control.bfgs.trust_radius_init,
                    'trust_radius_max': self._input.ion_control.bfgs.trust_radius_max,
                    'trust_radius_min': self._input.ion_control.bfgs.trust_radius_min,
                    'w1': self._input.ion_control.bfgs.w1,
                    'w2': self._input.ion_control.bfgs.w2
                },
                'ion_dynamics': self._input.ion_control.ion_dynamics,
                'md': self._input.ion_control.md,
                'refold_pos': self._input.ion_control.refold_pos,
                'remove_rigid_rot': self._input.ion_control.remove_rigid_rot,
                'upscale': self._input.ion_control.upscale
            },
            'k_points_IBZ': {
                'k_point': self._input.k_points_IBZ.k_point,
                'monkhorst_pack': {'nk': [self._input.k_points_IBZ.monkhorst_pack.nk1,
                                          self._input.k_points_IBZ.monkhorst_pack.nk2,
                                          self._input.k_points_IBZ.monkhorst_pack.nk3],
                                    'k': [self._input.k_points_IBZ.monkhorst_pack.k1,
                                          self._input.k_points_IBZ.monkhorst_pack.k2,
                                          self._input.k_points_IBZ.monkhorst_pack.k3],
                                    'valueOf_': self._input.k_points_IBZ.monkhorst_pack.valueOf_}
                                   if self._input.k_points_IBZ.monkhorst_pack else None,
                'nk': self._input.k_points_IBZ.nk
            },
            'spin': {
                'lsda': self._input.spin.lsda,
                'noncolin': self._input.spin.noncolin,
                'spinorbit': self._input.spin.spinorbit
            },
            'spin_constraints': {

            },
            'starting_atomic_velocities': {

            },
            'symmetry_flags': {
                'force_symmorphic': self._input.symmetry_flags.force_symmorphic,
                'no_t_rev': self._input.symmetry_flags.no_t_rev,
                'noinv': self._input.symmetry_flags.noinv,
                'nosym': self._input.symmetry_flags.nosym,
                'nosym_evc': self._input.symmetry_flags.nosym_evc,
                'use_all_frac': self._input.symmetry_flags.use_all_frac 
            },
        }
        return input_dict

    @property
    def units(self):
        return self._units

    @property
    def cputime(self):
        return self._cputime

    @property
    def general_info(self):
        general_info_dict = {
            'created': {
                'date': self._general_info.created.DATE,
                'time': self._general_info.created.TIME,
                'datetime': self._general_info.created.valueOf_
            },
            'creator': {
                'name': self._general_info.creator.NAME,
                'version': self._general_info.creator.VERSION,
                'creator': self._general_info.creator.valueOf_
            },
            'job': self._general_info.job,
            'xml_format': {
                'name': self._general_info.xml_format.NAME,
                'version': self._general_info.xml_format.VERSION,
                'format': self._general_info.xml_format.valueOf_
            }
        }
        return general_info_dict

    @property
    def parallel_info(self):
        parallel_info_dict = {
            'nbgrp': self._parallel_info.nbgrp,
            'ndiag': self._parallel_info.ndiag,
            'npool': self._parallel_info.npool,
            'nprocs': self._parallel_info.nprocs,
            'ntasks': self._parallel_info.ntasks,
            'nthreads': self._parallel_info.nthreads,
        }
        return parallel_info_dict

    @property
    def status(self):
        return self._status

    @property
    def step(self):
        step_list = [
            {'n_step': step.n_step,
            'scf_conv': {
                'n_scf_steps': step.scf_conv.n_scf_steps,
                'scf_error': step.scf_conv.scf_error
             },
             'atomic_structure': {
                'alat' : step.atomic_structure.get_alat(),
                'atomic_positions' : [{'name': atomic_position.name,
                                       'position': _string_to_matrix(atomic_position.valueOf_), 
                                       'index': atomic_position.index} 
                                       for atomic_position in step.atomic_structure.atomic_positions.atom],
                'bravais_index' : step.atomic_structure.bravais_index,
                'cell' : [[float(i) for i in step.atomic_structure.cell.a1],
                          [float(i) for i in step.atomic_structure.cell.a2],
                          [float(i) for i in step.atomic_structure.cell.a3]]
                         if step.atomic_structure.cell else None,
                'crystal_positions' : step.atomic_structure.get_crystal_positions(),
                'nat' : step.atomic_structure.nat,
                'wyckoff_positions' : step.atomic_structure.get_wyckoff_positions(),
            },
            'total_energy': {
                'demet' : step.total_energy.demet,  # 
                'eband' : step.total_energy.eband,  # 
                'efieldcorr' : step.total_energy.efieldcorr,  # 
                'ehart' : step.total_energy.ehart,  # hartree energy
                'etot' : step.total_energy.etot,  # total energy
                'etxc' : step.total_energy.etxc,  # total exchange-correlation energy
                'ewald' : step.total_energy.ewald,  # 
                'gatefield_contr' : step.total_energy.gatefield_contr,  # 
                'potentiostat_contr' : step.total_energy.potentiostat_contr,  # 
                'vtxc' : step.total_energy.vtxc,  # 
            },
            'forces': _string_to_matrix(step.forces.valueOf_),
            'stress': step.stress,
            'FCP_force': step.FCP_force,
            'FCP_tot_charge': step.FCP_tot_charge}
            for step in self._step]

        return step_list

   
    # TODO: looks like a lot of these are 1/2 the value in the stdout
    ## crystal structure ##
    # Input units (?)
    @property
    def alat(self):
        return self.output['atomic_structure']['alat']

    # Input units (?)
    @property
    def cell(self):
        return self.output['atomic_structure']['cell']

    # Units unkown
    @property
    def atomic_positions(self):
        return self.output['atomic_structure']['atomic_positions']
    
    # 2pi/alat
    # @property
    # def reciprocal_lattice(self):
    #     return self.output['basis_set']['reciprocal_lattice']
    # 2pi/input unit
    @property
    def reciprocal_lattice(self):
        lattice = np.array(self.cell)
        reciprocal_lattice = 2 * np.pi * np.linalg.inv(lattice)
        return reciprocal_lattice

    ## energy ##
    # Parser returns Ha
    # This function returns Ry
    @property
    def total_energy(self):
        return self.output['total_energy']['etot'] * 2

    ## magnetization ##
    @property
    def absolute_magnetization(self):
        return self.output['magnetization']['absolute_magnetization']

    @property
    def total_magnetization(self):
        return self.output['magnetization']['total_magnetization']

    ## forces and stresses ##

    # Unit unknown
    @property
    def forces(self):
        return self.output['forces']

    # Parser returns Ha/bohr**3
    # This function returns in GPa
    @property
    def stress_tensor(self):
        tensor_ry_bohr3 = np.array(self.output['stress']) * 2
        tensor_ev_a3 = tensor_ry_bohr3 / A3_PER_BOHR3 * EV_PER_RY
        tensor_gpa = tensor_ev_a3 * GPA_PER_EV_A3
        return tensor_gpa.tolist()

    # TODO: check that the trace is the appropriate measure
    # This function returns in GPa
    @property
    def total_stress(self):
        return np.trace(self.stress_tensor)

    ## band structure ##
    # Parser returns Ha
    # This function returns eV
    @property
    def fermi_energy(self):
        return self.output['band_structure']['fermi_energy'] * EV_PER_RY * 2

    @property
    def k_points(self):
        k_points = []
        for ks_state in self.output['band_structure']['ks_energies']:
            k_points.append(ks_state['k_point']['valueOf_'])
        return k_points

    @property
    def k_point_weights(self):
        weights = []
        for ks_state in self.output['band_structure']['ks_energies']:
            weights.append(ks_state['k_point']['weight'])
        return weights

    # Parser returns Ha
    # This function returns in eV
    @property
    def eigenvalues(self):
        eigenvalues = []
        for ks_state in self.output['band_structure']['ks_energies']:
            eigen = np.array(ks_state['eigenvalues']) * EV_PER_RY * 2
            eigenvalues.append(eigen.tolist())
        return eigenvalues

    @property
    def occupations(self):
        occupations = []
        for ks_state in self.output['band_structure']['ks_energies']:
            occupations.append(ks_state['occupations'])
        return occupations
    
    
    ## ANALYSIS METHODS ##
    def get_Lattice(self):
        return Lattice(matrix=self.cell)

    def get_Structure(self):
        return Structure(lattice=self.get_Lattice(),
                         species=[s['name'] for s in self.atomic_positions],
                         coords=[s['position'] for s in self.atomic_positions])

    def get_reciprocal_Lattice(self):
        return Lattice(matrix=self.reciprocal_lattice)

    # TODO: add support for spin polarized calculations
    def get_BandStructure(self):
        eigenvalues = self.eigenvalues
        eigendict = {Spin.up: eigenvalues} 
        return BandStructure(efermi=self.fermi_energy,
                             eigenvals=eigendict,
                             kpoints=self.k_points,
                             structure=self.get_Structure(),
                             lattice=self.get_reciprocal_Lattice())

    # TODO: add support for spin polarized calculations
    def get_BandStructureSymmLine(self):
        eigenvalues = self.eigenvalues
        eigendict = {Spin.up: eigenvalues} 
        highsymmkpath = HighSymmKpath(self.get_Structure().get_primitive_structure()).kpath
        return BandStructureSymmLine(efermi=self.fermi_energy,
                             eigenvals=eigendict,
                             kpoints=self.k_points,
                             structure=self.get_Structure(),
                             labels_dict=highsymmkpath['kpoints'],
                             lattice=self.get_reciprocal_Lattice())

    # def get_DOS(self):
    #     return DOS(efermi=self.fermi_energy,
    #                densities=self.k_point_weights,
    #                energies=


    def get_band_gap():
        return self.get_BandStructure.get_band_gap()['energy']

    def is_direct_band_gap():
        return self.get_BandStructure.get_band_gap()['direct']

    def get_direct_band_gap():
        return self.get_BandStructure.get_direct_band_gap()

    def is_metal():
        return self.get_BandStructure.is_metal()

    def get_cbm():
        return self.get_BandStructure.get_cbm()

    def get_vbm():
        return self.get_BandStructure.get_vbm()

    
    
    @classmethod
    def from_dict(cls, pwxml_dict, silence=True, show_warnings=False):
        return cls(xml_string=pwxml_dict['xml_string'],
                   xml_path=pwxml_dict['xml_path'],
                   encoding=pwxml_dict['encoding'],
                   silence=silence, show_warnings=show_warnings)

    @classmethod
    def from_file(cls, xml_path, encoding='utf-8', silence=True, show_warnings=False):
        with open(xml_path, 'r') as f:
            xml_string = f.read()
        return cls(xml_string=xml_string, xml_path=xml_path, encoding=encoding,
                   silence=silence, show_warnings=show_warnings)

    def as_dict(self):
        pwxml_dict = {'xml_string': self.xml_string,
                      'xml_path': self.xml_path,
                      'encoding': self.encoding,
                      'output': self.output,
                      'input': self.input,
                      'units': self.units,
                      'cputime': self.cputime,
                      'general_info': self.general_info,
                      'parallel_info': self.parallel_info,
                      'status': self.status,
                      'step': self.step}
        return pwxml_dict
