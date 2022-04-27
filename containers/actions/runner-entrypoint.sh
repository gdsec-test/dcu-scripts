#!/bin/bash

./config.sh \
    --name $(hostname) \
    --token ${RUNNER_TOKEN} \
    --url https://github.com/${GITHUB_OWNER}/${GITHUB_REPOSITORY} \
    --work ${RUNNER_WORKDIR} \
    --unattended \
    --replace \
    --disableupdate \
    --labels csetkube

remove() {
    echo "Removing runner"
    ./config.sh remove --unattended --token "${RUNNER_TOKEN}"
}

trap 'remove; exit 130' INT
trap 'remove; exit 143' TERM

rm -rf $XDG_RUNTIME_DIR
mkdir -p $XDG_RUNTIME_DIR
dockerd-rootless-setuptool.sh install --skip-iptables
dockerd-rootless.sh --experimental &

./run.sh "$*" &
wait $!
