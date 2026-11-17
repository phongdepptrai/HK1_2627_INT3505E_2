#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports
npx --yes newman run books-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  -r cli,junit \
  --reporter-junit-export reports/junit.xml
