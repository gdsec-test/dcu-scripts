#!/bin/bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

check_repo_list() {

    repos="$2"
    if [ $# -ne 2 ]; then
        echo "Error: Exactly 2 argument required!"
        break
    fi
    while read -r line; do
        if [[ $repos == "repos_unique.txt" && "$1" == "$line" ]]; then
            echo "No ci script will be added!"
            break
        fi
        if [ "$1" == "$line" ]; then 
            echo 0 
        fi
    done <<<"$(cat $SCRIPT_DIR/"$2")"
}

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
           requiredStatusCheckContexts: []
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
           requiredStatusCheckContexts: []
           requiresStatusChecks:true
       }) { clientMutationId }
       }' -f repositoryId="$repositoryId" -f branch="master"


       mkdir -p .github/
       cp $SCRIPT_DIR/pull_request_template.md .github/pull_request_template.md
       cp $SCRIPT_DIR/../CODEOWNERS CODEOWNERS

       check_repo_golang=$(check_repo_list $repo "repos_golang.txt")
       check_repo_empty=$(check_repo_list $repo "repos_empty.txt")
       check_repo_unique=$(check_repo_list $repo "repos_unique.txt")
       if [[ $check_repo_empty == 0 ]]; then
            cp $SCRIPT_DIR/workflows/ci.yaml .github/workflows/ci.yaml
       elif [[ $check_repo_golang == 0 ]]; then
            cp $SCRIPT_DIR/go-ci.yaml .github/workflows/ci.yaml
       elif [[ $check_repo_unique == "No ci script will be added!" ]]; then
            echo "No ci script copied for:" $repo
       else
            cp $SCRIPT_DIR/py-ci.yaml .github/workflows/ci.yaml
       fi

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
