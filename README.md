# Scripts

#### Automated Certificate Renewal
To know more about this project, please go through the README document inside the automated_certificate_renewal folder.

#### Action Shoppers
If you need to lock or change a shopper account's password or send a templated email to a shopper, [this is the script](action_shoppers) you want.

#### Close Tickets
If you need to close a number of tickets given parameters that can be formulated into a db query, [this is the script](close_tickets) you want.

# Run the Github Settings Bash Script
#### ADDING A NEW REPO
Repos_golang is a list of golang repos with unit-test & test coverage. \
Repos_empty is a list of python repos with empty unit-test & test coverage. \
Repos_unique is a list of repos that need a unique ci script or none at all. \
Repos_k8s is a list of repos that need the k8s deployment script.

Set the codeQL analysis to 'advanced' in the settings of the repo. \
Add the repo name to the regular repos list and to the specific repo list if it fits said description. \
Then, run github_settings.sh. 

If the repo is unique and its ci script or the k8s script needs updating, it has to be manually updated. 