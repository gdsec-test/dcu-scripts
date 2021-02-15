# Action Shoppers

## Motivation
DCU is often asked to change shopper account passwords on, or lock shopper accounts, or send templated emails to shoppers.  This script provides an automated and easy way to handle this process.

## Code style
This application is written in Python 3 and follows pep 8 style guide for python code. The required packages are listed in requirements.txt file
 
## Screenshots
![service](ss.png?raw=true "Screenshot of run log")

## Installation
1)  Pull the main branch of Scripts repository
2)  Install the required package listed in requirements.txt in a python3 virtual environment
3)  Provide the path to the `apiuser.cmap.int.godaddy.com`, `dcu.zeus.int.godaddy.com` & `phishstory.int.godaddy.com` crt and key files in settings.ini file
    
## Running Locally
Shopper account ids are required to scramble or email, while the lock functionality can accept an email address, username or shopper account id.
1)  Enter shopper ids to action into the `source.txt` file, one id per line
2)  Execute `python action_shopper.py` in the same virtual environment, providing `python` is Python version 3.
3)  Make sure to pay attention to the script prompts
4) If you notice output containing `Error while aggregating ShopperIDs`, it simply means that the shopper id provided is not associated with a valid shopper account

## Unit Tests
To run the unit tests, simply execute `nosetests` in the virtual environment mentioned in the Installation section