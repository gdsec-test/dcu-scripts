# Overview
Automatically suspend W&M accounts, and then create SNOW/Mongo tickets to track the change. This script was built/tested with python3. We suspend a W+M using this Orion, which creates an anomaly where the Orion account becomes suspended but the EComm account still shows active. The accounts end up out of sync.

## To Run
1. Change the variable `RUN_ENVIRONMENT` in suspend_csv.py to have a value of `prod`.
1. Set these INI settings `GOCENTRAL_SSL_CERT, GOCENTRAL_SSL_KEY, SNOW_PASS, DB_PASS` to the appropriate values.
1. You must install the packages cited in `requirements.txt`.
```sh
pip install private_pips.txt
pip install requirements.txt
```
1. Add the required information to a csv file called `accounts_to_suspend.csv`. This file must start with a header and the headers must be `account_id,shopper_id,domain_name`.
```csv
account_id,shopper_id,domain_name
ade82ff0-85ac-11eb-8139-0050569a4acb,4038908,nick.dev.godaddysites.com
```
1. Execute the suspend_csv.py script via `python suspend_csv.py`. The output will be stored in `results.csv`.
