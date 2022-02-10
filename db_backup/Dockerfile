FROM mongo:3.6.23
LABEL MAINTAINER=dcueng@godaddy.com

COPY slack.sh /usr/local/sbin/slack
COPY backup.sh /usr/local/sbin/backup_mongo
RUN chmod +x /usr/local/sbin/*
RUN apt-get update -y && apt-get install -y curl

ENV APP_SLACK_CHANNEL='#dcu_alerts'
ENV APP_SLACK_USERNAME='DB BACKUP'
ENV APP_SLACK_ICON_EMOJI=':-1:'

ENTRYPOINT ["/usr/local/sbin/backup_mongo"]
