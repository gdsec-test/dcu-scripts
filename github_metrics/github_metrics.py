from datetime import datetime

import json
import os
import requests
import sys


INFOSEC_PAT = os.getenv('INFOSEC_PAT')
REPOS_FILE = '../.github/repos.txt'
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
SYS_ARGV_ONE = sys.argv[1] if len(sys.argv) >= 1 else None

HEADERS = {"Authorization": f"token {INFOSEC_PAT}"}


def build_message(repos: list, start_date) -> str:
    message = f"Report start date: {start_date}"
    for repo in repos:
        if message:
            message += "\n\n"
        name = "Repository: {}".format(repo.get('repository'))
        merges = "Merges: {}".format(repo.get('merges'))
        pull_requests = "Pull requests created:"
        repo_details = "\n".join((name, merges, pull_requests))
        message += repo_details
        for pr in repo.get('pull_requests'):
            title = "\n  Title: {}".format(pr.get('title'))
            open_length = "    Open length: {}".format(pr.get('open_length'))
            comment_review_time = "    Time to first comment or review: {}".format(pr.get('comment_review_time'))
            commits = "    Commits: {}".format(pr.get('commits'))
            state = "    State: {}".format(pr.get('state'))
            pr_details = "\n".join((title, open_length, comment_review_time, commits, state))
            message += pr_details
    return f"```{message}```"


def get_start_date() -> datetime:
    if isinstance(SYS_ARGV_ONE, str):
        entered_date = ''
        try:
            entered_date = datetime.strptime(SYS_ARGV_ONE, '%Y-%m-%d')
        except Exception as e:
            print(f'Could not convert string to datetime. {e}')
            exit(0)

        now = datetime.now()
        if entered_date and entered_date > now:
            print(f'Exiting: entered date is a future date {entered_date}.')
            exit(1)

        return entered_date


def pull_requests_info(edges: list, start_date: datetime) -> list:
    """
    Example of where list is that is being looped through: edges list which contains a "node" dict for each pull request
    "data": {
        "repository": {
          "pullRequests": {
            "edges": []
    """
    pull_requests_stats = []
    for node in edges:
        if node.get('node').get('createdAt'):
            pr_created_date = datetime.strptime(node.get('node').get('createdAt'), '%Y-%m-%dT%H:%M:%SZ')
            if pr_created_date > start_date:
                title = node.get('node').get('title')

                # How long was/is PR open
                if node.get('node').get('mergedAt'):
                    open_length = datetime.strptime(node.get('node').get('mergedAt'), '%Y-%m-%dT%H:%M:%SZ') - pr_created_date
                elif node.get('node').get('closedAt'):
                    open_length = datetime.strptime(node.get('node').get('closedAt'), '%Y-%m-%dT%H:%M:%SZ') - pr_created_date
                else:
                    open_length = datetime.now() - pr_created_date

                # Determine time to first comment and review
                first_comment_review = None

                comments = node.get('node').get('comments').get('edges')
                if comments:
                    earliest_comment = datetime.strptime(comments[0].get('node').get('createdAt'), '%Y-%m-%dT%H:%M:%SZ')
                    first_comment_review = earliest_comment

                reviews = node.get('node').get('reviews').get('edges')
                if reviews:
                    earliest_review = datetime.strptime(reviews[0].get('node').get('createdAt'), '%Y-%m-%dT%H:%M:%SZ')
                    if not first_comment_review or earliest_review < first_comment_review:
                        first_comment_review = earliest_review

                if first_comment_review:
                    time_to_comment_review = str(first_comment_review - pr_created_date)
                else:
                    time_to_comment_review = 'None'

                # Number of commits for pull request
                commits = node.get('node').get('commits').get('totalCount')

                # Pull request state
                state = node.get('node').get('state')

                # Pull request info to add to repository pull requests list
                pr_info = {'title': title,
                           'open_length': str(open_length),
                           'comment_review_time': time_to_comment_review,
                           'commits': commits,
                           'state': state
                           }

                pull_requests_stats.append(pr_info)
    return pull_requests_stats


def read_repos_file() -> list:
    repos_file = open(REPOS_FILE)
    owner_repo_list = []
    for line in repos_file:
        line = line.rstrip()
        owner_repo_list.append(line.split('/'))
    return owner_repo_list  # example: [['gdcorp-infosec', 'dcu-shadowfax'], ['gdcorp-infosec', 'requeue']]


def repo_pull_request_query(owner: str, name: str) -> dict:
    query = '''
        query($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name){
                pullRequests(last:5) {
                    totalCount
                    edges {
                        node {
                            createdAt
                            closedAt
                            mergedAt
                            state
                            merged
                            title
                            url
                            reviews(first:1) {
                                totalCount
                                edges {
                                    node {
                                        createdAt
                                    }
                                }
                            }
                            comments(first:1) {
                                totalCount
                                edges {
                                    node {
                                        createdAt
                                    }
                                }
                            }
                            commits(last:1) {
                                totalCount
                            }
                        }
                    }
                }
            }
        }'''

    variables = {
        "owner": owner,
        "name": name
    }

    result = run_query(query, variables)
    return result


def run_query(query: str, variables: dict) -> dict:
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables},
                            headers=HEADERS)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


def repo_merges(edges: list, start_date: datetime) -> int:
    merges = 0
    for node in edges:
        if node.get('node').get('mergedAt'):
            merge_date = datetime.strptime(node.get('node').get('mergedAt'), '%Y-%m-%dT%H:%M:%SZ')
            if merge_date > start_date:
                merges += 1
    return merges


def slack_message(message: str) -> None:
    channel = '#cset-metrics'
    slack_user = 'GitHub Metrics Script'

    if SLACK_WEBHOOK_URL:
        try:
            payload = {'payload': json.dumps({
                'channel': channel,
                'username': slack_user,
                'text': message}
            )}
            response = requests.post(SLACK_WEBHOOK_URL, data=payload)
            if response.status_code != 200:
                print("Status: {} Headers: {} Error: {}".format(response.status_code, response.headers,
                                                                response.json()))
        except Exception as e:
            print(f'Error posting message to slack {e}')
    else:
        print('No OS environmental "SLACK_WEBHOOK_URL" found.')


def main():
    start_date = get_start_date()
    owner_repo_list = read_repos_file()
    slack_message_list = []

    for repo in owner_repo_list:
        owner = repo[0]
        name = repo[1]
        query_result = repo_pull_request_query(owner, name)

        if query_result:
            edges_list = query_result.get('data').get('repository').get('pullRequests').get('edges')
            total_merges = repo_merges(edges_list, start_date)
            pr_info = pull_requests_info(edges_list, start_date)

            if total_merges > 0 or pr_info:
                repo_info = {'repository': name,
                             'merges': total_merges,
                             'pull_requests': pr_info
                             }
                slack_message_list.append(repo_info)

    if slack_message_list:
        message = build_message(slack_message_list, start_date)
        slack_message(message)
    else:
        slack_message(f"```No merges or pull request to report starting with date {start_date}```")


if __name__ == '__main__':
    main()
