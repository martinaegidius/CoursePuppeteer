#!/bin/bash

# !!! FILE TO BE RUN BY GH ACTIONS UPON PUSH TO MAIN AFTER PARSE TO DOCS !!!

# Retrieve the list of files that were updated in the previous commit
LATEST_UPDATED_FILES=$(git diff-tree --no-commit-id --name-only -r HEAD~1 | grep "raw")
printf "FOUND FILES:\n$LATEST_UPDATED_FILES\n"

# Run script
# python scripts/append_md_updates.py $LATEST_UPDATED_FILES
python scripts/zip_material.py $LATEST_UPDATED_FILES

