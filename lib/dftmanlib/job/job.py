import subprocess
import pandas as pd

JOBS_DIRECTORY = './jobs'

def submitjob_statuses(jobs):
    status_dicts = []
    for job in jobs:
        status_dicts.append(job.check_status())
    df = pd.DataFrame(status_dicts)
    if not df.empty:
        df = df.set_index('Run Name')
        df = df[['ID', 'Location', 'Submission Time', 'Key']]
    return df
    
def submit_status():
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