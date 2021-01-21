# Automated Certificate Renewal

## Motivation
By investing in the automation of certificate renewal process, we can save significant time and frustration for DCU team members previously burdened with manual process to request and renew certificates.

## Code style
This application is written in Python 3 and follows pep 8 style guide for python code. The required packages are listed in requirements.txt file
 
## Screenshots
![Certificate Renewal](certificate_renewal.png?raw=true "Certificate Renewal")

## Certificate_Secret_Mapping json file schema
```
{
    "<certificate name>": {
        "secret": {
            "<secret name>": [<"dev"/"ote"/"prod">],
	    "<secret name>": [<"dev"/"ote"/"prod">]
        }
    }
}
```

## Installation
1)  Pull the main branch of Scripts repository
2)  Install the required package listed in requirements.txt in a python3 virtual environment
3)  Provide the path to the `apiuser.cmap.int.godaddy.com.crt` and `apiuser.cmap.int.godaddy.com.key` files in settings.ini file
4)  Execute the cert_renew.py script in the same virtual environment
5)  Make sure **new** certificate/kubernetes secrets are updated in certificate_secret_mapping.json file

## Unit Tests
To run the unit tests, simply execute `nosetests` in the virtual environment mentioned in the Installation section

## Certificate Renewal Process
[Click here to watch the automated certificate renewal process](https://secureservernet-my.sharepoint.com/:v:/g/personal/agrover_godaddy_com/ES-5k4M2ToRBnqLHeTGueKQB2G19J-6gY9m9h9A4Jo6oqg?e=u8MMjQ)

