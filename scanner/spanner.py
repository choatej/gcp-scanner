import json
from argparse import ArgumentParser
import logging
from pathlib import Path
import sys
import subprocess

import google.auth
from google.cloud import spanner
from google.cloud.spanner_admin_database_v1 import DatabaseAdminClient
from google.cloud.spanner_admin_instance_v1 import InstanceAdminClient
from googleapiclient import discovery


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--in_file', '-i',
                        help='File to read the data from. If not specified, data will '
                        'be pulled from GCP, this switch implies --visualize')
    parser.add_argument('--out_file', '-o',
                        help='JSON File to save the results to. If not specified, the '
                        'data will not be saved')
    parser.add_argument('--projects', '-p',
                        help='Projects to look at. Defaults to all')
    parser.add_argument('--visualize', '-v',
                        help='Show a tree of all of the spanner details',
                        action='store_true')
    arg_vals = parser.parse_args()
    return arg_vals


def get_projects():
    """Get a list of all projects."""
    credentials, _ = google.auth.default()
    service = discovery.build('cloudresourcemanager', 'v1',
                              credentials=credentials)
    logger.info('Getting projects...')
    request = service.projects().list()
    projects = []
    while request is not None:
        response = request.execute()
        if 'projects' in response:
            projects.extend(response['projects'])
        request = service.projects().list_next(previous_request=request,
                                               previous_response=response)
    # filter out projects with sandbox in the id
    projects = [project for project in projects if not
                ('sandbox' in project['projectId'] or
                 project['projectId'].startswith('sys-'))]
    return projects


def describe_project(project_id):
    logger.info(f'Describing project {project_id}')
    project_description = {'instances': {}}
    project_instances = project_description['instances']
    instances = get_instances(project_id)
    for instance in instances:
        instance_desc = describe_instance(instance)
        if instance_desc != {}:
            name = instance.name.split('/')[-1]
            project_instances[name] = instance_desc
    return project_description


def get_instances(project_id):
    """List all Spanner instances in a project."""
    client = InstanceAdminClient()
    parent = f"projects/{project_id}"
    instances = client.list_instances(request={"parent": parent})
    return instances


def describe_instance(instance):
    instance_id = instance.name
    logger.info(f'Describing instance {instance_id.split("/")[-1]}')
    instance_description = {'databases': {}}
    instance_databases = instance_description['databases']
    databases = get_databases(instance_id)
    for database in databases:
        db_description = describe_database(database.name)
        if db_description != {}:
            name = database.name.split('/')[-1]
            instance_databases[name] = db_description
    return instance_description


def get_databases(instance_id):
    client = DatabaseAdminClient()
    databases = client.list_databases(request={"parent": instance_id})
    # I don't have access to the prod pii database for good reason
    databases = [database for database in databases if not
                 ('prod' in database.name and 'pii' in database.name)]
    return databases


def describe_database(database_id):
    logger.info(f'Describing database {database_id.split("/")[-1]}')
    database_description = {'tables': {}}
    database_tables = database_description['tables']
    tables = get_tables(database_id)
    for table in tables:
        database_tables[table] = describe_table(database_id, table)
    return database_description


def get_tables(database_id):
    project, instance_id, database_name = extract_principles(database_id)
    client = spanner.Client(project=project)
    instance = client.instance(instance_id)
    database = instance.database(database_name)
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql("""
            SELECT t.table_name 
            FROM information_schema.tables t 
            WHERE t.table_catalog = '' 
            AND t.table_schema = ''
            AND t.table_name not in ('DATABASECHANGELOG', 'DATABASECHANGELOGLOCK')
""")
        tables = [row[0] for row in results]
    return tables


def describe_table(database_id, table):
    """Get the schema for a table."""
    project_id, instance_id, database_name = extract_principles(database_id)
    logger.info(f'Describing table {database_name}/{table}')
    client = spanner.Client(project=project_id)
    instance = client.instance(instance_id)
    database = instance.database(database_name)
    schema = {}
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(f"""
            SELECT column_name, spanner_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            ORDER BY ordinal_position
        """)
        for row in results:
            column_name, spanner_type, is_nullable = row
            schema[column_name] = {
                "spanner_type": spanner_type,
                "is_nullable": is_nullable
            }
    return {
        'schema': schema
    }


def extract_principles(database_id):
    parts = database_id.split('/')
    # the even number spots are the words projects, instances, and databases
    project_id = parts[1]
    instance_id = parts[3]
    database_name = parts[5]
    return project_id, instance_id, database_name


def visualize(data):
    json_file = 'spanner-tools/public/results.json'
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)
    subprocess.Popen(['npm start'], cwd='./spanner-tools',
                                         shell=True)
    print('Press any key to exit')
    sys.stdin.readline()
    json_file_path = Path(json_file)
    if json_file_path.exists():
        json_file_path.unlink()
    logger.info("Run `kill -9 $(ps -ef | grep start.js | grep -v grep | awk '{ print "
                "$2 }')` to stop node")


def pull_data(program_args):
    all_spanners = {}
    if program_args.projects is not None:
        google_projects = args.projects.split(',')
    else:
        google_projects = [project['project_id'] for project in get_projects()]
    for google_project in google_projects:
        project_desc = describe_project(google_project)
        if project_desc != {}:
            all_spanners[google_project] = project_desc
    return all_spanners


def remove_empty_elements(d):
    """
    Recursively remove empty dictionaries.
    """
    if not isinstance(d, dict):
        return d

    keys_to_remove = [key for key, value in d.items() if isinstance(value, dict) and not value]
    for key in keys_to_remove:
        del d[key]

    for key, value in list(d.items()):
        if isinstance(value, dict):
            d[key] = remove_empty_elements(value)
            if not d[key]:
                del d[key]

    return d


def main(program_args):
    print('Starting')
    if program_args.in_file is not None:
        logger.info('Reading data from %s', program_args.in_file)
        all_spanners = json.load(open(program_args.in_file))
    else:
        all_spanners = pull_data(program_args)
    all_spanners = remove_empty_elements(all_spanners)
    if program_args.out_file is not None:
        with open(args.out_file, 'w') as f:
            json.dump(all_spanners, f)
        print(f'Saved details to {args.out_file}')
    if program_args.in_file is not None or program_args.visualize:
        logger.info('Visualizing data in browser window')
        visualize(all_spanners)
    print('Done')


if __name__ == '__main__':
    args = parse_args()
    main(args)
