#!/bin/bash
./build.sh
aws s3 sync --exclude '*' --include '*.zip' . s3://devrel-lambda-functions
