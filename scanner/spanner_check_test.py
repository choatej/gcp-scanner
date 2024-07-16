import os
import unittest
from spanner import get_projects, get_instances, get_tables, get_databases


class SpannerCheckTestCase(unittest.TestCase):
    """
    SpannerCheckTestCase is a functional test of the logic to find Spanner databases.
    The inputs to the test should be a GCP project that contains at least one Spanner
    instance and the instance should have at least one database with at least on table.
    Of course, it also assumes that the test runner has appropriate access to the GCP
    project.
    The tests require three env vars to be exported to run properly:
        - TEST_PROJECT_ID - the GCP project ID to check for Spanner instances
        - TEST_INSTANCE_ID - the Spanner instance name to check for databases
        - TEST_DATABASE_ID - the Spanner database name to test for tables
    """
    def __init__(self, method_name='runTest'):
        super().__init__(method_name)
        self.project = os.getenv('TEST_PROJECT_ID', '')
        self.instance = os.getenv('TEST_INSTANCE_ID', '')
        self.database_id = os.getenv('TEST_DATABASE_ID', '')
        missing_data = self.collect_missing_data()
        if missing_data != '':
            raise ValueError(f'missing required env var(s): {missing_data}')

    def collect_missing_data(self):
        missing_fields = []
        if self.project == '':
            missing_fields.append('TEST_PROJECT_ID')
        if self.instance == '':
            missing_fields.append('TEST_INSTANCE_ID')
        if self.database_id == '':
            missing_fields.append('TEST_DATABASE_ID')
        return ','.join(missing_fields)

    def test_get_instances(self):
        project_id = self.project
        instances_pager = get_instances(project_id)
        self.assertIsNotNone(list(instances_pager),'no instances found')
        # make sure we have something that can get passed along
        for instance in instances_pager:
            print(instance.name)

    def test_get_databases(self):
        instance_name = self.instance
        db_pager = get_databases(instance_name)
        self.assertIsNotNone(list(db_pager),'no databases found')
        # make sure we have something that can get passed along
        for db in db_pager:
            print(db.name)

    def test_get_tables(self):
        database_name = self.database_id
        table_pager = get_tables(database_name)
        self.assertIsNotNone(list(table_pager), 'no tables found')
        # make sure we have something that can get passed along
        for table in table_pager:
            print(table)


if __name__ == '__main__':
    unittest.main()
