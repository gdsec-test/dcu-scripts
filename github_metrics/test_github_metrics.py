import github_metrics
import unittest

from datetime import datetime
from mock import patch


EDGES = [{
    "node": {
        "closedAt": "2022-06-02T00:00:00Z",
        "comments": {
            "edges": [
                {"node": {
                    "createdAt": "2022-06-01T01:00:00Z"}}
            ],
            "totalCount": 1
        },
        "commits": {
            "totalCount": 1
        },
        "createdAt": "2022-06-01T00:00:00Z",
        "merged": True,
        "mergedAt": "2022-06-02T00:00:00Z",
        "reviews": {
            "edges": [
                {"node": {
                    "createdAt": "2022-06-01T02:00:00Z"}}
            ],
            "totalCount": 1
        },
        "state": "MERGED",
        "title": "Totally Legit Pull Request",
        "url": "https://TotallyLegitPullRequest.com"
    }}]
MOCK_QUERY_RETURN = {"data": {"repository": {"pullRequests": {"edges": []}}}}
NO_EDGES = []
PR_INFO = [{'title': 'Totally Legit Pull Request', 'open_length': '1 day, 0:00:00', 'comment_review_time': '1:00:00',
            'commits': 1, 'state': 'MERGED'}]


class AutomatedCertificateRenewalTestCases(unittest.TestCase):

    def test_get_start_date_success(self):
        github_metrics.SYS_ARGV_ONE = '2022-01-01'
        date_object = datetime.strptime(github_metrics.SYS_ARGV_ONE, '%Y-%m-%d')
        date = github_metrics.get_start_date()
        self.assertEqual(date, date_object)

    def test_get_start_date_convert_fail(self):
        github_metrics.SYS_ARGV_ONE = 'a'
        with self.assertRaises(SystemExit) as e:
            github_metrics.get_start_date()
        self.assertEqual(e.exception.code, 0)

    def test_get_start_date_convert_future(self):
        github_metrics.SYS_ARGV_ONE = '2050-01-01'
        with self.assertRaises(SystemExit) as e:
            github_metrics.get_start_date()
        self.assertEqual(e.exception.code, 1)

    def test_pull_requests_info_edges(self):
        date = datetime.strptime('2022-01-01', '%Y-%m-%d')
        expected_results = PR_INFO
        results = github_metrics.pull_requests_info(EDGES, date)
        self.assertEqual(results, expected_results)

    def test_pull_requests_info_no_edges(self):
        date = datetime.strptime('2022-01-01', '%Y-%m-%d')
        expected_results = []
        results = github_metrics.pull_requests_info(NO_EDGES, date)
        self.assertEqual(results, expected_results)

    def test_read_repos_file(self):
        github_metrics.REPOS_FILE = 'test_repos.txt'
        expected_results = [['gdcorp-infosec', 'dcu-scripts'], ['gdcorp-infosec', 'cset-sharktales']]
        results = github_metrics.read_repos_file()
        self.assertEqual(results, expected_results)

    def test_repo_merges_edges(self):
        date = datetime.strptime('2022-01-01', '%Y-%m-%d')
        expected_results = 1
        results = github_metrics.repo_merges(EDGES, date)
        self.assertEqual(results, expected_results)

    def test_repo_merges_no_edges(self):
        date = datetime.strptime('2022-01-01', '%Y-%m-%d')
        expected_results = 0
        results = github_metrics.repo_merges(NO_EDGES, date)
        self.assertEqual(results, expected_results)

    @patch('requests.post')
    def test_successful_slack_message(self, mock_post):
        github_metrics.SLACK_WEBHOOK_URL = 'test webhook url'
        github_metrics.slack_message('test')
        assert mock_post.called

    @patch('requests.post')
    def test_no_webhook_slack_message(self, mock_post):
        github_metrics.SLACK_WEBHOOK_URL = ''
        github_metrics.slack_message('test')
        assert mock_post.notcalled

    @patch.object(github_metrics, 'slack_message', return_value=None)
    @patch.object(github_metrics, 'build_message', return_value='test')
    @patch.object(github_metrics, 'pull_requests_info', return_value=PR_INFO)
    @patch.object(github_metrics, 'repo_merges', return_value=1)
    @patch.object(github_metrics, 'repo_pull_request_query', return_value=MOCK_QUERY_RETURN)
    @patch.object(github_metrics, 'read_repos_file', return_value=[['owner', 'name']])
    @patch.object(github_metrics, 'get_start_date', return_value=datetime.strptime('2022-01-01', '%Y-%m-%d'))
    def test_main(self, mock_date, mock_repos, mock_query, mock_merges, mock_pr_info, mock_build, mock_slack):
        github_metrics.main()
        assert mock_date.called
        assert mock_repos.called
        assert mock_query.called
        assert mock_merges.called
        assert mock_pr_info.called
        assert mock_build.called
        assert mock_slack.called

    @patch.object(github_metrics, 'slack_message', return_value=None)
    @patch.object(github_metrics, 'pull_requests_info', return_value=[])
    @patch.object(github_metrics, 'repo_merges', return_value=0)
    @patch.object(github_metrics, 'repo_pull_request_query', return_value=MOCK_QUERY_RETURN)
    @patch.object(github_metrics, 'read_repos_file', return_value=[['owner', 'name']])
    @patch.object(github_metrics, 'get_start_date', return_value=datetime.strptime('2022-01-01', '%Y-%m-%d'))
    def test_main_no_merges_or_prs(self, mock_date, mock_repos, mock_query, mock_merges, mock_pr_info, mock_slack):
        github_metrics.main()
        assert mock_date.called
        assert mock_repos.called
        assert mock_query.called
        assert mock_merges.called
        assert mock_pr_info.called
        assert mock_slack.called
