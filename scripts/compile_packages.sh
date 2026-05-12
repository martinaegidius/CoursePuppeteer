#!/bin/bash

TEST=""

SOLVED_PATH="${TEST}sol_md"
UNSOLVED_PATH="${TEST}raw"
DOCS_PAYLOAD_PATH="${TEST}docs"
EXERCISES_PUBLIC_PATH="${TEST}exercises"
TMP_PATH="${TEST}tmp"


mkdir -p "${DOCS_PAYLOAD_PATH}" "${EXERCISES_PUBLIC_PATH}" "${TMP_PATH}"


### always copy HTML assets to docs folder before push
cp -r "${UNSOLVED_PATH}/javascripts" "${DOCS_PAYLOAD_PATH}/" 
cp -r "${UNSOLVED_PATH}/icons" "${DOCS_PAYLOAD_PATH}/"
cp -r "${UNSOLVED_PATH}/stylesheets" "${DOCS_PAYLOAD_PATH}/"
cp "${UNSOLVED_PATH}/README.md" "${DOCS_PAYLOAD_PATH}/"


now_ts=$(date +%s)
now=$(date "+%Y-%m-%d %H:%M")
echo "RUNNING SCHEDULED CHECK AT ${now}"


#what we wanna do: 
#1. compile a .md package from solved and unsolved path into docs and rename to ex-*.md. How to handle the renaming is still an open question.  
#2. always take all files from raw/ excepting *.ipynb into exercises/ folder 
# #3.

# to check or not to check if any change has happened.. for now lets just always act as if change has happened 
# to cp or cp that is the question 

tr -d '\r' < schedule.csv | {
    while IFS=, read -r exercise time
    do
        [[ -z "$exercise" ]] && continue
        # Quote the variable and use -eq for integer comparison
        csv_ts=$(date -d "$time" +%s 2>/dev/null)
        # Check if the date conversion was successful and compare
        mkdir -p ${DOCS_PAYLOAD_PATH}/${exercise}/
        mkdir -p ${EXERCISES_PUBLIC_PATH}/${exercise}/ 
        #copy all exercise data excepting .ipynb and .py to public path 
        cp -r ${UNSOLVED_PATH}/${exercise}/* ${EXERCISES_PUBLIC_PATH}/${exercise}/ #push everything as is in RAW to the the target folder. Needs to be raw because else it is mkdocs format. Remove solution if we are not past timestep; all exercise .py helpers are to be stored in data/ 
        if [ -n "$csv_ts" ] && [ "$(date +%s)" -gt "$csv_ts" ]; then
        #if [ $? -eq 0 ] && [ "$(date +%s)" -gt "$csv_ts" ]; then #this line says ./scripts/compile_packages.sh: line 47: [: : integer expression expected
            echo "Found active flag for $exercise on release-time: $time! Moving to payload"
            #copy .md files to docs
            #cp -r ${SOLVED_PATH}/${exercise}/ex*.md ${DOCS_PAYLOAD_PATH}/${exercise}/ #push solved version with integrated solutions to docs
            cp -r ${SOLVED_PATH}/${exercise}/*.md ${DOCS_PAYLOAD_PATH}/${exercise}/ #push solved version with integrated solutions to docs
             
        else
            echo "$exercise is inactive, release-time: $time. Moving unsolved version to docs payload and removing solutions from the $EXERCISES_PUBLIC_PATH"  
            #case; solutions not available yet; remove from public exercises payload 
            rm -f ${EXERCISES_PUBLIC_PATH}/${exercise}/*.ipynb #exclude solution
            rm -f ${EXERCISES_PUBLIC_PATH}/${exercise}/*.py #exclude solution
            #add unsolved .md to docs 
            cp -r ${UNSOLVED_PATH}/${exercise}/*.md ${DOCS_PAYLOAD_PATH}/${exercise}/ #push .md to docs 
        fi
        #also copy figure folders to the docs/ and exercises/ payloads. 
        figPathCopy=""
        figCandidates=(
            "${UNSOLVED_PATH}/${exercise}/figs"
            "${UNSOLVED_PATH}/${exercise}/figures"
        )
        figPathCopy=""
        for d in "${figCandidates[@]}"; do
            if [ -d "$d" ]; then
                figPathCopy="$d"
                echo "$d exists."
                break
            fi
        done
        if [ -n "$figPathCopy" ]; then
            cp -r "$figPathCopy" "${DOCS_PAYLOAD_PATH}/${exercise}/"
            cp -r "$figPathCopy" "${EXERCISES_PUBLIC_PATH}/${exercise}/"
        else
            echo "No figure directory found for exercise $exercise"
        fi 
    done
}
echo "Moving readme.md and mkdocs.yml to tmp folder ${TMP_PATH}"
mv "${TEST}readme.md" "${TMP_PATH}/readme.md" 
mv "${TEST}mkdocs.yml" "${TMP_PATH}/mkdocs.yml"
#echo "Moving ${UNSOLVED_PATH}/README.md to root temporarily for pushing to public main"
#cp "${UNSOLVED_PATH}/README.md" "${TEST}README.md"  #fra RAW/readme.md skal et dir op når push til public main 


# # Use a while loop with a file redirection instead of a pipe to keep variables accessible
# while IFS=, read -r exercise time
# do
#     # Skip empty lines or headers if they exist
#     [[ -z "$exercise" ]] && continue

#     csv_ts=$(date -d "$time" +%s 2>/dev/null)
    
#     mkdir -p "${DOCS_PAYLOAD_PATH}/${exercise}"
#     mkdir -p "${EXERCISES_PUBLIC_PATH}/${exercise}"

#     # Copy all exercise data. Note: removed the '*' from destination
#     cp -r "${UNSOLVED_PATH}/${exercise}/"* "${EXERCISES_PUBLIC_PATH}/${exercise}/"
    
#     if [ -n "$csv_ts" ] && [ "$now_ts" -gt "$csv_ts" ]; then
#         echo "Found active flag for $exercise on release-time: $time! Moving to payload"
#         # Copy solved version. Removed wildcard from destination.
#         cp -r "${SOLVED_PATH}/${exercise}/"ex*.md "${DOCS_PAYLOAD_PATH}/${exercise}/"
#     else
#         echo "$exercise is inactive, release-time: $time. Moving unsolved to docs."  
        
#         # Clean up sensitive files from public path
#         rm -f "${EXERCISES_PUBLIC_PATH}/${exercise}/"*.ipynb
#         rm -f "${EXERCISES_PUBLIC_PATH}/${exercise}/"*.py
        
#         # Copy unsolved .md to docs. Wildcard MUST be outside quotes.
#         cp -r "${UNSOLVED_PATH}/${exercise}/"*.md "${DOCS_PAYLOAD_PATH}/${exercise}/"
#     fi
# done < <(tr -d '\r' < schedule.csv)

# # Clean up / Move files
# [ -f "readme.md" ] && mv readme.md "${TMP_PATH}/readme.md" 
# [ -f "mkdocs.yml" ] && cp mkdocs.yml "${TMP_PATH}/mkdocs.yml"
# cp "${UNSOLVED_PATH}/README.md" "README.md"
