#!/usr/bin/env python3

from datetime import datetime, timedelta
from time import sleep
from typing import List, Optional, Tuple
import os
import requests
import json


def set_repo_token_secret(org: str, repo: str, value: str):
    os.popen(f'kubectl delete secret {org}-{repo}-reg-token').read()
    stream = os.popen(f'kubectl create secret generic {org}-{repo}-reg-token --from-literal=token="{value}"')
    print(stream.read())


def scale_to(org: str, repo: str, parallelism: int):
    stream = os.popen(f'kubectl scale --replicas={parallelism} deployment github-action-runner-{org}-{repo}')
    print(stream.read())


def get_runner(org: str, repo: str) -> Optional[dict]:
    stream = os.popen(f'kubectl get deploy github-action-runner-{org}-{repo} -o json 2>&1')
    result = stream.read()
    if 'Error from server (NotFound): deployments.apps' in result:
        return None
    return json.loads(result)


def get_runner_pods(org: str, repo: str) -> Optional[dict]:
    stream = os.popen(f'kubectl get pods -l=app=github-action-runner-{org}-{repo} -o json')
    result = json.loads(stream.read())
    if len(result.get('items', [])) == 0:
        return None
    return result.get('items', [])[0]


def create_runner(org: str, repo: str, runner_template: str) -> Optional[dict]:
    runner = get_runner(org, repo)
    if not runner:
        stream = os.popen(f'cat {runner_template}| sed "s/<org>/{org}/g"| sed "s/<repo>/{repo}/g" | kubectl apply -f -')
        print(stream.read())
        runner = get_runner(org, repo)
    return runner


def start_runner(org: str, repo: str, pat: str):
    runner = get_runner(org, repo)
    if not runner:
        raise Exception('Need to create the runner before starting it')

    if runner.get('status', {}).get('availableReplicas', 0) == 0:
        # Create registration token
        result = requests.post(f'https://api.github.com/repos/{org}/{repo}/actions/runners/registration-token', headers={'Authorization': f'token {pat}'})
        response = result.json()
        token = response['token']
        set_repo_token_secret(org, repo, token)
        scale_to(org, repo, 1)


def get_queued_jobs(org: str, repo: str, pat: str):
    result = requests.get(f'https://api.github.com/repos/{org}/{repo}/actions/runs?per_page=1', headers={'Authorization': f'token {pat}'})
    response = result.json()
    if len(response.get('workflow_runs', [])) > 0:
        if response.get('workflow_runs')[0].get("status") == "queued":
            return 1
    return 0


def stop_runner(org: str, repo: str):
    scale_to(org, repo, 0)
    set_repo_token_secret(org, repo, "")


def read_repo_list(repo_list_path: str) -> List[Tuple[str, str]]:
    repos = []
    with open(repo_list_path) as f:
        for line in f.readlines():
            repos.append(line.strip().split('/'))
    return repos


def main(repo_list_path: str, runner_template: str, pat: str):
    # Create initial deployment objects for all needed repos.
    repos = read_repo_list(repo_list_path)

    while True:
        for org, repo in repos:
            runner = get_runner(org, repo)
            if not runner:
                print(f'No active runner for {org}/{repo}, creating')
                runner = create_runner(org, repo, runner_template)
            if runner and runner.get('status', {}).get('availableReplicas', 0) == 0:
                jobs = get_queued_jobs(org, repo, pat)
                if jobs > 0:
                    print(f'Have {jobs} queued for {org}/{repo}, starting runner')
                    start_runner(org, repo, pat)
            elif runner:
                # Check to see how long the pod has been running for, if too long tear it down.
                pod = get_runner_pods(org, repo)
                if pod:
                    creationTime = datetime.strptime(pod.get('metadata', {}).get('creationTimestamp', '1980-01-01T01:00:00Z'), '%Y-%m-%dT%H:%M:%SZ')
                    if datetime.utcnow() - creationTime > timedelta(hours=8):
                        print(f'Old pod for {org}/{repo}, shutting down runner')
                        scale_to(org, repo, 0)
        sleep(90)


if __name__ == '__main__':
    main(
        os.getenv('REPO_LIST_PATH', '.github/repos.txt'),
        os.getenv('KUBE_RUNNER_TEMPLATE', 'containers/actions/base_worker.yml'),
        os.getenv('GITHUB_TOKEN', '')
    )
