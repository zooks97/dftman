from ..db import load_db

import subprocess
import os
import getpass
import pandas as pd

def pbsjob_statuses(jobs, update_in_db=False):
    '''
    Check the statuses of a set of PBSJobs
    :param jobs: Jobs to check status of
    :type jobs: PBSJob
    :returns: status data frame
    :rtype: pandas.DataFrame
    '''
    status_dicts = []
    for job in jobs:
        status_dicts.append(job.check_status())
    df = pd.DataFrame(status_dicts)
    if not df.empty:
        df = df.set_index('PBS ID')
        df = df[['Run Name', 'Status', 'Elapsed Time', 'Walltime', 'Queue', 'Doc ID']]
    if update_in_db:
        db = load_db()
        table = db.table('PBSJob')
        table.write_back(jobs, doc_ids=[job.doc_id for job in jobs])
    return df


def pbs_status():
    '''
    Check the statuses of all PBS jobs in the user's queue
    :returns: status data frame
    :rtype: pandas.DataFrame
    '''
    status_codes = {'C': 'Complete',
                'E': 'Exiting',
                'H': 'Held',
                'Q': 'Queued',
                'R': 'Running',
                'T': 'Moving',
                'W': 'Waiting'
             }
    
    process = subprocess.Popen(['qstat', '-u', getpass.getuser()],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    status_text = process.stdout.read().decode('utf-8').strip()
    status_lines = status_text.split('\n')
    
    if len(status_lines) > 4:
        status_dicts = []
        for line in status_lines[4:]:
            pbs_id, username, queue, runname, session_id,\
            nnodes, np, reqd_memory, walltime, status, elapsed_time = line.split()
            status = {
               'pbs_id': pbs_id.split('.')[0],
               'username': username,
               'queue': queue,
               'runname': runname,
               'session_id': session_id,
               'nnodes': nnodes,
               'np': np,
               'reqd_memory': reqd_memory,
               'walltime': walltime,
               'status': status_codes[status],
               'elapsed_time': elapsed_time
            }
            status_dicts.append(status)
        status_df = pd.DataFrame(status_dicts).set_index('pbs_id')
        status_df = status_df[['runname', 'status', 'elapsed_time', 'walltime', 'queue']]
    else:
        status_df = pd.DataFrame([])
    return status_df
        
    
def submitjob_statuses(jobs, update_in_db=False):
    '''
    Check the statuses of a set of SubmitJobs
    :param jobs: Jobs to check status of
    :type jobs: SubmitJob
    :param update_to_db: Whether to update job in database
    :type update_to_db: bool
    :returns: status data frame
    :rtype: pandas.DataFrame
    '''
    status_dicts = []
    for job in jobs:
        status_dicts.append(job.check_status())
    df = pd.DataFrame(status_dicts)
    if not df.empty:
        df = df.set_index('Submit ID')
        df = df[['Status', 'Instance', 'Location', 'Doc ID']]
    if update_in_db:
        db = load_db()
        table = db.table('SubmitJob')
        table.write_back(jobs, doc_ids=[job.doc_id for job in jobs])
    return df
    
    
def submit_status():
    '''
    Check the statuses of all Submit jobs in the user's queue
    :returns: status data frame
    :rtype: pandas.DataFrame
    '''
    process = subprocess.Popen(['submit', '--status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    stdout = process.stdout.peek().decode('utf-8')
    stderr = process.stderr.peek().decode('utf-8')

    if subprocess.returncode == 0:
        status_text = stdout.strip()
    else:
        raise subprocess.CalledProcessError
    
    nruns = len(status_text) - 1 if len(status_text) else 0
    if nruns:
        status_dicts = []
        statuses = status_text.strip().split('\n')[1:]
        for status in statuses:
            status = status.strip().split()
            status_dict = {
                'Submit ID': int(status[1]),
                'Instance': int(status[2]),
                'Status': status[3],
                'Location': status[4]
            }
            status_dicts.append(status_dict)
        status_df = pd.DataFrame(status_dicts).set_index('Submit ID')
        status_df = status_df[['Status', 'Instance', 'Location']]
    else:
        status_df = pd.DataFrame([])
    return status_df