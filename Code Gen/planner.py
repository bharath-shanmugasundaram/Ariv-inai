import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

import json 
import re 
from llm import generate 
from prompts import PLANNER_SYSTEM_PROMPT 


def _strip_json_fences (text :str )->str :
    """Remove markdown code fences if the model wraps JSON in them."""
    text =text .strip ()

    text =re .sub (r"^```(?:json)?\s*","",text )
    text =re .sub (r"\s*```$","",text )
    return text .strip ()


def create_plan (user_prompt :str )->dict :
    """
    Ask the LLM to generate a full project plan from the user's description.
    Returns a dict with keys: project_name, description, tech_stack, roadmap, files.
    """
    raw =generate (PLANNER_SYSTEM_PROMPT ,user_prompt )
    clean =_strip_json_fences (raw )

    try :
        plan =json .loads (clean )
    except json .JSONDecodeError as e :
        raise ValueError (
        f"LLM returned invalid JSON.\n\nError: {e }\n\nRaw response:\n{raw [:500 ]}..."
        )


    required_keys ={"project_name","description","roadmap","files"}
    missing =required_keys -set (plan .keys ())
    if missing :
        raise ValueError (f"Plan is missing required keys: {missing }")

    return plan 
