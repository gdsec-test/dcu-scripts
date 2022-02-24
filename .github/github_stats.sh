#!/bin/bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL"
SLACK_CHANNEL="$SLACK_CHANNEL"

send_github_notification() {
    curl --silent -H 'Content-Type: application/json' --data "{\"channel\": \"#${SLACK_CHANNEL}\", \"username\": \"Github Stats\", \"as_user\": \"true\", \"link_names\": \"true\", \"icon_emoji\": \":github:\", \"attachments\": [{\"pretext\":\"$1\", \"text\": \"$2\"}] }" ${SLACK_WEBHOOK_URL}
}

get_github_current() {
    outstanding_issue_body=""
    outstanding_pr_body=""
    outstanding_alert_body=""
    while read repo; do
        CURRENT_RUN_ISSUES=$(gh issue list --repo $repo --json url | jq)
        CURRENT_RUN_PRs=$(gh pr list --repo $repo --json url | jq)
        OWNER=$(echo "$repo" |cut -d/ -f 1)
        REPO_NAME=$(echo "$repo" |cut -d/ -f 2)
        CURRENT_DEPENDABOT_ALERTS="["
        DEPENDABOT_ALERTS=$(gh api graphql -F owner="$OWNER" -F name="$REPO_NAME" -f query='query($name: String!, $owner: String!) { repository(owner: $owner, name: $name) { vulnerabilityAlerts(last: 100, states: OPEN) { nodes { securityVulnerability { package { name } advisory { identifiers { value }}}}}}}' | jq -r '[ .data.repository.vulnerabilityAlerts.nodes[].securityVulnerability.advisory.identifiers[0].value ] | @csv')
        CURRENT_DEPENDABOT_ALERTS="$CURRENT_DEPENDABOT_ALERTS$DEPENDABOT_ALERTS]"
        echo $CURRENT_DEPENDABOT_ALERTS
        if [ "$CURRENT_RUN_ISSUES" != "[]" ]; then
            outstanding_issue_body="$outstanding_issue_body\n<https://github.com/$repo/issues|$repo>"
        fi
        if [ "$CURRENT_RUN_PRs" != "[]" ]; then
            outstanding_pr_body="$outstanding_pr_body\n<https://github.com/$repo/pulls|$repo>"
        fi
        if [ "$CURRENT_DEPENDABOT_ALERTS" != "[]" ]; then
            outstanding_alert_body="$outstanding_alert_body\n<https://github.com/$repo/security/dependabot|$repo>"
        fi
        aws ssm put-parameter --region us-west-2 --name "/slackstats/repo/$repo" --type "String" --value "{\"issues\": $CURRENT_RUN_ISSUES, \"prs\": $CURRENT_RUN_PRs, \"dependabot\": $CURRENT_DEPENDABOT_ALERTS}" --overwrite >/dev/null
    done <<<"$(cat $SCRIPT_DIR/repos.txt)"
    send_github_notification "Outstanding Issues" "$outstanding_issue_body"
    send_github_notification "Outstanding PRs" "$outstanding_pr_body"
    send_github_notification "Outstanding Security Alerts" "$outstanding_alert_body"
}

get_github_differences() {
    outstanding_issues=false
    outstanding_prs=false
    outstanding_security_alerts=false
    outstanding_issue_body=""
    outstanding_pr_body=""
    outstanding_alert_body=""
    while read repo; do
        CURRENT_RUN_ISSUES=$(gh issue list --repo $repo --json url,title | jq)
        CURRENT_RUN_PRs=$(gh pr list --repo $repo --json url,title | jq)
        OWNER=$(echo "$repo" |cut -d/ -f 1)
        REPO_NAME=$(echo "$repo" |cut -d/ -f 2)
        CURRENT_DEPENDABOT_ALERTS="["
        DEPENDABOT_ALERTS=$(gh api graphql -F owner="$OWNER" -F name="$REPO_NAME" -f query='query($name: String!, $owner: String!) { repository(owner: $owner, name: $name) { vulnerabilityAlerts(last: 100, states: OPEN) { nodes { securityVulnerability { package { name } advisory { identifiers { value }}}}}}}' | jq -r '[ .data.repository.vulnerabilityAlerts.nodes[].securityVulnerability.advisory.identifiers[0].value ] | @csv')
        CURRENT_DEPENDABOT_ALERTS="$CURRENT_DEPENDABOT_ALERTS$DEPENDABOT_ALERTS]"

        LAST_RUN_DATA=$(aws ssm get-parameter --name "/slackstats/repo/$repo" --region us-west-2 >/dev/null && aws ssm get-parameter --name "/slackstats/repo/$repo" --region us-west-2 | jq -r '.Parameter.Value' || echo '{"issues":[],"prs":[],"dependabot":[]}')
        PREVIOUS_RUN_ISSUES=$(echo $LAST_RUN_DATA | jq '.issues')
        PREVIOUS_RUN_PRS=$(echo $LAST_RUN_DATA | jq '.prs')
        PREVIOUS_RUN_DEPENDABOT_ALERTS=$(echo $LAST_RUN_DATA | jq '.dependabot')
        update_ssm=false
        if [ "$CURRENT_RUN_ISSUES" != "$PREVIOUS_RUN_ISSUES" ]; then
            DIFFERENCE=$(python -c "curr = $CURRENT_RUN_ISSUES; prev = $PREVIOUS_RUN_ISSUES; diff = list(set(x['url'] for x in curr) - set(x['url'] for x in prev)); print(diff)")
            if [ "$DIFFERENCE" != "[]" ]; then
                outstanding_issues=true
                outstanding_issue_body="$outstanding_issue_body\n<https://github.com/$repo/issues|$repo>"
            fi
            update_ssm=true
        fi
        if [ "$CURRENT_RUN_PRs" != "$PREVIOUS_RUN_PRS" ]; then
            DIFFERENCE=$(python -c "curr = $CURRENT_RUN_PRs; prev = $PREVIOUS_RUN_PRS; diff = list(set(x['url'] for x in curr) - set(x['url'] for x in prev)); print(diff)")
            if [ "$DIFFERENCE" != "[]" ]; then
                outstanding_prs=true
                outstanding_pr_body="$outstanding_pr_body\n<https://github.com/$repo/pulls|$repo>"
            fi
            update_ssm=true
        fi
        if [ "$CURRENT_DEPENDABOT_ALERTS" != "$PREVIOUS_RUN_DEPENDABOT_ALERTS" ]; then
            DIFFERENCE=$(python -c "curr = $CURRENT_DEPENDABOT_ALERTS; prev = $PREVIOUS_RUN_DEPENDABOT_ALERTS; diff = list(set(x['url'] for x in curr) - set(x['url'] for x in prev)); print(diff)")
            if [ "$DIFFERENCE" != "[]" ]; then
                outstanding_security_alerts=true
                outstanding_alert_body="$outstanding_alert_body\n<https://github.com/$repo/security/dependabot|$repo>"
            fi
            update_ssm=true
        fi
        if [ "$update_ssm" = true ]; then
            aws ssm put-parameter --region us-west-2 --name "/slackstats/repo/$repo" --type "String" --value "{\"issues\": $CURRENT_RUN_ISSUES, \"prs\": $CURRENT_RUN_PRs, \"dependabot\": $CURRENT_DEPENDABOT_ALERTS}" --overwrite >/dev/null
        fi
    done <<<"$(cat $SCRIPT_DIR/repos.txt)"

    if [ "$outstanding_issues" = true ]; then
        send_github_notification "Outstanding Issues" "$outstanding_issue_body"
    fi
    if [ "$outstanding_prs" = true ]; then
        send_github_notification "Outstanding PRs" "$outstanding_pr_body"
    fi
    if [ "$outstanding_security_alerts" = true ]; then
        send_github_notification "Outstanding Security Alerts" "$outstanding_alert_body"
    fi
}

while getopts ":cd" option; do
    case $option in
    c)
        echo "Running github current sync"
        get_github_current
        exit
        ;;
    d)
        echo "Running github difference sync"
        get_github_differences
        exit
        ;;
    esac
done
