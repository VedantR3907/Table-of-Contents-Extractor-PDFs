import os
import re
import shutil

# Define paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '03')
OUTPUT_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '04')

# Regular expression to detect chapter/part patterns
chapter_part_pattern = re.compile(
    r'^(Chapter|Part)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|[IVXLCDM]+)[\s\-\.:]?',
    re.IGNORECASE
)

def process_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Process only if line count is greater than 500
    if len(lines) <= 500:
        return None  # Skip processing for files with 500 lines or fewer

    processed_lines = []
    line_count = 0
    removal_triggered = False

    for i, line in enumerate(lines):
        line = line.strip()

        # Check for chapter/part indicators
        if chapter_part_pattern.match(line):
            line_count = 0  # Reset the line counter on finding a chapter/part indicator
            removal_triggered = False  # Reset removal flag since we found a valid section
            processed_lines.append(line + '\n')  # Keep the chapter/part line
        else:
            line_count += 1  # Increment counter for non-chapter/part lines

            # If we reach 15 consecutive lines without chapter/part markers, trigger removal
            if line_count >= 15:
                removal_triggered = True
                break  # Stop processing further lines after reaching the removal condition
            
            # Add the line to processed lines if no removal has been triggered
            if not removal_triggered:
                processed_lines.append(line + '\n')

    return processed_lines

def process_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    processed_files = []

    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)

            # Copy the file to the output folder, whether processed or not
            shutil.copy2(input_file_path, output_file_path)

            # Process the file if it meets the line count condition
            processed_content = process_text_file(input_file_path)
            if processed_content:
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(processed_content)
                processed_files.append(filename)

    # Print summary after processing all files
    if processed_files:
        print(f"{len(processed_files)} files have been processed and saved in {output_folder}: {', '.join(processed_files)}")
    else:
        print(f"All files from {input_folder} have been copied to {output_folder}.")

if __name__ == "__main__":
    process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
