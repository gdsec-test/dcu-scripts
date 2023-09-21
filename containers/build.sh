#!/bin/bash

SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL"
SLACK_CHANNEL="$SLACK_CHANNEL"

send_github_notification() {
    curl --silent -H 'Content-Type: application/json' --data "{\"channel\": \"#${SLACK_CHANNEL}\", \"username\": \"GCI Rebuild\", \"as_user\": \"true\", \"link_names\": \"true\", \"icon_emoji\": \":docker:\", \"attachments\": [{\"pretext\":\"$1\", \"text\": \"$2\"}] }" ${SLACK_WEBHOOK_URL}
}

for file in dockerfiles/Dockerfile.*; do 
    BUILD_TARGET=$(echo "$file" | awk '{split($0,a,"Dockerfile."); print a[2]}' )
    BASE_IMAGE=$(cat $file| grep FROM | awk '{print $2}')
    docker pull $BASE_IMAGE
    CURRENT_BASE_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' $BASE_IMAGE)
    CURRENT_MD5SUM=$(md5sum $file | awk '{print $1}')

    LAST_RUN_DATA=$(aws ssm get-parameter --name "/gci/$BUILD_TARGET" --region us-west-2 > /dev/null && aws ssm get-parameter --name "/gci/$BUILD_TARGET" --region us-west-2 | jq -r '.Parameter.Value' || echo '{"base_digest":"","base-version":"0","local-version":"0", "md5":""}')
    PREVIOUS_BASE_DIGEST=$(echo $LAST_RUN_DATA | jq -r '.base_digest')
    PREVIOUS_MD5SUM=$(echo $LAST_RUN_DATA | jq -r '.md5')
    PREVIOUS_BASE_VERSION=$(echo $LAST_RUN_DATA | jq -r '."base-version"')
    CURRENT_BASE_VERSION=$PREVIOUS_BASE_VERSION
    PREVIOUS_LOCAL_VERSION=$(echo $LAST_RUN_DATA | jq -r '."local-version"')
    CURRENT_LOCAL_VERSION=$PREVIOUS_LOCAL_VERSION
    need_rebuild=false

    if [ "$CURRENT_BASE_DIGEST" != "$PREVIOUS_BASE_DIGEST" ]; then
        need_rebuild=true
        CURRENT_BASE_VERSION=$((CURRENT_BASE_VERSION+1))
    fi

    if [ "$CURRENT_MD5SUM" != "$PREVIOUS_MD5SUM" ]; then
        need_rebuild=true
        CURRENT_LOCAL_VERSION=$((CURRENT_LOCAL_VERSION+1))
    fi

    if [ "$need_rebuild" = true ]; then
        DOCKER_TAG="$CURRENT_LOCAL_VERSION.$CURRENT_BASE_VERSION" make $BUILD_TARGET
        NEW_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' gdartifactory1.jfrog.io/docker-dcu-local/$BUILD_TARGET:$CURRENT_LOCAL_VERSION.$CURRENT_BASE_VERSION)
        aws ssm put-parameter --region us-west-2 --name "/gci/$BUILD_TARGET" --type "String" --value "{\"digest\":\"$NEW_DIGEST\",\"base_digest\":\"$CURRENT_BASE_DIGEST\",\"base-version\":\"$CURRENT_BASE_VERSION\",\"local-version\":\"$CURRENT_LOCAL_VERSION\", \"md5\":\"$CURRENT_MD5SUM\"}" --overwrite >/dev/null
        send_github_notification "Image Rebuilt" "gdartifactory1.jfrog.io/docker-dcu-local/$BUILD_TARGET:$CURRENT_LOCAL_VERSION.$CURRENT_BASE_VERSION"
    fi
done
