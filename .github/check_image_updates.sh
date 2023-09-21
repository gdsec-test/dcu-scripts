#!/bin/bash

SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL"
SLACK_CHANNEL="$SLACK_CHANNEL"
export AWS_REGION='us-west-2'
export KUBECONFIG=./.github/static/local-config.yml

send_slack_notification() {
    curl --silent -H 'Content-Type: application/json' --data "{\"channel\": \"#${SLACK_CHANNEL}\", \"username\": \"GCI Outdate Check\", \"as_user\": \"true\", \"link_names\": \"true\", \"icon_emoji\": \":docker:\", \"attachments\": [{\"pretext\":\"$1\", \"text\": \"$2\"}] }" ${SLACK_WEBHOOK_URL}
}
pip install -r containers/requirements.txt
RESULT=$(python containers/find_outdated_images.py prod-cset gdartifactory1.jfrog.io/docker-dcu-local)

send_slack_notification "Containers checked for updates" "$RESULT"
