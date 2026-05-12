#!/bin/bash

TEST=""
TMP_PATH="tmp"
#rm -f "${TEST}README.md"
rm -f "${TEST}mkdocs.yml" #this is the mkdocs file for the docs/ branch on public - we also want a private version for local testing
echo "Unpacking temporary folder ${TEST}${TMP_PATH}..."
mv  "${TEST}${TMP_PATH}/readme.md" "${TEST}readme.md"
mv  "${TEST}${TMP_PATH}/mkdocs.yml" "${TEST}mkdocs.yml"
rm -rf "${TEST}tmp" 
echo "Removed ${TEST}${TMP_PATH} folder"