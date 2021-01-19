# Scripts

## Automated Certificate Renewal
By investing in automation of certicate renewal process, we can save significant time and frustration for DCU team members previously burdened with manual process to request and renew certificates.

## Code style
This application is written in Python 3 and follows pep 8 style guide for python code.
 
## Screenshots
![Certificate Renewal](https://secureservernet-my.sharepoint.com/:i:/r/personal/agrover_godaddy_com/Documents/Screen%20Shot%202021-01-17%20at%2010.47.27%20AM.png?csf=1&web=1&e=GlKlcz "Logs")

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
2)  Execute the cert_renew.py script in a python3 environment
3)  Make sure new certificate/kubernetes secrets are updated in certificate_secret_mapping.json file

#### Certificate Renewal Process
[Click here to watch the automated certificate renewal process](https://secureservernet-my.sharepoint.com/:v:/r/personal/agrover_godaddy_com/Documents/Projects/Automated_Certificate_Renewal/zoom_0.mp4?csf=1&web=1&e=hI0Ivl)
