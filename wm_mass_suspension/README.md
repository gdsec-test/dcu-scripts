# Overview
Automatically suspend W&M accounts, and then create SNOW/Mongo tickets to track the change. This script was built/tested with python3.

## To Run
1. Set these environment variables.
```sh
export GOCENTRAL_URL='https://services.orion.dev.sdl1.gdg/account/accountoperations.asmx'
export GOCENTRAL_SSL_CERT='/Users/nwade/secrets/dev-gocentral.crt'
export GOCENTRAL_SSL_KEY='/Users/nwade/secrets/dev-gocentral.key'
export SNOW_PASS=""
export SNOW_URL='https://godaddydev.service-now.com/api/now/table'
export SNOW_USER='dcuapi'
export SUSPENSION_NOTE="Auto-suspending W&M account as part of justforfans phishing cleanup"
export COLLECTION='incidents'
export DB='devphishstory'
export DB_USER='devuser'
export DB_PASS=''
export DB_IP='10.36.156.188'
```
2. You must install the packages cited in `requirements.txt`. 
```sh
pip install private_pips.txt
pip install requirements.txt
```
3. Add the required information to a csv file called `accounts_to_suspend.csv`.
```csv
account_id,shopper_id,domain_name
ade82ff0-85ac-11eb-8139-0050569a4acb,4038908,nick.dev.godaddysites.com
```
4. Execute the suspend_csv.py script via `python suspend_csv.py`. The output will be stored in `results.csv`.
