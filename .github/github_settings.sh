#!/bin/bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

set_github_stats() {
    while read repo; do
        gh repo clone $repo
        pushd $(basename $repo) || exit 1
        mkdir -p .github/
        cp $SCRIPT_DIR/pull_request_template.md .github/pull_request_template.md
        # If there are changes in the repo create a PR.
        if [[ `git status --porcelain | wc -l` -gt 0 ]]; 
        then
            bname=github-settings-sync-$(date +"%Y-%M-%d_%H%M%S")
            git checkout -b $bname
            git add .
            git commit -m "Bringing inline with dcu-scripts"
            git push --set-upstream origin $bname
            gh pr create --title "Sync the repo settings" --body "Bringing inline with dcu-scripts"
        fi
        popd
        rm -rf $(basename $repo)
        exit 0
    done <<<"$(cat $SCRIPT_DIR/repos.txt)"
}

set_github_stats
