#!/bin/bash
#make directory TESTS which completely simulates root for unit testing 
rm -rf TESTS/
mkdir TESTS
cp -r raw TESTS/
cp mkdocs.yml TESTS/mkdocs.yml 
cp readme.md TESTS/readme.md 

python3 scripts/integrate_solutions_in_md.py
./scripts/compile_packages.sh
python3 scripts/parse_mkdocs_yml.py TESTS/tmp/mkdocs.yml
./scripts/clean_up.sh
