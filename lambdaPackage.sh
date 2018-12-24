#!/usr/bin/env bash

#
# Generates zip for upload to aws lambda
#
source venv/bin/activate
rm -rf ./lambda/ ./lambda.zip
mkdir ./lambda
cp *.py ./lambda/
cd ./lambda
pip install -r ../requirements.txt -t .
zip -r ../lambda.zip ./*
cd ..
rm -rf ./lambda/
deactivate
