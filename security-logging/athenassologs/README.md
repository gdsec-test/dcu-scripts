# Manually running athena queries 
# Introduction
This document discusses how to run athena queries manually for the legal team.
The process is semi automated but requires frequent user actions. 

# Prerequisites for script
* Install [aws cli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* Python version 3.x preferably `3.11` 
* Download and install [aws-okta-processor](https://github.com/godaddy/aws-okta-processor)


# Environment set up
Once the pre-requisistes are installed. Perform the following steps:
* Create a virtual environment for python. `python -m venv .venv` 
* Activate virtual environment `source .venv/bin/activate` 
* Install requirements `pip install -r requirements.txt` 
  
# Running the script 

You will have to run the script 3 times. Each with a gap of approx 4 hours. 
* Legal team will give the query to be run in #sso-lookup slack channel. Copy
  the string part of the query into `shopper_email_query.txt`. Make sure you
  string starts and ends with `'"` 
* Activate virutal environment using `source .venv/bin/activate`
* Use `alias okta='eval $(aws-okta-processor authenticate -e -o godaddy.okta.com
  -u $USER -k $(openssl rand -hex 18))'` to log in to security prod ops role. 
* We need a unique identifier to be used across 3 runs of the script. Its
  recommended to use todays date as the uuid ie `20240227` . 
* Execute the first run of script by using the following command: `python
  main.py 1 <uuid>`
* After approx 4 hours check [athena
  ui](https://us-west-2.console.aws.amazon.com/athena/home?region=us-west-2#/query-editor/history)
  in us-west-2 and us-east-1 to see if all queries have completed. 
* Execute the second run of script by using the following command: `python
  main.py 2 <uuid>`
* After approx 4 hours check [athena
  ui](https://us-west-2.console.aws.amazon.com/athena/home?region=us-west-2#/query-editor/history)
  in us-west-2 and us-east-1 to see if all queries have completed.
* Execute the final run of script by using the following command: `python
  main.py 3 <uuid>`
* Make sure all athena queries have completed. 
* You can run `concat.sh` as `./concat.sh <uuid>` to combine all the results into a single file. 