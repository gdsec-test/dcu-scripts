#!/bin/bash
#Create the backup directory
export BDIR=$BACKUP_DEST/`date +%Y-%m-%d`
mkdir -p $BDIR
COLLECTIONS_TO_DUMP=(`echo $COLLECTIONS`)

#Dump the required collections in the backup directory - one by one
#We can even dump the entire database in one go

for collection in ${COLLECTIONS_TO_DUMP[@]}; do
    mongodump --host=10.22.9.209 --port=27017 --db=$BACKUP_DB -u $USERNAME -p $PASSWORD --collection=$collection -o $BDIR --gzip
    if [ $? -ne 0 ]; then
        echo "Backup failed for the $collection collection of $BACKUP_DB database"
        /usr/local/sbin/slack "#ise-prod-alerts" "Backup failed for the $collection collection of $BACKUP_DB database"
    fi
done

find $BACKUP_DEST/* -type d -ctime +5 | xargs rm -rf

# Check if the nfs mount utilization is high
FOLDER_SIZE=`du -s | awk '{print $1;}'`
echo $FOLDER_SIZE
if [ "$FOLDER_SIZE" -gt "30000000" ]; then
    msg="Backup size greater than 30 GB. Check disk utilization"
    echo $msg
fi