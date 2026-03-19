import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print


"""
AI Code-Generation Agent — CLI Entry Point
Usage:
    python main.py
    python main.py --prompt "create a portfolio website"
"""

import sys 
import argparse 
from rich .console import Console 
from agent import run 

console =Console ()

BANNER ="""
[bold cyan]
 ██████╗ ██████╗ ██████╗ ███████╗ ██████╗ ███████╗███╗   ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝ ██╔════╝████╗  ██║
██║     ██║   ██║██║  ██║█████╗  ██║  ███╗█████╗  ██╔██╗ ██║
██║     ██║   ██║██║  ██║██╔══╝  ██║   ██║██╔══╝  ██║╚██╗██║
╚██████╗╚██████╔╝██████╔╝███████╗╚██████╔╝███████╗██║ ╚████║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
[/bold cyan]
[dim]Local AI Agent that turns your ideas into real code[/dim]
"""

EXAMPLE_PROMPTS =[
"create a portfolio website with HTML, CSS and JavaScript",
"create a Python Flask REST API with /health and /items endpoints",
"create a simple todo app with localStorage using vanilla JS",
"create a React landing page for a SaaS product",
]


def main ():
    parser =argparse .ArgumentParser (
    description ="AI Code-Generation Agent — describe a project and get working code"
    )
    parser .add_argument (
    "--prompt","-p",
    type =str ,
    default =None ,
    help ="Project description (if omitted, enters interactive mode)",
    )
    args =parser .parse_args ()

    console .print (BANNER )

    if args .prompt :
        prompt =args .prompt .strip ()
    else :

        console .print ("[bold]Example prompts:[/bold]")
        for i ,ex in enumerate (EXAMPLE_PROMPTS ,1 ):
            console .print (f"  [dim]{i }.[/dim] {ex }")
        console .print ()

        try :
            prompt =console .input ("[bold cyan]> Describe your project:[/bold cyan] ").strip ()
        except (KeyboardInterrupt ,EOFError ):
            console .print ("\n[yellow]Exiting. Goodbye![/yellow]")
            sys .exit (0 )

    if not prompt :
        console .print ("[red]No prompt provided. Please describe what you want to build.[/red]")
        sys .exit (1 )

    run (prompt )


    try :
        again =console .input ("\n[dim]Build another project? (y/N):[/dim] ").strip ().lower ()
        if again =="y":
            main ()
    except (KeyboardInterrupt ,EOFError ):
        console .print ("\n[yellow]Goodbye![/yellow]")


if __name__ =="__main__":
    main ()
