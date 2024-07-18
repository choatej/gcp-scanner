from scanner.spanner import filter_projects


class TestSpannerLogic:
    def test_filter_projects(self):
        good_projects = [
            {'projectId': 'project-1'},
            {'projectId': 'project-2'},
            {'projectId': 'project-4'},
            {'projectId': 'project-5'},
            {'projectId': 'project-6'}
        ]
        sandbox_projects = [
            {'projectId': 'sandbox-project-1'},
            {'projectId': 'sandbox-project-2'},
        ]

        system_projects = [
            {'projectId': 'sys-project-1'},
            {'projectId': 'sys-project-2'},
        ]

        projects_in = [
            good_projects[0],
            sandbox_projects[0],
            good_projects[1],
            system_projects[0],
            good_projects[2],
            sandbox_projects[1],
            good_projects[3],
            system_projects[1],
            good_projects[4],
        ]

        projects_out = filter_projects(projects_in)

        assert all(project not in projects_out for project in sandbox_projects)
        assert all(project not in projects_out for project in system_projects)
        assert all(project in projects_out for project in good_projects)
