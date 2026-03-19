import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

from rich .console import Console 
from rich .panel import Panel 
from rich .progress import Progress ,SpinnerColumn ,TextColumn 
from rich .tree import Tree 
from rich import print as rprint 
from planner import create_plan 
from writer import write_project 

console =Console ()


def run (user_prompt :str )->None :
    """Full pipeline: plan → generate → write to disk."""

    console .rule ("[bold cyan] AI Code-Generation Agent[/bold cyan]")
    console .print (f"\n[bold]Prompt:[/bold] {user_prompt }\n")


    with Progress (
    SpinnerColumn (),
    TextColumn ("[progress.description]{task.description}"),
    console =console ,
    transient =True ,
    )as progress :
        progress .add_task ("Thinking and planning your project...",total =None )
        try :
            plan =create_plan (user_prompt )
        except ValueError as e :
            console .print (f"[bold red]Planning failed:[/bold red] {e }")
            return 
        except Exception as e :
            console .print (f"[bold red] Unexpected error during planning:[/bold red] {e }")
            return 


    console .print (
    Panel (
    f"[bold]{plan ['project_name']}[/bold]\n{plan .get ('description','')}",
    title ="[green]Plan Ready[/green]",
    border_style ="green",
    )
    )

    if plan .get ("tech_stack"):
        console .print (
        "[bold]Tech Stack:[/bold] "+", ".join (plan ["tech_stack"])
        )

    console .print ("\n[bold underline]Roadmap[/bold underline]")
    for step in plan .get ("roadmap",[]):
        console .print (f"  [yellow]→[/yellow] {step }")


    console .print ("\n[bold underline]Generating Files[/bold underline]")
    with Progress (
    SpinnerColumn (),
    TextColumn ("[progress.description]{task.description}"),
    console =console ,
    transient =True ,
    )as progress :
        progress .add_task ("Writing files to disk...",total =None )
        project_root ,written_files =write_project (plan )


    tree =Tree (f"[bold cyan]{plan ['project_name']}/[/bold cyan]")
    for f in written_files :

        parts =f .split ("/")[1 :]
        node =tree 
        for part in parts :
            node =node .add (f"[green]{part }[/green]")

    console .print (tree )

    console .print (
    Panel (
    f"[bold green]{len (written_files )} files generated[/bold green]\n"
    f"Location: [cyan]{project_root }[/cyan]",
    title ="[bold green] Done![/bold green]",
    border_style ="green",
    )
    )
