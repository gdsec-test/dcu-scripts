# Purpose

## AWS Auth
You can setup the aws-okta-processor and an easy alias for using it like so;
```sh
pipx install aws-okta-processor
alias okta='OKTA_DOMAIN=godaddy.okta.com; KEY=$(openssl rand -hex 18); eval $(aws-okta-processor authenticate -e -o $OKTA_DOMAIN -u $USER -k $KEY)'
```
Here are the accounts you will need to authenticate into to backfill specific indexes.
|index|AWS Account ID|
|-----|--------------|
|on_prem|811396126940|
|aws_cloudtrail|811396126940|
|aws_config|811396126940|
|aws_syslog|811396126940|
|aws_service_logs|811396126940|
|aws_eks|811396126940|
|aws_waf|811396126940|
|app_security|811396126940|
|windows_events_pki|811396126940|
|windows_events|811396126940|
|aws_guardduty|811396126940|

## How to run
You can run `python --index on_prem --start_date 2023-10-12 --end_date 2023-10-13` to backfill all of the logs in `on_prem` between the specified dates. You can filter down to just a specific tag like so; `python --index on_prem --start_date 2023-10-12 --end_date 2023-10-13 --tag SECURITY.GEN.ALL.CYBERARK.PROD`. You will need to auth into the required account before running the script.
