import tinydb
import pymatgen
import pandas as pd
import pathlib as pl
import json
import time
import qgrid
import sys
import os
import uuid
import getpass
import socket
import subprocess
import shlex
import re
import warnings
import hashlib

from IPython.display import clear_output, display
from pymatgen import Structure
from pypwio import PWInput, PWCalculation, PWOutput, PWXML

PSEUDO_PATH = '/data/tools/shared/dftman/pseudo'
PSEUDOMAP_PATH = str(pl.Path(PSEUDO_PATH) / 'pseudo_map.json')
PSEUDO_FAMILY_DIRS = {'sssp_efficiency': 'SSSP_EFFICIENCY',
                      'sssp_precision': 'SSSP_PRECISION',
                      'gbrv_us_lda': 'GBRV_LDA_US',
                      'gbrv_us_gga_pbesol': 'GBRV_PBSsol_US',
                      'gbrv_us_gga_pbe': 'GBRV_PBE_US',
                      'dojo_nc_lda_standard': 'DOJO_STANDARD_LDA_NC',
                      'dojo_nc_gga_pbe_standard': 'DOJO_STANDARD_GGA_PBE_NC',
                      'dojo_nc_gga_pbesol_standard': 'DOJO_STANDARD_GGA_PBEsol_NC',
                      'dojo_nc_lda_stringent': 'DOJO_STRINGENT_GGA_LDA_NC',
                      'dojo_nc_gga_pbe_stringent': 'DOJO_STRINGENT_GGA_PBE_NC',
                      'dojo_nc_gga_pbesol_stringent': 'DOJO_STRINGENT_GGA_PBEsol_NC'}
ESPRESSO_VERSION = 'espresso-6.2.1_pw'

A_PER_BOHR = 0.52917720859
A3_PER_BOHR3 = A_PER_BOHR ** 3
EV_PER_RY = 13.6056917253

class InsertError(Exception):
    def __init__(self, message):
        self.message = message
        return

    def __str__(self):
        return self.message

class SubmitError(Exception):
    def __init__(self, message):
        self.message = message
        return
    
    def __str__(self):
        return self.message

class PseudoError(Exception):
    def __init__(self, specie, message):
        self.specie = specie
        self.message = message
    
    def __str__(self):
        return '{} {}'.format(self.specie, self.message)

def walltime2seconds(walltime):
    '''
    Convert walltime string to seconds
    '''
    ftr = [3600,60,1]
    return sum([a*b for a,b in zip(ftr, map(int,walltime.split(':')))])

def calculation_from_doc_id(project, doc_id):
    '''
    Retrieve a calculation from the database by its 
        document id
    '''
    db = tinydb.TinyDB('dftman.json')
    table = db.table(project)
    doc = table.get(doc_id=doc_id)
    calculation = PWCalculationDFTman.from_dict(doc)
    return calculation

def nanoHUB_pseudo(structure, pseudo_family='sssp_efficiency'):
    '''
    Create a pseudo_dict for a given structure
        using either 'efficiency' or 'precision' SSSP
        potentials
    '''
    with open(PSEUDOMAP_PATH, 'r') as f:
        pseudo_maps = json.load(f)
    pseudo_map = pseudo_maps[pseudo_family]
    
    pseudo_dict = {}
    for specie in set(structure.species):
        try:
            pseudo_dict[specie.symbol] = pseudo_map[specie.symbol]['filename']
        except KeyError as key_error:
            raise PseudoError(specie.symbol, str(key_error))
    
    return pseudo_dict

def nanoHUB_status(project, watch=False, delay=5, upsert=True):
    clear_output()
    db = tinydb.TinyDB('dftman.json')
    table = db.table(project)
    query = tinydb.Query()
    
    while True:
        status = subprocess.check_output(['submit', '--status']).decode('utf-8').strip()
        clear_output()
        nruns = len(status) - 1 if len(status) else 0
        status_dicts = []
        untracked_runs = []
        if nruns:
            statuses = status.split('\n')[1:]
            for status in statuses:
                status = status.strip().split()
                status_dict = {
                    'runname': status[0],
                    'id': int(status[1]),
                    'instance': int(status[2]),
                    'status': status[3],
                    'location': status[4]
                }
                status_dicts.append(status_dict)
                pwcalculation = table.get(query.metadata.nanoHUB_id == status_dict['id'])
                if pwcalculation:
                    pwcalculation = PWCalculationDFTman.from_dict(pwcalculation)
                    pwcalculation.metadata['nanoHUB_status'] = status_dict['status']
                    pwcalculation.metadata['nanoHUB_location'] = status_dict['location']
                    if upsert:
                        pwcalculation.db_upsert()
                else:
                    warnings.warn('nanoHUB_runname {} nanoHUB_id {} has no database entry'.format(
                        status_dict['runname'], status_dict['id']))
                    untracked_runs.append(status_dict)
            
        all_documents = table.all()
        for d, document in enumerate(all_documents):
            mod = False
            if document['metadata']['nanoHUB_id']:
                nanoHUB_id = str(document['metadata']['nanoHUB_id'])
                # if *.stdout file exists, the simulation has completed
                if pl.Path(document['metadata']['output_path']).exists():
                    document['metadata']['nanoHUB_status'] = 'Complete'
                    subprocess.Popen(['submit', '--attach', nanoHUB_id])
                    mod = True
                # if *.stderr file exists, the simulation has completed with some flavor of error
                if pl.Path(document['metadata']['error_path']).exists():
                    document['metadata']['nanoHUB_status'] = 'Complete [ERROR]'
                    subprocess.Popen(['submit', '--attach', nanoHUB_id])
                    mod = True
                # if CRASH file exists, the simulation has completed after a crash (pw.x only)
                if (pl.Path(document['metadata']['UUID']) / 'CRASH').exists():
                    document['metadata']['nanoHUB_status'] = 'Complete [CRASH]'
                    subprocess.Popen(['submit', '--attach', nanoHUB_id])
                    mod = True
#             if not document['metadata']['DFTman_status']:
#                 document['metadata']['DFTman_status'].append('saved')
#                 mod = True
            if mod:
                all_documents[d] = document
                pwcalculation = PWCalculationDFTman.from_dict(document)
                pwcalculation.db_upsert()

        all_metadatas = []
        for document in all_documents:
            metadata = document['metadata']
            metadata['formula'] = metadata['mp_data']['pretty_formula']
            metadata['doc_id'] = document.doc_id
            # metadata['in_file'] = '<a href="{}" target="_blank">Input</a>'.format(metadata['input_path'])
            metadata['dir'] = '<a href="./{}/" target="_blank">directory</a>'.format(metadata['dir'])
            all_metadatas.append(metadata)
        if all_metadatas: 
            df = pd.DataFrame(all_metadatas)[
                    [# 'nanoHUB_runname', 
                     'doc_id', 'nanoHUB_id', 'formula',
                     'nanoHUB_status', # 'nanoHUB_location',
                     'DFTman_status', # 'submission_time', 
                     'dir']
                ].set_index('doc_id')
        else:
            df = pd.DataFrame([])

        display(qgrid.show_grid(df))
        
        if watch:
            time.sleep(delay)
        else:
            return

def pwmetadataDFTman(project, pwinput, pseudo_family='efficiency', espresso_version='espresso-6.2.1_pw',
                     walltime='01:00:00', ncpus=1, tag=None):
        '''
        Generate necessary / appropriate metadata for PWCalculationDFTman objects for use in DFTman
        :param project: string name of project
        :param pwinput: pypwio.PWInput or DFTman.PWInputDFTman object representing a pw.x input file
        :param pseudo_family: string name of pseudopotential family to use for pw.x calculation
        :param espresso_version: nanoHUB quantum espresso version string
        :param walltime: hh::mm::ss string representation of reqested maximum walltime
        :param ncpus: integer number of cpus used for calculatin
        :param tag: an optinal string tag for the calculation which will be prepended to the last four
            characters of the UUID and used for the nanoHUB runname
        '''
        pseudo_family_dir = PSEUDO_FAMILY_DIRS[pseudo_family]
        
        md5_string = '{}{}{}{}{}{}'.format(str(pwinput), pseudo_family, espresso_version, walltime, ncpus, tag)
        
        UUID = uuid.uuid4().hex
        UUID_end = UUID[-4:]
        
        if tag:
            nanoHUB_runname = tag + UUID_end
        else:
            nanoHUB_runname = UUID_end

        if pwinput.sections['control']['disk_io'] == 'none':
            xml_path = None
        else:
            xml_path = str(pl.Path(UUID) / (pwinput.sections['control']['prefix']+'.xml'))

        metadata = {
            'project': project,
            'tag': tag,
            'UUID': UUID,
            'md5': hashlib.md5(md5_string.encode('utf-8')).hexdigest(), 
            'user': getpass.getuser(),
            'hostname': socket.gethostname(),
            'DFTman_status': [],
            'creation_time': time.asctime(time.gmtime()),

            'walltime': walltime,
            'ncpus': ncpus,

            'dir': UUID,
            'pseudo_dir': str(pl.Path(PSEUDO_PATH) / pseudo_family_dir),
            'input_path': str(pl.Path(UUID) / '{}.in'.format(UUID)),
            'output_path': str(pl.Path(UUID) / (nanoHUB_runname+'.stdout')),
            'error_path': str(pl.Path(UUID) / (nanoHUB_runname+'.stderr')),
            'xml_path': xml_path,            
            'pseudo_family': pseudo_family,
            'output_flags': None,

            'espresso_version': espresso_version,
            'nanoHUB_id': None,
            'nanoHUB_runname': nanoHUB_runname,
            'nanoHUB_status': None,
            'nanoHUB_location': None,
            'submission_time': None,
        }
        return metadata

    
class MPQuery(object):
    def __init__(self, criteria, properties, API):
        REQUIRED_PROPERTIES = ['material_id', 'pretty_formula', 'elements', 'structure']
        self.properties = list(set(REQUIRED_PROPERTIES + properties))
        self.criteria = criteria
        self.API = API
        self.result = None
        self.df = None
        
    # TODO: Implement __repr__ with tabulate
#     def __repr__(self):
#         pass

    # TODO: Figure out how to get show_toolbar to work with editing self.df
    #    and self.result
    def display(self):
        display(qgrid.show_grid(self.df))

    def query(self):
        m = pymatgen.MPRester(self.API)
        result = m.query(criteria=self.criteria, properties=self.properties)
        self._set_result(result)
        return result
    
    def as_dict(self):
        mpquery_dict = {
            'properties': self.properties,
            'criteria': self.criteria,
            'API': self.API,
            'result': self.result
        }
        return mpquery_dict
    
    def _set_result(self, result):
        self.result = result
        if result:
            self.df = pd.DataFrame(result).set_index('material_id')
        else:
            self.df = pd.DataFrame(result)
        return
    
    @classmethod
    def from_dict(cls, mpquery_dict):
        mpquery = cls(criteria=mpquery_dict['criteria'],
                       properties=mpquery_dict['properties'],
                       API=mpquery_dict['api'])
        mpquery._set_result(mpquery_dict['result'])
        return mpquery


class PWInputDFTman(PWInput):
    '''
    Subclass of pypwio's PWInput (a subclass of pymatgen's PWInput)
        which adds some parameter checks for use with DFTman
    See the pymatgen or pwpyio documentation for a parameter description
    '''
    def __init__(self, structure, pseudo=None, control={}, system={},
                 electrons={}, ions={}, cell={}, kpoints_mode="automatic",
                 kpoints_grid=(1, 1, 1), kpoints_shift=(0, 0, 0)):
        # ensure prefix has a value (used for xml_path)
        if 'prefix' not in control:
            control['prefix']  = 'pwscf'
        # ensure that disk_io has a value (used for xml_path)
        if 'disk_io' not in control:
            if control['calculation'] == 'scf':
                control['disk_io'] = 'low'
            else:
                control['disk_io'] = 'medium'
        # ensure these fields do not exist (will be set by database)
        for key in ['title', 'outdir', 'max_seconds', 'pseudo_dir']:
            if key in control.keys():
                del control[key]
        # ensure these fields do not exist (will be set by pymatgen.io.pwscf.PWInput)
        for key in ['nat', 'ntyp']:
            if key in system.keys():
                del system[key]
        # check for pseudos in sites if not explicitly given
        if not pseudo:
            for site in structure:
                if 'pseudo' not in site.properties:
                    raise PseudoError(site.specie.symbol, 'has no pseudopotential specified')
        else:
            for specie in set(structure.species):
                if specie.symbol not in pseudo:
                    raise PseudoError(specie.symbol, 'has no pseudopotential specified')
        
        self.pseudo = pseudo      
        self.structure = structure
        self.sections = {'control': control,
                         'system': system,
                         'electrons': electrons,
                         'ions': ions,
                         'cell': cell}
        
        self.pseudo = pseudo
        self.kpoints_mode = kpoints_mode
        self.kpoints_grid = kpoints_grid
        self.kpoints_shift = kpoints_shift
                
        super(PWInputDFTman, self).__init__(self.structure, self.pseudo, self.sections['control'], self.sections['system'],
                                            self.sections['electrons'], self.sections['ions'], self.sections['cell'],
                                            self.kpoints_mode, self.kpoints_grid, self.kpoints_shift)
        return


class PWCalculationDFTman(PWCalculation):
    def __init__(self, pwinput, metadata, pwoutput=None, pwxml=None):
        self.pwinput = pwinput
        self.pwoutput = pwoutput
        self.pwxml = pwxml
        self.metadata = metadata

        super(PWCalculationDFTman, self).__init__(self.pwinput, self.metadata, self.pwoutput, self.pwxml)
        return

    def submit(self, upsert=True, db='dftman.json', ignore_not_saved=False, ignore_submitted=False,
               warn_not_saved=True, warn_submitted=True):
        project = self.metadata['project']
        
        # check if the calculation has been saved
        if 'saved' not in self.metadata['DFTman_status'] and not ignore_not_saved:
            if warn_not_saved:
                warnings.warn('This simulation has not been saved in the database. Set ignore_not_saved to submit anyway')
                return None
            else:
                raise SubmitError('This simulation has not been saved in the database. Set ignore_not_saved to submit anyway or warn_not_saved to recieve a warning instead of an error')

        # check if the calculation has been submitted
        if 'submitted' in self.metadata['DFTman_status'] and not ignore_submitted:
            if warn_not_saved:
                warnings.warn('This simulation has already been submitted. Set ignore_submitted to submit anyway')
                return None
            else:
                raise SubmitError('This simulation has already been submitted. Set ignore_submitted to submit anyway or warn_submitted to recieve a warning instead of an error.')
        
        db = tinydb.TinyDB('dftman.json')
        table = db.table(project)
        query = tinydb.Query()
        
        # ensure correct outdir and pseudodir
        self.pwinput.sections['control']['outdir'] = './'
        self.pwinput.sections['control']['pseudo_dir'] = './'

        # add max_seconds to pwinput
        walltime = self.metadata['walltime']
        self.pwinput.sections['control']['max_seconds'] = walltime2seconds(walltime)

        # write input file
        os.makedirs(self.metadata['dir'])
        self.write_input()

        # get input filename
        input_file = pl.Path(self.metadata['input_path']).name

        # create pseduo inputs string
        pseudos = ''
        for pseudo in list(self.pwinput.pseudo.values()):
            path = pl.Path(PSEUDO_PATH) / PSEUDO_FAMILY_DIRS[self.metadata['pseudo_family']] / pseudo
            pseudos += ' -i {}'.format(path)

        command = 'submit --detach -n {:d} -w {:s} --runName="{:s}"{:s} {} -in {:s}'.format(
            self.metadata['ncpus'],
            walltime,
            self.metadata['nanoHUB_runname'],
            pseudos,
            self.metadata['espresso_version'],
            input_file)

        process = subprocess.Popen(shlex.split(command),
                                   cwd=self.metadata['dir'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout = process.stdout.read().decode('utf-8')
        stderr = process.stderr.read().decode('utf-8')

        nanoHUB_id_re = re.compile(r'Check run status with the command: submit --status (\d+)')
        nanoHUB_id_match = re.search(nanoHUB_id_re, stdout)
        try:
            nanoHUB_id = int(nanoHUB_id_match.group(1))
            self.metadata['nanoHUB_id'] = nanoHUB_id
            self.metadata['nanHUB_status'] = 'Registered'
            self.metadata['DFTman_status'].append('submitted')
            self.metadata['submission_time'] = time.asctime(time.gmtime())
            if upsert:
                self.db_upsert(db=db)
            return None
        except:
            raise SubmitError(stderr)
            # return stderr

    def check_status(self, upsert=True, db='dftman.json'):
        raise NotImplementedError('Please use the nanoHUB_status function for now')
        # return

    def db_exists(self, db='dftman.json'):
        project = self.metadata['project']

        db = tinydb.TinyDB('dftman.json')
        table = db.table(project)
        query = tinydb.Query()
       
        result = table.get(query.metadata.md5 == self.metadata['md5'])
        return bool(result)
    
    def db_insert(self, db='dftman.json', ignore_duplicate=False, warn_duplicate=True):
        project = self.metadata['project']

        db = tinydb.TinyDB('dftman.json')
        table = db.table(project)
        query = tinydb.Query()
       

        result = self.db_exists()
        if result and not ignore_duplicate:
            if not warn_duplicate:
                raise InsertError(
'''An identical simulation is in the database, use ignore_duplicate to insert anyway.
Use warn_duplicate to recieve a warning instead of an error.''')
            else:
                warnings.warn(
'''An identical simulation is in the database, use ignore_duplicate to insert anyway.''')
                return None
        else:
            pwcalculation_dict = self.as_dict()
            pwcalculation_dict['metadata']['DFTman_status'].append('saved')
            result = table.insert(pwcalculation_dict)
            return result

    def db_upsert(self, db='dftman.json'):
        project = self.metadata['project']

        db = tinydb.TinyDB('dftman.json')
        table = db.table(project)
        query = tinydb.Query()

        result = table.upsert(self.as_dict(), query.metadata.UUID == self.metadata['UUID'])
        return result

    @classmethod
    def from_dict(cls, pwdict):
        pwinput = PWInputDFTman.from_dict(pwdict['input'])
        if pwdict['output']:
            pwoutput = PWOutput.from_dict(pwdict['output'])
        else:
            pwoutput = pwdict['output']
        if pwdict['xml']:
            pwxml = PWXML.from_dict(pwdict['xml'])
        else:
            pwxml = pwdict['xml']

        metadata = pwdict['metadata']
        pwcalculation = cls(pwinput, metadata, pwoutput, pwxml)
        return pwcalculation
