#!/bin/bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

set_github_stats() {
    while read repo; do
        gh repo clone $repo
        pushd $(basename $repo) || exit 1

        owner="$(dirname $repo)"
        name="$(basename $repo)"
        repositoryId="$(gh api graphql -f query='{repository(owner:"'$owner'",name:"'$name'"){id}}' -q .data.repository.id)"
        gh api graphql -f query="
        query {
            repository(owner: \"$owner\", name: \"$name\") {
                branchProtectionRules(first:100) {
                    nodes {
                        pattern
                        id
                    }
                    pageInfo {
                        endCursor
                        hasNextPage
                    }
                }
            }
        }" | jq -r '.data.repository.branchProtectionRules.nodes[].id' | while read line ; do gh api graphql -f query="mutation {deleteBranchProtectionRule(input:{branchProtectionRuleId: \"$line\"}) {clientMutationId}}" ; done
        gh api graphql -f query='
        mutation($repositoryId:ID!,$branch:String!) {
        createBranchProtectionRule(input: {
            repositoryId: $repositoryId
            pattern: $branch
            requiredApprovingReviewCount: 2
            requiresConversationResolution: true
            requiresCodeOwnerReviews: true
            requiresApprovingReviews: true
            dismissesStaleReviews: true
            restrictsPushes: true
            requiredStatusCheckContexts: ["dodge-tartufo-scan"]
            requiresStatusChecks:true
        }) { clientMutationId }
        }' -f repositoryId="$repositoryId" -f branch="main"
        gh api graphql -f query='
        mutation($repositoryId:ID!,$branch:String!) {
        createBranchProtectionRule(input: {
            repositoryId: $repositoryId
            pattern: $branch
            requiredApprovingReviewCount: 2
            requiresConversationResolution: true
            requiresCodeOwnerReviews: true
            requiresApprovingReviews: true
            dismissesStaleReviews: true
            restrictsPushes: true
            requiredStatusCheckContexts: ["dodge-tartufo-scan"]
            requiresStatusChecks:true
        }) { clientMutationId }
        }' -f repositoryId="$repositoryId" -f branch="master"

        mkdir -p .github/
        cp $SCRIPT_DIR/pull_request_template.md .github/pull_request_template.md
        cp $SCRIPT_DIR/../CODEOWNERS CODEOWNERS
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
    done <<<"$(cat $SCRIPT_DIR/repos.txt)"
}

set_github_stats
