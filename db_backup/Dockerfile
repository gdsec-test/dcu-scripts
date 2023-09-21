FROM gdartifactory1.jfrog.io/docker-dcu-local/dcu-alpine3.15:3.3
LABEL MAINTAINER=dcueng@godaddy.com

USER root
RUN apk add curl findutils
RUN apk add mongodb-tools
COPY slack.sh /usr/local/sbin/slack
COPY backup.sh /usr/local/sbin/backup_mongo
RUN chmod +x /usr/local/sbin/*
RUN chown dcu:dcu /usr/local/sbin/*
USER dcu

ENV APP_SLACK_CHANNEL='#dcu_alerts'
ENV APP_SLACK_USERNAME='DB BACKUP'
ENV APP_SLACK_ICON_EMOJI=':-1:'

ENTRYPOINT ["/usr/local/sbin/backup_mongo"]
