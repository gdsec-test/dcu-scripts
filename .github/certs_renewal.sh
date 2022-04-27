#!/bin/bash

CSV_CERTS="$CSV_CERTS"
export KUBECONFIG=./.github/static/local-config.yml
cd automated_certificate_renewal
pip install -r requirements.txt

python cert_renew.py certs_renewal $CSV_CERTS
