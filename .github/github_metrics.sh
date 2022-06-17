#!/bin/bash

DATE_STRING="$DATE_STRING"
cd github_metrics
pip install -r requirements.txt

python github_metrics.py $DATE_STRING
