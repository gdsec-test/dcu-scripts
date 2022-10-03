#!/bin/bash

set_github_stats() {
    while read repo; do
        gh repo clone $repo scratch/
        pushd scratch/
        mkdir -p .github/
        cp $SCRIPT_DIR/.github/pull_request_template.md .github/pull_request_template.md
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
        rm -rf scratch/
    done <<<"$(cat $SCRIPT_DIR/repos.txt)"
}

set_github_stats
