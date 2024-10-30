import glob
import os
import re

# Define paths relative to the project root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TXT_DIRECTORY = os.path.join(ROOT_DIR, 'Output', '02')
EXTRACTED_DIRECTORY = os.path.join(ROOT_DIR, 'Output', 'extracted_content')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '01')

# Function to extract TOC entries
def extract_toc_entries_clean(text_content):
    toc_phrases = ["Table of Contents", "Contents", "Index", "CONTENTS"]
    toc_start_index = None
    lines = text_content.split('\n')
    
    # Step 1: Detect split TOC title lines and combine them
    joined_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if line is part of TOC title and combine if split
        if any(phrase.startswith(line) for phrase in toc_phrases):
            # Attempt to combine with the next line if it appears to be split
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            combined_line = f"{line}{next_line}"
            if any(phrase in combined_line for phrase in toc_phrases):
                line = combined_line
                i += 1  # Skip the next line as it was combined

        # Normalize spaces in lines with symbols or redundant characters
        line = re.sub(r'[○\s]+', ' ', line)
        joined_lines.append(line)
        i += 1
    
    # Step 2: Look for TOC start using enhanced matching
    for i, line in enumerate(joined_lines):
        line = line.strip()
        # Check for exact or partial match with any toc_phrase
        if any(phrase in line for phrase in toc_phrases):
            toc_start_index = i
            break

    if toc_start_index is None:
        return []

    # Process TOC entries from the identified start point
    toc_lines = joined_lines[toc_start_index:]
    toc_entries = []
    i = 0

    while i < len(toc_lines):
        line = toc_lines[i].strip()
        # Define valid lines that aren’t page numbers or headings
        valid_lines = [
            toc_lines[j] for j in range(i, min(i + 5, len(toc_lines)))
            if not re.match(r'^(\d+|[IVXLCDM]+|\d+(\.\d+)+)', toc_lines[j].strip(), re.IGNORECASE)
        ]
        if sum(len(valid_line.split()) > 10 for valid_line in valid_lines) >= 3:
            break

        if line:
            toc_entries.append({'heading': line, 'page_number': None})

        i += 1

    return toc_entries

def filter_files_by_line_count(folder_path, max_lines=20):
    filtered_files = []
    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))

    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) <= max_lines:
            filtered_files.append(os.path.basename(txt_file))

    return filtered_files

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filtered_files = filter_files_by_line_count(TXT_DIRECTORY, max_lines=20)

    processed_files = []  # List to store processed file names

    for file_name in filtered_files:
        extracted_file_path = os.path.join(EXTRACTED_DIRECTORY, file_name)

        with open(extracted_file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()

        toc_entries = extract_toc_entries_clean(text_content)

        output_file_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file_name)[0]}.txt")
        with open(output_file_path, 'w', encoding='utf-8') as toc_file:
            for entry in toc_entries:
                toc_file.write(f"{entry['heading']}\n")

        processed_files.append(file_name)  # Add the file name to the list

    # Print summary after processing all files
    if processed_files:
        print(f"{len(processed_files)} files have been processed: {', '.join(processed_files)}")