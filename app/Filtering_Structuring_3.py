import subprocess
import os
from tabulate import tabulate

# Paths relative to the main script
SCRIPT_DIR = os.path.join("utils", "Filters_03")
SCRIPT_1 = "Filter_from_2nd_method_1.py"
SCRIPT_2 = "Filter_Two_Points_2.py"
SCRIPT_3 = "Filter_Structure_TOC_3.py"

def run_script(script_name):
    """Function to change to SCRIPT_DIR and run a script by name"""
    original_dir = os.getcwd()  # Save the current working directory
    try:
        os.chdir(SCRIPT_DIR)  # Change to the directory with our scripts
        result = subprocess.run(["python", script_name], capture_output=True, text=True)
        if result.returncode != 0:
            output = f"Error:\n{result.stderr}"
        else:
            output = result.stdout.strip()
        return output
    finally:
        os.chdir(original_dir)  # Change back to the original directory

def filtering_main_3():
    # Initialize table data and run scripts here, as in the original code
    table_data = []

    # Step 1: Run Filter_from_2nd_method_1.py
    output_script_1 = run_script(SCRIPT_1)
    table_data.append(["Step 1: Filter_from_2nd_method_1.py", output_script_1])

    # Step 2: Run Filter_Two_Points_2.py
    output_script_2 = run_script(SCRIPT_2)
    table_data.append(["Step 2: Filter_Two_Points_2.py", output_script_2])

    # Step 3: Run Filter_Structure_TOC_3.py
    output_script_3 = run_script(SCRIPT_3)
    table_data.append(["Step 3: Filter_Structure_TOC_3.py", output_script_3])

    print(tabulate(table_data, headers=["Script", "Output"], tablefmt="fancy_grid"))
    print("All scripts have been run successfully.")

if __name__ == "__main__":
    filtering_main_3()