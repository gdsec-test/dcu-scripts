#!/bin/bash
date=$(date +'%Y_%m_%d')
echo 'GUID given is $1'
aws s3 cp s3://gd-security-prod-assets-athena-uswest2/march-athena-queries/$1/ . --recursive --exclude "*" --include "*.csv"
aws s3 cp s3://gd-security-prod-assets-athena/march-athena-queries/$1/ . --recursive --exclude "*" --include "*.csv"
cat *.csv > combined_legal_$date.csv