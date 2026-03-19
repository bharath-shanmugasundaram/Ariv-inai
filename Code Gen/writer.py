import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

import os 
from pathlib import Path 


OUTPUT_ROOT =Path (__file__ ).parent /"output"


def write_project (plan :dict )->Path :
    """
    Materialise the plan on disk.
    Creates output/<project_name>/ and writes every file listed in plan["files"].
    Returns the Path of the project root.
    """
    project_name =plan ["project_name"]
    project_root =OUTPUT_ROOT /project_name 
    project_root .mkdir (parents =True ,exist_ok =True )

    written =[]
    for file_entry in plan .get ("files",[]):
        rel_path =file_entry .get ("path","")
        content =file_entry .get ("content","")

        if not rel_path :
            continue 

        target =project_root /rel_path 
        target .parent .mkdir (parents =True ,exist_ok =True )

        target .write_text (content ,encoding ="utf-8")
        written .append (str (target .relative_to (OUTPUT_ROOT )))

    return project_root ,written 
