"""
Script is part of workflow for automatically integrating python solution content into markdown files to form complete solution form.
No dependencies. 
Does NOT handle cron-jobbing. 
"""
import shutil
import os 
from glob import glob 
import re
from pathlib import Path
from textwrap import indent
import json 
import textwrap

"""
    Goal of this file: only a single solution type in markdown. 
"""

"""
    Match python pattern of type: 
    #<START_SOLUTION 1>
    #<END_SOLUTION 1>
"""
GENERIC_SOLUTION_RE = re.compile(
    r'\s*#\s*<\s*START_SOLUTION\s+(\d+(?:,\d+)*|\d+-\d+)\s*>(?:\s*\n)*'
    r'(.*?)'
    r'\s*#\s*<\s*END_SOLUTION\s+\1\s*>',
    re.DOTALL
)

"""
    Match markdown pattern of type: 
    <!-- START_SOLUTION 1 -->
    <!-- END_SOLUTION 1 -->
"""
MD_BLOCK_RE = re.compile(
    r'<!--\s*START_SOLUTION\s+(\d+(?:,\d+)*|\d+-\d+)\s*-->'
    r'(.*?)'
    r'<!--\s*END_SOLUTION\s+\1\s*-->',
    re.DOTALL
)


START_RE = re.compile(r"^\s*#\s*<\s*START_SOLUTION\s+(\d+(?:,\d+)*|\d+-\d+)\s*>")
END_RE   = re.compile(r"^\s*#\s*<\s*END_SOLUTION\s+(\d+(?:,\d+)*|\d+-\d+)\s*>")
def validate_text(text: str):
    """
        Validates processed solution text by checking:
            (1) START <n>,END <n> are not flipped (END before START)
            (2) START <n>,END <n> are never repeated (e.g. START 2 found twice in document)
            (3) All STARTed solutions are ENDed
    """
    
    state = {} # { n: started|ended }
    for line in text.splitlines():

        # Match start regex
        if m := START_RE.match(line):
            print(f"START: {line}")
            n = m.group(1) # Only takes integer (n)

            # Raise error if already encountered
            if n in state:
                raise ValueError(f"{n} START repeated!!")
            state[n] = "started"

        # Match end regex
        elif m := END_RE.match(line):
            print(f"END: {line}")
            
            n = m.group(1)

            # Raise error if not already started
            if n not in state:
                raise ValueError(f"End statement: {n}; came before start! Flipped assignment!")
            elif state[n] == 'ended': # Ended repeated
                raise ValueError(f"{n} END repeated!!")
            state[n] = "ended"

    # Assert that all elements in state are ended
    for k, v in state.items():
        if v != "ended":
            raise ValueError(f"{k}; was never ended!")

    return True


def detect_file_solution(content: str):
    """Checks whether first character of each line is a !, which indicates file solution
    Args:
        content (str): a multiline string
    """
    x = content.split("\n")
    x = [l[0] for l in x if len(l)>0] #remove empty spaces
    output = [True if l=="!" else False for l in x]
    
    return output

def parse_code_cell(code):

    # Retrieve solution wrapper indices if present
    start_match = re.search(r"^#\s*<\s*START_SOLUTION\s+(\d+(?:,\d+)*|\d+-\d+)\s*>", code)
    end_match = re.search(r"\s*#\s*<\s*END_SOLUTION\s+(\d+(?:,\d+)*|\d+-\d+)\s*>", code)
    # start_match = re.search(r'^#\s*<\s*START_SOLUTION\s*(\d+)\s*>', code)
    # end_match = re.search(r'\s*#\s*<\s*END_SOLUTION\s*(\d+)\s*>', code)
    start_idx = start_match.end() if start_match else None
    end_idx = end_match.start() if end_match else None

    # Cases
    if start_idx and end_idx: # Both are present 
        text = code[:start_idx] + "```py\n" + code[start_idx:end_idx] + "\n```" + code[end_idx:]
    elif start_idx: # Only a start solution is present
        text = code[:start_idx] + "```py\n" + code[start_idx:] + "\n```"
    elif end_idx: # Only end is present
        text = "```py\n" + code[:end_idx] + "\n```" + code[end_idx:]
    else: # No wrapped solution - wrap in code md without further modification (should always be the case if input from .py file)
        text =  "\n```py\n" + code + "\n```\n"

    # Edgecase - append "\n" if it doesn't appear after END block
    text += "\n" if not text.endswith("\n") else ""

    return text


def merge_solutions(d1, d2):
    """
        Merge solutions found in new file with those already registered.
        Keys may not overlap, else duplicate solutions emerge.
    """

    overlap = d1.keys() & d2.keys()
    if overlap:
        raise ValueError(f"Duplicate keys found!: {overlap}")

    return d1 | d2 # Merges two dicts, quite cool

def extract_solutions(file: Path, curr_sols: dict):
    """
        Extract SOLUTION blocks from both .py and .ipynb files.
    """

    # Read .ipynb as combined text of code cells
    if is_ipynb := file.suffix == ".ipynb":
        nb = json.loads(file.read_text())
        text = ""
        #md_text = ""
        for cell in nb["cells"]:
            if cell["cell_type"] == "code": # Parse code block
                code = "".join(cell["source"]).rstrip()
                text += parse_code_cell(code)

            elif cell["cell_type"] == "markdown": # Parse markdown
                text += "".join(cell["source"]) + "\n"

    else: #.py
        text = file.read_text()

    # Run file validation
    print("Validating: ", file)
    assert validate_text(text)

    # Store solutions
    solutions = {}
    # print(f"is_ipynb = {is_ipynb}")
    for sol_num, content in GENERIC_SOLUTION_RE.findall(text):
        # print(f"NUM: {sol_num}\nCONTENT:\n{repr(content)}")

        if is_ipynb and True in detect_file_solution(content): 
            """
                Case: file solution embedded in .ipynb file ('!python ...'). Parse file
                content accordingly (remove line and insert file content).
                ONLY HANDLES CASES WHERE COMMAND IS ISOLATED IN CONTENT.
            """

            # Get fileline
            inner = content.strip()
            match = re.search(r"^!python[^\n]*", inner, re.MULTILINE) # MULTILINE changes the meaning of ^ and $ in a regex
            file_line = match.group() # Should always result in TRUE output
            
            # Retrieve filepath
            fname = file_line.lstrip("!python")
            fname = fname.strip() #safely strip blank space after "!python"
            sol_path = f"{str(file).rsplit("/",1)[0]}/{fname}"
            sol_path = sol_path.split(" ")[0] #often files have inputs - e.g. !python myfile.py 1 0 2 3. we just need the file contents, so we remove args by splitting on space. 
            sol_path = Path(sol_path)

            # Assert that path exists
            if not sol_path.exists():
                raise FileNotFoundError(
                    f"Referenced file '{fname}' not found for FILE_SOLUTION {sol_num} "
                    f"in {file}"
                )

            # Overwrite content and add solution
            content = sol_path.read_text().rstrip()
            solutions[sol_num] = f"Run from jupyter by executing solution file: \n\n```py\n{file_line}\n```\n\nin a code block.\nThe solution file contains:\n\n```py\n{content}\n```\n"  # treat as normal solution

        else: # Store SOLUTION normally
            if not is_ipynb: # Parse code cell if *.py file
                content = textwrap.dedent(content) # Remove unnecessary indentations
                content = parse_code_cell(content)

            solutions[sol_num] = content.rstrip()

    return merge_solutions(curr_sols, solutions)

def inject_into_markdown(md_file: Path, solutions: dict, output_dir: str):
    md = md_file.read_text()

    def repl(match):
        num_str, _ = match.groups()
        key = num_str

        if key not in solutions:
            return match.group(0)

        sol_content = solutions[key]

        # has_fence = "```" in sol_content
        # has_start_fence = "```py" in sol_content 
        # has_end_fence_only = "```" in sol_content and "```py" not in sol_content

        # has_both_fences = has_start_fence==True and has_end_fence_only==False and has_fence==True
        
            
        # if has_both_fences:
        #     # Do NOT wrap again — indent as-is
        #     sol_content = sol_content.rstrip()
        # elif has_start_fence and not has_end_fence_only: #case: end tags in code block will loose braces
        #     # Wrap in ``` and indent
        #     sol_content = sol_content.rstrip() + "\n```"
        # elif has_end_fence_only: 
        #     sol_content = "```py\n"+sol_content.rstrip()
        # else:
        #     sol_content = "```py\n" + sol_content.rstrip() + "\n```"

        indented = indent(sol_content.rstrip(), "    ")

        injected = (
            f"<!-- START_SOLUTION {num_str} -->\n"
            f"??? tip \"Solution {num_str}\"\n"
            f"{indented}\n"
            f"<!-- END_SOLUTION {num_str} -->"
        )

        return injected

    new_md = MD_BLOCK_RE.sub(repl, md)
    file_name = str(md_file).rsplit("/",1)[-1]
    out_file = Path(f"{output_dir}/{file_name}")
    with open(out_file, 'a+') as f:
        out_file.write_text(new_md)
    
   
def convert_list_to_string(li: list) -> str: 
    s = ""
    for i, s_ in enumerate(li): 
        s+=s_
        if i<len(li)-1:
            s+="/"
    return s 

if __name__=="__main__":
    DEBUG = False
    VERBOSE = False
    in_dir = "raw"
    out_folder_name = "sol_md"
    if DEBUG: 
        in_dir=f"tests/{in_dir}"
        all_md_exc_files = glob(f'{in_dir}/*/*.md', recursive=False)
        print(all_md_exc_files)
        complete_dir = f"tests/{out_folder_name}"
        print(f"!Running solution integrator in DEBUG setting in directory {complete_dir}...!")
    else:
        all_md_exc_files = glob(f'{in_dir}/*/*.md', recursive=False)
        complete_dir = f"{out_folder_name}"

    os.makedirs(complete_dir, exist_ok=True)
    print(f"Constructed {complete_dir} folder")
    INTEGRATION_COUNT = 0
    COPY_COUNT = 0
    copy_files = []
    integrated_files = []
    for md_file in sorted(all_md_exc_files):

        root_dir = md_file.rsplit("/",1)[0]
        dst_path = root_dir.replace(f"{in_dir}",f"{complete_dir}")
        os.makedirs(dst_path,exist_ok=True)
        
        # Get all .py and .iypnb files in target directory
        target_files = glob(f"{root_dir}/*.ipynb") + glob(f"{root_dir}/*.py")

        # No solution file present in root dir
        if len(target_files) == 0:
            file_name = str(md_file).rsplit("/",1)[-1]
            print(f"Error! No *.py or *.ipynb file found in folder {root_dir} = no solutions! Copying {md_file} to {dst_path}/{file_name}") 
            shutil.copyfile(md_file,f"{dst_path}/{file_name}")
            COPY_COUNT += 1
            copy_files.append(md_file)

        else: # Solution file present, loopping over all files

            solutions = {}
            for target_file in target_files:
                f_name = os.path.basename(target_file)
                print(f"Integrating {target_file} solutions into {dst_path}/{md_file}")
                solutions = extract_solutions(Path(target_file), solutions)
                shutil.copyfile(target_file, f"{dst_path}/{f_name}")

            if DEBUG and VERBOSE:
                print(f"{in_dir}\n{complete_dir}\n{root_dir}\nHELLO? {dst_path}\nFull path created at: {os.path.abspath(dst_path)}")

            inject_into_markdown(md_file=Path(md_file), solutions=solutions, output_dir=dst_path)
            integrated_files.append(md_file)
            INTEGRATION_COUNT += 1 
        
    print(f"Finished integrating solutions from python scripts into markdown files. Output dir: {complete_dir}")
    print(f"\n\n\n\n========== SOLUTION INTEGRATION STATUS =================\nIntegrated {INTEGRATION_COUNT} files out of {len(all_md_exc_files)}.\nBlankly copied {COPY_COUNT} files due to solutions not being available for files:\n\t{copy_files}.\n========================================================\n\n\n\n")

"""
PROBLEM: .md files present in data/.. Need to restrict the glob search depth.
MAYBE solved atm, double check tmrw
"""
