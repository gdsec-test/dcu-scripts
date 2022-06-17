# GitHub Metrics

## Code style
This application is written in Python 3 and follows pep 8 style guide for python code.

## Repositories list file
This application uses a pre-existing text file listing DCU repositories. It is located at .github/repos.txt

Example of the repository owner/repository name format the file uses:
```
gdcorp-infosec/dcu-shadowfax
gdcorp-infosec/requeue
gdcorp-infosec/dcu-hubstream-actions
```

## Running the application
This application will be run from a triggered GitHub action and requires a date to be entered in string format of YYYY-MM-DD. The date is used as the start date for metrics.

If run from terminal, this application require operating system environmental variables of INFOSEC_PAT and SLACK_WEBHOOK_URL.

## Unit Tests
To run the unit tests, simply execute `nosetests` in the virtual environment mentioned in the Installation section