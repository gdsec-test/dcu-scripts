#!/bin/bash

export KUBECONFIG=./.github/static/local-config.yml
cd automated_certificate_renewal
pip install -r requirements.txt

python cert_renew.py expiring_certs 90
