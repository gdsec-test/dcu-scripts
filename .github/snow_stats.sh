#!/bin/bash

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL"
SLACK_CHANNEL="$SLACK_CHANNEL"
SNOW_USER="$SNOW_USER"
SNOW_PASS="$SNOW_PASS"
ASSIGN_GROUP="4b80f9c10f1b8e009d232ca8b1050e20"

send_slack_notification() {
    curl --silent -H 'Content-Type: application/json' --data "{\"channel\": \"#${SLACK_CHANNEL}\", \"username\": \"SNOW Stats\", \"as_user\": \"true\", \"link_names\": \"true\", \"icon_emoji\": \":snow:\", \"attachments\": [{\"pretext\":\"$1\", \"text\": \"$2\"}] }" ${SLACK_WEBHOOK_URL}
}

get_current_oncall() {
    CURRENT_USER_ID=$(curl -u "$SNOW_USER:$SNOW_PASS" --silent --location --request GET "https://godaddy.service-now.com/api/now/on_call_rota/whoisoncall?group_ids=$ASSIGN_GROUP" --header 'Accept: application/json' --header 'Content-Type: application/json' | jq -r '.result[0].userId')
    CURRENT_USER_NAME=$(curl -u "$SNOW_USER:$SNOW_PASS" --silent --location --request GET https://godaddy.service-now.com/api/now/table/sys_user/$CURRENT_USER_ID --header 'Accept: application/json' --header 'Content-Type: application/json' | jq -r '.result.user_name')

    send_slack_notification "On-call Today" "@$CURRENT_USER_NAME"
}

get_current_incidents() {
    CURRENT_INCS=$(curl -u "$SNOW_USER:$SNOW_PASS" --silent --location --request GET "https://godaddy.service-now.com/api/now/table/incident?assignment_group=$ASSIGN_GROUP&state=1" --header 'Accept: application/json' --header 'Content-Type: application/json' | jq -r '.result[] | "\n<https://godaddy.service-now.com/nav_to.do?uri=%2Fproblem.do%3Fsys_id%3D\(.sys_id)|\(.number)>"')
    send_slack_notification "Open Incidents Reports" "$CURRENT_INCS"
}

get_current_problems() {
    CURRENT_PRBs=$(curl -u "$SNOW_USER:$SNOW_PASS" --silent --location --request GET "https://godaddy.service-now.com/api/now/table/problem?assignment_group=$ASSIGN_GROUP&state=1" --header 'Accept: application/json' --header 'Content-Type: application/json' | jq -r '.result[] | "\n<https://godaddy.service-now.com/nav_to.do?uri=%2Fproblem.do%3Fsys_id%3D\(.sys_id)|\(.number)>"')
    send_slack_notification "Open Problem Reports" "$CURRENT_PRBs"
}

get_current_incidents
get_current_problems
get_current_oncall
