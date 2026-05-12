import re
import sys 
import os

def parse_mkdocs_file_for_public(tmp_path):
    """
        Parses mkdocs.yml file to sync with public_repository/origin/docs mkdocs.yml file
    """

    # Open mkdocs.yml file
    with open(tmp_path, "r", encoding="utf-8") as f:
        file = f.read()

    # Match start line of public/origin/docs mkdocs.yml file - remove all before pointer
    match = re.search(r'#\s*mkdocs.yml\s*\n', file)
    
    abs_path = os.path.join(os.getcwd(), tmp_path)
    fname = tmp_path.rsplit("/",1)[-1]
    file_out = os.path.dirname(os.path.dirname(abs_path))+"/"+fname
    print(file_out)
    if match:
    	with open(file_out, "w", encoding="utf-8") as f:
            f.write(file[match.start():])

    else:
        raise ValueError(f"""
        No match of '# mkdocs.yml' found in mkdocs.yml file - maybe you've deleted the line?
        Put after exclude_docs section.
        """)

if __name__ == "__main__":
    parse_mkdocs_file_for_public(sys.argv[1])
