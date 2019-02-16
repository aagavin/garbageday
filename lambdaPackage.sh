#!/usr/bin/env bash

#
# Generates zip for upload to aws lambda
#
if [[ "$inCodeBuild" -ne "true" ]]
    then
        source venv/bin/activate
fi
rm -rf ./lambda/ ./lambda.zip
mkdir ./lambda
cp *.py ./lambda/
cd ./lambda
pip install -r ../requirements.txt -t .
zip -r ../lambda.zip ./*
cd ..
rm -rf ./lambda/
if [[ "$inCodeBuild" -ne "true" ]]
    then
        deactivate
fi
