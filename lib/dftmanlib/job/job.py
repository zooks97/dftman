import subprocess
import os
import getpass
import pandas as pd

def pbsjob_statuses(jobs):
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
        
    
def submitjob_statuses(jobs):
    '''
    Check the statuses of a set of SubmitJobs
    :param jobs: Jobs to check status of
    :type jobs: SubmitJob
    :returns: status data frame
    :rtype: pandas.DataFrame
    '''
    status_dicts = []
    for job in jobs:
        status_dicts.append(job.check_status())
    df = pd.DataFrame(status_dicts)
    if not df.empty:
        df = df.set_index('Run Name')
        df = df[['Status', 'ID', 'Location', 'Submission Time', 'Hash', 'Doc ID']]
    return df
    
    
def submit_status():
    '''
    Check the statuses of all Submit jobs in the user's queue
    :returns: status data frame
    :rtype: pandas.DataFrame
    '''
    status_text = subprocess.check_output(['submit', '--status']).decode('utf-8').strip()
    
    nruns = len(status_text) - 1 if len(status_text) else 0
    if nruns:
        status_dicts = []
        statuses = status_text.strip().split('\n')[1:]
        for status in statuses:
            status = status.strip().split()
            status_dict = {
                'Run Name': status[0],
                'ID': int(status[1]),
                'Instance': int(status[2]),
                'Status': status[3],
                'Location': status[4]
            }
            status_dicts.append(status_dict)
        status_df = pd.DataFrame(status_dicts).set_index('ID')
        status_df = status_df[['Run Name', 'Status', 'Instance', 'Location']]
    else:
        status_df = pd.DataFrame([])
    return status_df