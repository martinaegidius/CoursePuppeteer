import os
import sys
import zipfile
import shutil
from pathlib import Path
import re
from datetime import datetime
import csv

def write_zip(zip_file, exercise_dir, material_folders, sol_files=[]):
    """
        Write to zip file.
    """

    # Create zip folder over material folders
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as z:

        # Loop over material folders
        for dir in material_folders:
            dir = Path(dir)
            for file in dir.rglob("*"): # Descend into dir recursively, writing to z
                if file.is_file():
                    z.write(file, arcname=file.relative_to(exercise_dir))

        for f in sol_files: # Add solution files if specified
            f = Path(f)
            z.write(f, arcname = f.relative_to(exercise_dir))


def parse_sol_md(sol_dir, section_names, sol_out_file):
    """
        Parses solution link into exercise README.md files. 

        Added into the 'download data' section.
    """

    # Line to add
    sol_line = f"***Solution is now available! Download the full solution from here:*** [Solution](../{sol_out_file}){{ .md-button .md-button--primary .inline-button }}"

    # --- Add line to TOP of all *.md files in sol_dir --- #

    for e in Path(sol_dir).iterdir():
        if e.is_file() and e.suffix in ".md": # Modify *.md files

            # Read file
            fpath = os.path.join(str(sol_dir), e.name)
            with open(fpath, "r") as f:
                content = f.read()

            # Search for 'Latest Update' pattern - add sol_line to end
            if m := re.search(r"\s*_Latest\s*(Page|Website)\s*Update:\s*\d+-\d+-\d+_\s*", content, re.IGNORECASE):

                # Split file wrt. head
                head, content = content[:m.end()], content[m.end():]
                
                # Add sol_line to end of head
                head += f"\n\n{sol_line}\n\n"

            else: # If no match, add to top of file
                head = f"{sol_line}\n\n"

            # Write to file
            with open(fpath, "w") as f:
                f.write(head + content)

    # --- --- #
    
    # --- Add line to BOTTOM of README.md file --- #

    # Read file
    print("GOING INTO 2!")
    fpath = os.path.join(sol_dir, "README.md")
    with open(fpath, "r") as f:
        content = f.read()

    # If line already exists, return:
    if sol_line in content:
        return

    # Match time already found in docs file
    parse_section_names = list(
        map(lambda x: x.replace(" ", "\\s*"), section_names)
    )

    # Set regex pattern:
    pattern = rf"""
    ^\#+\s*({ '|'.join(parse_section_names) })\s*\n
    .*?
    (?=\n\#|\Z)
    """
        # Catches the download data section! The title header for this section needs to be
        # specified in the DATA_SECTION_NAMES to be cought (Not case nor blankspace sensitive)

    if m := re.search(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL | re.VERBOSE):

        # Split file wrt. head
        head, tail = content[:m.end()], content[m.end():]

        # Add to head
        head += f"\n\n{sol_line}\n\n"

        # Write to file
        with open(fpath, "w") as f:
            f.write(head + tail)

    # --- --- #

def zip_material(modified_files):
    """
        Zip data files and solution if due.

        Robust to partial releases for future iterations (i.e. if 'git init -b docs' is
        no longer used, function will only push modified files / new solutions upon).
    """

    # Variables
    ROOT = "raw"
    DOWNLOAD_DIR = os.path.join(ROOT, "downloads")
    SOL_MD_DIR = "sol_md"
    DATA_SECTION_NAMES = ["Getting The Data", "Exercise Data and Material"]
    candidates = ["data", "theory"] # List of data directories
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    print(f"DOWNLOAD_DIR: {DOWNLOAD_DIR}")
    print(f"MODIFIED FILES IN RAW (last commit):\n{modified_files}")

    # Retrieve schedule and parse to set if solution is released:
    released_set = set()
    now = datetime.now()
    print(f"NOW: {now}")
    with open("schedule.csv", newline="") as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:

            # Skip empty rows and setup entries
            if not row or "setup" in row[0]:
                continue

            # Retrieve ID and datetime object
            ex_idx = str(row[0])
            release_time = datetime.strptime(row[1].lstrip(), "%Y-%m-%d %H:%M")
            print(f"TIME: {release_time}")

            if release_time < now: # Compare and add
                released_set.add(os.path.join(ROOT, ex_idx))

    print(f"REL_SET: {released_set}")

    # Given modified files, retrieve all folders that are of relevance for zipping data:
    ROI_modified = set()
    for f in modified_files:
        path = Path(f)
        for part in path.parents:
            if part.name in candidates:
                ROI_modified.add(str(path.parent.parent))
                break

        # Add all .py and .ipynb files
        if f.endswith((".py", ".ipynb")):
            ROI_modified.add(f)


    # Iterate through raw directory and make zip folders if necessary (data, solutions)
    for e in os.scandir(ROOT):

        # Go deeper if exercise directory (not setup)
        if m := re.search(r"ex(\d+[A-Za-z]?)-((?!setup).+)$", e.name, re.IGNORECASE):

            exercise_dir = Path(os.path.join(ROOT, e.name))
            ex_idx = m.group(1)
            zip_file = os.path.join(DOWNLOAD_DIR, f"material-{ex_idx}.zip")
            print(f"exercise_dir: {exercise_dir}")
            print(f"zip_file: {zip_file}")


            # Fetch relevant data subfolders
            material_folders = []
            for cand in candidates:
                candidate_path = os.path.join(exercise_dir, cand)
                if os.path.exists(candidate_path):
                    material_folders.append(candidate_path)

            
            # Add solution zip if released
            if str(exercise_dir) in released_set:
                print(f"Released: {exercise_dir}")
                sol_zip_file = os.path.join(DOWNLOAD_DIR, f"sol_material-{ex_idx}.zip")

                # Find solution files
                sol_files = []
                for e in exercise_dir.iterdir():
                    if e.is_file() and e.suffix in (".py", ".ipynb"):
                        sol_files.append(os.path.join(str(exercise_dir), e.name))

                if not os.path.exists(sol_zip_file) or any(f in modified_files for f in sol_files):

                    # Write to zip and parse download link into sol_md/**/README.md file
                    write_zip(sol_zip_file, exercise_dir, material_folders, sol_files=sol_files)
                    sol_md_dir = str(exercise_dir).replace(ROOT, SOL_MD_DIR)
                    sol_out_file = sol_zip_file.replace(f"{ROOT}/", "")
                    parse_sol_md(sol_md_dir, DATA_SECTION_NAMES, sol_out_file)
                    print("*ADDED SOLUTION*")

                else:
                    print("Solution exists and not modified - SKIPPING ADDING SOLUTION ZIP!")


            # Skip zipping if no data folders exist for exercise
            if not material_folders:
                print("Exercise has no data! Skipping zip...")
                continue

            # Create zip folder if not already exists or directory has been modified
            if not os.path.exists(zip_file) or str(exercise_dir) in ROI_modified:
                write_zip(zip_file, exercise_dir, material_folders)
                print("^ADDED DATA^")
            else:
                print("Not modified and already exists - SKIPPING DATA ZIP!")
            print()

if __name__ == "__main__":
    zip_material(sys.argv[1:])
