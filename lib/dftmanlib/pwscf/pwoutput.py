import re
import numpy as np

def _stress_post(match):
    lines = match.strip().split('\n')
    matrix = np.array([[float(stress)
                        for stress in line.strip().split()]
                       for line in lines])
    stress_kbar = matrix[:,[3,4,5]].tolist()
    return stress_kbar

def _atomic_positions_post(match):
    lines = match.strip().split('\n')
    positions = []
    for line in lines:
        line = line.strip()
        if len(line.split()) == 4:
            specie, x, y, z = line.strip().split()
            position = (specie, [float(pos)
                                 for pos in [x, y, z]])
            positions.append(position)
    return positions

def _cell_parameters_post(match):
    lines = match.strip().split('\n')
    matrix = [[float(param)
               for param in line.strip().split()]
              for line in lines]
    return matrix

def _force_post(match):
    atom = int(match[0])
    type_ = int(match[1])
    force = [float(f) for f in match[2].strip().split()]
    return {'atom': atom, 'type': type_, 'force': force}

def _bands_post(match):
    k_re = re.compile('k\s+=\s+([\s\d\.\-]+)')
    bands_re = re.compile('bands\s+\(ev\)\:\n+([\s\d\-\.]+)', re.MULTILINE)
    occupations_re = re.compile('occupation numbers\s+\n([\s\d\.]+)', re.MULTILINE)

    k = k_re.findall(match)
    k = [[float(j) for j in i.replace('-', ' -').strip().split()] for i in k]
    bands = bands_re.findall(match)
    bands = [[float(j) for j in i.strip().split()] for i in bands]
    occupations = occupations_re.findall(match)
    occupations = [[float(j) for j in i.strip().split()] for i in occupations]

    return {'kpoints': k, 'bands': bands, 'occupations': occupations}

def _kpoints_post(match):
    lines = match.strip().split('\n')

    kpoints = []
    for line in lines:
        line = line.strip().split()
        index = int(line[1].strip(')'))
        x, y, z = [float(i.strip('),')) for i in line[4:7]]
        weight = float(line[-1])
        kpoints.append({'index': index,
                        'coords': [x, y, z],
                        'weight': weight})
    return kpoints

def _initial_atomic_positions_post(match):
    lines = match.strip().split('\n')
    positions = []
    for line in lines:
        line = line.split()
        site = int(line[0])
        specie = line[1]
        coords = [float(i) for i in [6, 7, 8]]
        positions.append((specie, coords))

    return positions

patterns = {
    'energy': {
        'pattern': r'total energy\s+=\s+([\d\.\-]+)\s+Ry',
        'flags': [],
        'postprocess': float,
    },
    'final_energy': {
        'pattern': r'!\s+total energy\s+=\s+([\d\.\-]+)\s+Ry',
        'flags': [],
        'postprocess': float,
    },
    'enthalpy': {
        'pattern': r'enthalpy new\s+=\s+([\d\.\-]+)\s+Ry',
        'flags': [],
        'postprocess': float,
    },
    'final_enthalpy': {
        'pattern': r'Final enthalpy\s+=\s+([\d\.\-]+)\s+Ry',
        'flags': [],
        'postprocess': float,
    },
    'density': {
        'pattern': r'density\s+=\s+([\d\.]+)\s+g\/cm\^3',
        'flags': [],
        'postprocess': float,
    },
    'warning': {
        'pattern': r'Warning:\s+([\w\s\/\&]+)$',
        'flags': [re.MULTILINE],
        'postprocess': lambda x: str(x).strip(),
    },
    'total_magnetization': {
        'pattern': r'total magnetization\s+=\s+([\d\.\-]+)',
        'flags': [],
        'postprocess': float,
    },
    'absolute_magnetization': {
        'pattern': r'absolute magnetization\s+=\s+([\d\.\-]+)',
        'flags': [],
        'postprocess': float,
    },
    'total_stress': {
        'pattern': r'total\s+stress\s+\(Ry\/bohr\*\*3\)\s+\(kbar\)\s+P=\s+([\d\.\-]+)',
        'flags': [],
        'postprocess': float,
    },
    'stress': {
        'pattern': r'total\s+stress\s+\(Ry\/bohr\*\*3\)\s+\(kbar\)\s+P=\s+[\d\.\-]+\n([\s\d\.\-]+)\n',
        'flags': [re.MULTILINE],
        'postprocess': _stress_post,
    },
    'total_force': {
        'pattern': r'Total force\s+=\s+([\d\.\-]+)',
        'flags': [],
        'postprocess': float,
    },
    'force': {
        'pattern': r'Forces acting on atoms \(cartesian axes, Ry\/au\)\:\n\n\s+atom\s+([\d]+)\s+type\s+([\d]+)\s+force\s+=\s+([\s\d\.\-]+)',
        'flags': [re.MULTILINE],
        'postprocess': _force_post,
    },
    'bands_data': {
        'pattern': r'End of self\-consistent calculation\n\n(.*?)the Fermi energy is',
        'flags': [re.DOTALL],
        'postprocess': _bands_post,
    },
    'fermi_energy': {
        'pattern': r'the Fermi energy is\s+([\d\.]+) ev',
        'flags': [],
        'postprocess': float,
    },
    'conv_iters': {
        'pattern': r'convergence has been achieved in\s+([\d+]) iterations',
        'flags': [],
        'postprocess': int,
    },
    'cell_parameters': {
        'pattern': r'CELL\_PARAMETERS\s+\(angstrom\)\s+([\s\d\.\-]+)^$',
        'flags': [re.MULTILINE],
        'postprocess': _cell_parameters_post,
    },
    'atomic_positions': {
        'pattern': r'ATOMIC_POSITIONS\s+\(crystal\)\s+([\w\s\d\.\-\n]+)^$',
        'flags': [re.MULTILINE],
        'postprocess': _atomic_positions_post,
    },
    'version': {
        'pattern': r'Program PWSCF v.([\d\.]+)',
        'flags': [],
        'postprocess': float,
    },
    'date': {
        'pattern': r'Program PWSCF v.[\d\.]+ starts on\s+([\S]+)',
        'flags': [],
        'postprocess': lambda x: str(x).strip(),
    },
    'time': {
        'pattern': r'Program PWSCF v.[\d\.]+ starts on\s+\S+\s+at\s+([\d\:\s]+)$',
        'flags': [re.MULTILINE],
        'postprocess': lambda x: str(x).strip(),
    },
    'lattice_type': {
        'pattern': r'bravais\-lattice index\s+=\s+(\d+)',
        'flags': [],
        'postprocess': int,
    },
    'lattice_parameter': {
        'pattern': r'lattice parameter \(alat\)\s+=\s+([\d\.]+)',
        'flags': [],
        'postprocess': float,
    },
    'unit_cell_volume': {
        'pattern': r'unit-cell volume\s+=\s+([\d\.]+)',
        'flags': [],
        'postprocess': float,
    },
    'nat': {
        'pattern': r'number of atoms\/cell\s+=\s+(\d+)',
        'flags': [],
        'postprocess': int,
    },
    'ntype': {
        'pattern': r'number of atomic types\s+=\s+(\d+)',
        'flags': [],
        'postprocess': int,
    },
    'nelectrons': {
        'pattern': r'number of electrons\s+=\s+([\d\.]+)',
        'flags': [],
        'postprocess': float,
    },
    'nks_states': {
        'pattern': r'number of Kohn\-Sham states=\s+(\d+)',
        'flags': [],
        'postprocess': int,
    },
    'ecutwfc': {
        'pattern': r'kinetic\-energy cutoff\s+=\s+([\d\.\-]+)\s+Ry',
        'flags': [],
        'postprocess': float,
    },
    'echutrho': {
        'pattern': r'charge density cutoff\s+=\s+([\d\.\-]+)\s+Ry',
        'flags': [],
        'postprocess': float,
    },
    'conv_thr': {
        'pattern': r'convergence threshold\s+=\s+([\d\.\-E]+)',
        'flags': [],
        'postprocess': float,
    },
    'mixing_beta': {
        'pattern': r'mixing beta\s+=\s+([\d\.]+)',
        'flags': [],
        'postprocess': float,
    },
    'niter': {
        'pattern': r'number of iterations used\s+=\s+([\d\w\s]+)$',
        'flags': [re.MULTILINE],
        'postprocess': lambda x: str(x).strip(),
    },
    'exc': {
        'pattern': r'Exchange\-correlation\s+=\s+([\d\w\s\(\)]+)$',
        'flags': [re.MULTILINE],
        'postprocess': lambda x: str(x).strip(),
    },
    'celldm1': {
        'pattern': r'celldm\(1\)=\s+([\d\.]+)\s',
        'flags': [],
        'postprocess': float,
    },
    'celldm2': {
        'pattern': r'celldm\(2\)=\s+([\d\.]+)\s',
        'flags': [],
        'postprocess': float,
    },
    'celldm3': {
        'pattern': r'celldm\(3\)=\s+([\d\.]+)\s',
        'flags': [],
        'postprocess': float,
    },
    'celldm4': {
        'pattern': r'celldm\(4\)=\s+([\d\.]+)\s',
        'flags': [],
        'postprocess': float,
    },
    'celldm5': {
        'pattern': r'celldm\(5\)=\s+([\d\.]+)\s',
        'flags': [],
        'postprocess': float,
    },
    'celldm6': {
        'pattern': r'celldm\(6\)=\s+([\d\.]+)\s',
        'flags': [],
        'postprocess': float,
    },
    'a1': {
        'pattern': r'a\(1\)\s+=\s+\(\s+([\d\s\.\-]+)\s+\)',
        'flags': [],
        'postprocess': lambda x: [float(i) for i in str(x).split()],
    },
    'a2': {
        'pattern': r'a\(2\)\s+=\s+\(\s+([\d\s\.\-]+)\s+\)',
        'flags': [],
        'postprocess': lambda x: [float(i) for i in str(x).split()],
    },
    'a3': {
        'pattern': r'a\(3\)\s+=\s+\(\s+([\d\s\.\-]+)\s+\)',
        'flags': [],
        'postprocess': lambda x: [float(i) for i in str(x).split()],
    },
    'b1': {
        'pattern': r'b\(1\)\s+=\s+\(\s+([\d\s\.\-]+)\s+\)',
        'flags': [],
        'postprocess': lambda x: [float(i) for i in str(x).split()],
    },
    'b2': {
        'pattern': r'b\(2\)\s+=\s+\(\s+([\d\s\.\-]+)\s+\)',
        'flags': [],
        'postprocess': lambda x: [float(i) for i in str(x).split()],
    },
    'b3': {
        'pattern': r'b\(3\)\s+=\s+\(\s+([\d\s\.\-]+)\s+\)',
        'flags': [],
        'postprocess': lambda x: [float(i) for i in str(x).split()],
    },
    'nsymop': {
        'pattern': r'^\s+([\d]+)\s+Sym\. Ops\.',
        'flags': [re.MULTILINE],
        'postprocess': int,
    },
    # TODO: symmetry operations (frac)
    # TODO: symmetry operations (cart)
    'initial_atomic_positions_cart': {
        'pattern': r'Cartesian axes[\s\n]+site n\.\s+atom\s+positions \(alat units\)\n(.*?)Crystallographic',
        'flags': [re.DOTALL],
        'postprocess': _initial_atomic_positions_post,
    },
    'initial_atomic_positions_frac': {
        'pattern': r'Crystallographic axes[\s\n]+site n\.\s+atom\s+positions \(cryst\. coord\.\)\n(.*?)number',
        'flags': [re.DOTALL],
        'postprocess': _initial_atomic_positions_post,
    },
    'nkpts': {
        'pattern': r'number of k points=\s+([\d]+)',
        'flags': [],
        'postprocess': int,
    },
    'smearing': {
        'pattern': r'number of k points=\s+[\d]+\s+([\S]+) smearing',
        'flags': [],
        'postprocess': lambda x:x,
    },
    'degauss': {
        'pattern': r'number of k points=\s+\d+\s+\S+ smearing, width\s+\(Ry\)=\s+([\d\.]+)',
        'flags': [],
        'postprocess': float,
    },
    'kpoints_cart': {
        'pattern': r'cart\. coord\. in units 2pi\/alat(.*?)cryst\. coord\.',
        'flags': [re.DOTALL],
        'postprocess': _kpoints_post,
    },
    'kpoints_frac': {
        'pattern': r'k\( .*?cryst\.\s+coord\.(.*?)Dense\s+grid',
        'flags': [re.DOTALL],
        'postprocess': _kpoints_post,
    },
    'vdw_correction': {
        'pattern': r'Carrying out vdW\-DF run using the following parameters: ([\w\s]+)$',
        'flags': [re.MULTILINE],
        'postprocess': str
    },
    'job_done': {
        'pattern': r'JOB DONE\.',
        'flags': [],
        'postprocess': str,
    },
    'not_electronically_converged': {
        'pattern': r'SCF convergence NOT achieved',
        'flags': [],
        'postprocess': str,
    },
    'cpu_time_exceeded': {
        'pattern': r'Maximum CPU time exceeded',
        'flags': [],
        'postprocess': str,
    },
    'max_steps_reached': {
        'pattern': r'The maximum number of ionic\/electronic relaxation steps has been reached',
        'flags': [],
        'postprocess': str, 
    },
    'wentzcovitch_max_reached': {
        'pattern': r'The maximum number of iterations was reached in Wentzcovitch Damped Dynamics',
        'flags': [],
        'postprocess': str,
    },
    'eigenvalues_not_converged': {
        'pattern': r'c_bands.*eigenvalues not converged',
        'flags': [],
        'postprocess': str, 
    },
    'general_error': {
        'pattern': r'\%{78}(.*?)\%{78}',
        'flags': [re.DOTALL | re.MULTILINE],
        'postprocess': lambda x: x.strip(),
    },
    'deprecated_feature_used': {
        'pattern': r'DEPRECATED',
        'flags': [],
        'postprocess': str,
    },
    'scf_correction_too_large': {
        'pattern': r'SCF correction compared to forces is too large, reduce conv\_thr',
        'flags': [],
        'postprocess': str,
    },

}