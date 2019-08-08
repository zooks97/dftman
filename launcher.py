import shutil
import time
import json
import os

import pathlib

import qgrid

import pandas as pd

from ipywidgets import Button, Text, Dropdown, HBox, VBox
from IPython.display import clear_output, display
# from tinydb import *


# TODO: get everything from git
# TODO: implement project reset (i.e. delete / trash all databases + files except for notebook(s))
# TODO: implement tool dropdown to choose which notebook to initialize a new project with
# TODO: transition to a tabbed interface with different functions in different tabs (create, delete, duplicate)
#           this shold allow for cleaner code and more options


qgrid.enable()


INSTALL_PATH = str(pathlib.Path.cwd())  # determine where dftman is installed

GLOBAL_LIB_PATH = '/apps/dftman/dev/lib'
LOCAL_LIB_PATH = './lib'

GLOBAL_BIN_PATH = './bin'

LOCAL_SRC_PATH = 'src'

PROJECTS_TABLE_PATH = 'projects.json'

PROJECTS_PATH = 'projects'

DEFAULT_TOOL = 'default.ipynb'
DEFAULT_TOOLS = [None, 'default.ipynb']


add_button = Button(
    description='Add Project',
    icon='plus',
    tooltip='Add a New Project',
    button_style='success',
    disabled=True
)

delete_button = Button(
    description='Delete Project',
    icon='minus',
    tooltip='Delete Project and its Files',
    button_style='danger',
    disabled=True
)
duplicate_button = Button(
    description='Duplicate Project',
    icon='plus',
    tooltip='Duplicate Project and its Files',
    button_style='info',
    disabled=True
)
tool_dropdown = Dropdown(
    options=DEFAULT_TOOLS,
    value=None,
    description='Tool',
    disabled=False,
)
style = {'description_width': 'initial'}
name_field = Text(description='Project Name', style=style)
duplicate_field = Text(description='Duplicate Name', style=style)


def load_projects(table_path=PROJECTS_TABLE_PATH, as_df=False) -> pd.DataFrame:
    '''
    Read the projects table into (probably) a
        list of dictionaries
    '''
    if os.path.exists(table_path):
        with open(table_path, 'r') as f:
            projects = json.load(f)
    else:
        projects = []
    if as_df:
        projects = pd.DataFrame(projects)
    return projects


def write_projects(projects, table_path=PROJECTS_TABLE_PATH):
    '''
    Dump what should be a list of dictionaries into the
        projects table
    '''
    if isinstance(projects, pd.DataFrame):
        projects = projects.to_dict('records')
    with open(table_path, 'w') as f:
        json.dump(projects, f)


def install_libs():
    '''
    Install all available versions of dftman librar(y/ies)
    Currently copies library files from global LIB_PATH to
        the local 'lib' directory
    '''
    # install / update library files
    if pathlib.Path(LOCAL_SRC_PATH).exists():  # src is only in dev, lib already present
        print('Not installing libs, already in dev!')
        return

    locallib = pathlib.Path(LOCAL_LIB_PATH)
    globallib = pathlib.Path(GLOBAL_LIB_PATH)

    # create local lib directory if necessary
    if not locallib.exists():
        locallib.mkdir()

    # scan globallib and add any missing softlinks
    for f in globallib.iterdir():
        dst = locallib / f.name
        if not dst in locallib.iterdir():
            dst.symlink_to(f)


def add_project(_):
    '''
    Add a new project by adding a project entry to the database,
        creating the project directory, and copying the DEFAULT_TOOL
        to the project directory
    :param name_field: Jupyter widget for name insertion
    '''
    name = name_field.value

    project_path = pathlib.Path(PROJECTS_PATH) / '{}'.format(name)
    tool_source = pathlib.Path(GLOBAL_BIN_PATH) / DEFAULT_TOOL
    tool_dest = project_path / '{}.ipynb'.format(name)

    path_link = '<a href="{}" target="_blank">{}</a>'.format(
        project_path, project_path)
    tool_link = '<a href="{}" target="_blank">Notebook</a>'.format(tool_dest)

    project_dict = {
        'Name': str(name),
        'Path': str(path_link),
        'Link': str(tool_link),
        'Creation Time': time.asctime(time.gmtime()),  # UTC creation time
        '_path': str(project_path),
        '_tool': str(tool_dest)
    }

    # load projects table
    projects_list = load_projects(as_df=False)
    if projects_list:
        # add project
        projects_list.append(project_dict)
    else:
        projects_list = [project_dict]
    # write new projects table
    write_projects(projects_list)

    # make directories
    project_path.mkdir(parents=True)
    # copy files
    shutil.copy(str(tool_source), str(tool_dest))

    # show projects
    show_projects()


def delete_project(_):
    '''
    Delete a project by adding finding and deleting the project from
        the database and removing the project directory tree
    :param name_field: Jupyter widget for name insertion
    '''
    name = name_field.value

    # load projects, find project, and remove project
    #     from the projects table
    projects_list = load_projects(as_df=False)
    for i, project in enumerate(projects_list):
        if project['Name'] == name:
            deleted_project = projects_list.pop(i)
            # remove project directory
            try:
                shutil.rmtree(deleted_project['_path'])
            except:
                pass
    write_projects(projects_list)

    show_projects()

# TODO: implement project duplication


def duplicate_project(_):
    og_name = name_field.value
    dup_name = duplicate_field.value

    dup_path = pathlib.Path(PROJECTS_PATH) / '{}'.format(dup_name)
    dup_tool = dup_path / '{}.ipynb'.format(dup_name)

    projects_list = load_projects(as_df=False)
    for project in projects_list:
        if project['Name'] == og_name:
            og_project = project
            og_path = pathlib.Path(og_project['_path'])
            og_tool = pathlib.Path(og_project['_tool'])
            # TODO: rename all appropriate files from og_tool with the dup_name
            shutil.copytree(og_path, dup_path)
            shutil.move(dup_path / og_tool.name, dup_tool)

    path_link = '<a href="{}" target="_blank">{}</a>'.format(
        dup_path, dup_path)
    tool_link = '<a href="{}" target="_blank">Notebook</a>'.format(dup_tool)

    project_dict = {
        'Name': str(dup_name),
        'Path': str(path_link),
        'Link': str(tool_link),
        'Creation Time': time.asctime(time.gmtime()),  # UTC creation time
        '_path': str(dup_path),
        '_tool': str(dup_tool)
    }

    # load projects table
    projects_list = load_projects(as_df=False)
    # add project
    projects_list.append(project_dict)
    # write new projects table
    write_projects(projects_list)

    # show projects
    show_projects()


def project_name(change):
    '''
    Callback when the name_field changes
    When the name changes, should check if the project
        exists and enable / disable Add / Delete buttons
        as necessary
    :param change: ipywidget state change dictionary
    '''
    name = change['new']

    projects_df = load_projects(as_df=True)

    if not projects_df.empty:
        if name and name in projects_df['Name'].tolist():
            add_button.disabled = True
            delete_button.disabled = False
            duplicate_field.value = '{}_copy'.format(name)
            if duplicate_field.value in projects_df['Name'].tolist():
                duplicate_button.disabled = True
            else:
                duplicate_button.disabled = False
        elif name:
            add_button.disabled = False
            delete_button.disabled = True
            duplicate_field.value = ''
            duplicate_button.disabled = True
        else:
            add_button.disabled = True
            delete_button.disabled = True
            duplicate_button.value = ''
            duplicate_button.disabled = True
    else:
        if name:
            add_button.disabled = False
        else:
            add_button.disabled = True
            delete_button.disabled = True
            duplicate_button.disabled = True


def duplicate_name(change):
    '''
    Callback when the name_field changes
    :param change: ipywidget state change dictionary
    '''
    name = change['new']

    projects_df = load_projects(as_df=True)

    if not projects_df.empty:
        if name in projects_df['Name'].tolist():
            duplicate_button.disabled = True
        elif name:
            duplicate_button.disabled = False
        else:
            duplicate_button.disabled = True


def select_cb(event, w):
    '''
    Callback when a different row of the qgrid is selected
    This will change the name in field_name to the appropriate
        name in the table, and project_name will handle the rest
    :param event: qgrid state change event dictionary
    :w: qgrid status information dictionary
    '''
    ind = event['new'][0]

    projects_df = load_projects(as_df=True)

    # find name
    name = projects_df.iloc[ind].Name
    name_field.value = name


def show_projects():
    '''
    Show the projects and their metadata as listed in the
        database using a qgrid grid widget
    '''
    show_columns = ['Name', 'Link', 'Path', 'Creation Time']
    clear_output()

    projects_df = load_projects(as_df=True)
    if not projects_df.empty:
        projects_df = projects_df[show_columns]

    if projects_df.empty:
        print('No projects exist. Make a project first.')
        display(qgrid.show_grid(projects_df,
                                grid_options={'editable': False}))
    else:
        qgrid.on('selection_changed', select_cb)
        display(qgrid.show_grid(projects_df.set_index('Name'),
                                grid_options={'editable': False}))

    add_button.on_click(callback=add_project)
    delete_button.on_click(callback=delete_project)
    duplicate_button.on_click(callback=duplicate_project)

    name_field.value = ''
    name_field.observe(project_name, names='value')

    duplicate_field.value = ''
    duplicate_field.observe(duplicate_name, names='value')

    display(
        VBox(
            [HBox([name_field, add_button, delete_button]),
             HBox([duplicate_field, duplicate_button])]
        )
    )

    return


if __name__ == '__main__':
    install_libs()
    show_projects()
