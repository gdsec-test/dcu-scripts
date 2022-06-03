import sys
from logging import INFO, StreamHandler, getLogger
from pythonjsonlogger.jsonlogger import JsonFormatter
import os
from requests import get
from datetime import datetime
import pandas as pd


class JiraStats:

    def __init__(self):
        self.logger = getLogger(__name__)
        self.logger.setLevel(INFO)
        logHandler = StreamHandler(sys.stdout)
        formatter = JsonFormatter()
        logHandler.setFormatter(formatter)
        self.logger.addHandler(logHandler)

    def ticket_dict(self):
        # get jira ticket data from api
        created_list = []
        closed_list = []
        issues_list = []
        points_list = []
        sprintStarted_list = []
        sprintClosed_list = []
        rollover_list = []
        status_list = []
        assignees_list = []
        count = 0
        for i in range(8):
            url = "http://jira.godaddy.com/rest/agile/1.0/board/4480/issue?startAt=" + str(i * 500) + "&maxResults=500"
            r = get(url, auth=(os.getenv("JOMAX_USER"), os.getenv("JOMAX_PASS")))
            issues = r.json()['issues']
            for issue in issues:
                issueName = issue['key']
                points = issue['fields']['customfield_10004']
                sprintClosed = None
                sprint = issue.get('fields').get('closedSprints', None)
                if sprint:
                    sprintStarted = sprint[0]['name']
                    sprintClosed = sprint[len(sprint) - 1]['name']
                else:
                    sprintStarted = None
                    start = issue.get('fields').get('sprint', None)
                    if start:
                        sprintStarted = start['name']

                rollover = True if len(issue.get('fields').get('closedSprints', {})) > 1 else False
                created = datetime.strptime(issue['fields']['created'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime("%d-%m-%Y")
                status = issue['fields']['status']['name']
                closed = datetime.strptime(issue['fields']['resolutiondate'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime(
                    "%d-%m-%Y") \
                    if issue.get('fields').get('resolutiondate', {}) else None
                assignee = issue['fields']['assignee']['name'] if issue.get('fields').get('assignee', {}) else None
                issues_list.append(issueName)
                points_list.append(points)
                sprintStarted_list.append(sprintStarted)
                sprintClosed_list.append(sprintClosed)
                rollover_list.append(rollover)
                status_list.append(status)

                assignees_list.append(assignee)
                created_list.append(created)
                closed_list.append(closed)
                count += 1
                if count % 500 == 0:
                    print(str(count) + " issues added")
            data = pd.DataFrame({"Issue": issues_list, "Assignee": assignees_list, "Points": points_list,
                                 "Sprint Started": sprintStarted_list, "Sprint Closed": sprintClosed_list,
                                 "Status": status_list, "Created": created_list, "Closed": closed_list,
                                 "Roll": rollover_list})
            data.to_excel('jira_metrics.xlsx', sheet_name='sheet1', index=False)
        print("total issues added: " + str(count))


if __name__ == "__main__":
    running = JiraStats()
    running.ticket_dict()
