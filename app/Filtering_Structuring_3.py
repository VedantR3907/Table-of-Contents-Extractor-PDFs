import subprocess
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.traceback import install

# Install rich traceback handler for better error display
install()

# Initialize Rich console
console = Console()

# Paths relative to the main script
SCRIPT_DIR = os.path.join("utils", "Filters_03")
SCRIPT_1 = "Filter_from_2nd_method_1.py"
SCRIPT_2 = "Filter_Two_Points_2.py"
SCRIPT_3 = "Filter_Remove_Extra_Text_3.py"
SCRIPT_4 = "Filter_Structure_TOC_4.py"

def run_script(script_name, progress):
    """Function to change to SCRIPT_DIR and run a script by name"""
    original_dir = os.getcwd()  # Save the current working directory
    try:
        os.chdir(SCRIPT_DIR)  # Change to the directory with our scripts
        task_id = progress.add_task(f"[cyan]Running {script_name}...", total=None)
        
        result = subprocess.run(["python", script_name], capture_output=True, text=True, encoding='utf-8')
        progress.remove_task(task_id)
        
        if result.returncode != 0:
            output = f"[red]Error:[/red]\n{result.stderr}"
        else:
            output = result.stdout.strip()
        return output
    finally:
        os.chdir(original_dir)  # Change back to the original directory

def filtering_main_3():
    # Create a rich table
    table = Table(title="Filtering Process Results", show_header=True, header_style="bold magenta")
    table.add_column("Step", style="cyan", width=40)
    table.add_column("Output", style="green")

    # Create progress context
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Display welcome message
        console.print(Panel("Starting Filtering Process", style="bold blue"))

        # Step 1: Run Filter_from_2nd_method_1.py
        console.print("\n[yellow]Step 1: Running first filter... (Filter_from_2nd_method_1)[/yellow]")
        output_script_1 = run_script(SCRIPT_1, progress)
        table.add_row("Step 1: Filter_from_2nd_method_1.py", output_script_1)

        # Step 2: Run Filter_Two_Points_2.py
        console.print("\n[yellow]Step 2: Running second filter... (Filter_Two_Points_2)[/yellow]")
        output_script_2 = run_script(SCRIPT_2, progress)
        table.add_row("Step 2: Filter_Two_Points_2.py", output_script_2)

        # Step 3: Run Filter_Structure_TOC_3.py
        console.print("\n[yellow]Step 3: Running third filter... (Filter_Remove_Extra_Text_3)[/yellow]")
        output_script_3 = run_script(SCRIPT_3, progress)
        table.add_row("Step 3: Filter_Remove_Extra_Text_3.py", output_script_3)

        # Step 4 is commented out as in original code
        # output_script_4 = run_script(SCRIPT_4, progress)
        # table.add_row("Step 4: Filter_Structure_TOC_4.py", output_script_4)

    # Print the final results table
    console.print("\n")
    console.print(table)
    console.print(Panel("All scripts have been run successfully!", 
                       style="bold green", 
                       subtitle="Process Complete"))

if __name__ == "__main__":
    filtering_main_3()