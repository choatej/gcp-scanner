import json

from googleapiclient.errors import HttpError
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from spanner import get_projects

credentials = GoogleCredentials.get_application_default()
service = discovery.build('sqladmin', 'v1beta4',
                          credentials=credentials)


def list_instances(project_id):
    """
    Retrieve Cloud SQL instances
    """
    instance_array = []
    try:
        request = service.instances().list(project=project_id)
        while request is not None:
            response = request.execute()
            if 'items' not in response:
                return instance_array
            for database_instance in response['items']:
                instance_array.append(database_instance['name'])
            request = service.instances().list_next(previous_request=request,
                                                    previous_response=response)
    except HttpError:
        print(f'failed to find instances on {project_id}')
    return instance_array


def list_databases(project_id, instance_name):
    database_array = []
    request = service.databases().list(project=project_id, instance=instance_name)
    while request is not None:
        try:
            response = request.execute()
            if 'items' not in response:
                return database_array
            for database in response['items']:
                database_array.append(database['name'])
            request = service.instances().list_next(previous_request=request,
                                                    previous_response=response)
        except HttpError as e:
            if 'is not running' in str(e):
                return database_array
    return database_array


def list_all_databases(project_id):
    project_instances = list_instances(project_id)
    collector = {}
    for instance in project_instances:
        databases = list_databases(project_id, instance)
        short_name = instance.split('/')[-1]
        collector[short_name] = databases
    return collector


def main():
    all_projects = {}
    projects = get_projects()
    for project in projects:
        project_id = project['projectId']
        all_projects[project_id] = list_all_databases(project_id)
    with open('cloudsql-instances.json', 'w') as f:
        json.dump(all_projects, f)


if __name__ == '__main__':
    main()
