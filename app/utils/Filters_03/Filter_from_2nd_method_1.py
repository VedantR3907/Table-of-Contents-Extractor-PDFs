import glob
import os
import re
import logging
# Define paths relative to the project root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TXT_DIRECTORY = os.path.join(ROOT_DIR, 'Output', '02')
EXTRACTED_DIRECTORY = os.path.join(ROOT_DIR, 'Output', 'extracted_content')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '01')
# Set up logging configuration to write to both console and log file
LOG_FILE = os.path.join(OUTPUT_DIR, "toc_extraction.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')  # Write logs to a file only
    ]
)
# Function to extract TOC entries
def extract_toc_entries_clean(text_content):
    toc_phrases = ["Table of Contents", "Contents", "CONTENTS"]
    # Compile regex patterns for exact or start-of-line matching
    toc_patterns = [re.compile(rf'^{re.escape(phrase)}\b', re.IGNORECASE) for phrase in toc_phrases]
    
    toc_start_index = None
    lines = text_content.split('\n')
    lines = lines[:700]  # Limit to first 700 lines for efficiency
    
    logging.info("Processing the first 700 lines of the text content.")

    # Step 1: Detect split TOC title lines and combine them
    joined_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if line matches any TOC phrase using regex
        if any(pattern.match(line) for pattern in toc_patterns):
            # Attempt to combine with the next line if it appears to be split
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            combined_line = f"{line} {next_line}" if next_line else line
            if any(pattern.match(combined_line) for pattern in toc_patterns):
                line = combined_line
                i += 1  # Skip the next line as it was combined
        
        # Handle the case where "ontents" is on one line and "C" on the next
        elif "ontents" in line.lower() and i + 1 < len(lines) and lines[i + 1].strip().upper() == "C":
            # Combine "C" + "ontents" to form "Contents"
            line = lines[i + 1].strip() + line
            i += 1  # Skip the next line as it was combined
        
        # Handle the case where "C" is on one line and "ontents" is on the next
        elif line.strip().upper() == "C" and i + 1 < len(lines) and "ontents" in lines[i + 1].strip().lower():
            # Combine "C" + "ontents" to form "Contents"
            line = line + lines[i + 1].strip()
            i += 1  # Skip the next line as it was combined
        
        # Normalize spaces in lines with symbols or redundant characters
        line = re.sub(r'[○\s]+', ' ', line)
        joined_lines.append(line)
        logging.debug(f"Processed and combined line {i}: {line}")
        i += 1

    logging.info("Finished joining split lines in the text content.")

    # Step 2: Look for TOC start using enhanced matching
    for i, line in enumerate(joined_lines):
        line = line.strip()
        logging.debug(f"Checking for TOC title at line {i}: {line}")
        if any(pattern.match(line) for pattern in toc_patterns):
            toc_start_index = i
            logging.info(f"TOC start detected at line {i}: {line}")
            break

    if toc_start_index is None:
        logging.warning("No TOC title found in the text.")
        return []

    toc_lines = joined_lines[toc_start_index:]  # Start from the TOC title
    toc_entries = []

    def count_valid_words(line):
        valid_words = [token for token in line.split() if token.isalnum() or re.match(r'^\d+(\.\d+)*$', token)]
        logging.debug(f"Counted {len(valid_words)} valid words in line: {line}")
        return len(valid_words)

    for i in range(len(toc_lines)):
        line = toc_lines[i].strip()
        logging.debug(f"Processing line {i}: '{line}'")

        next_five_lines = toc_lines[i:i + 5]
        long_lines_count = sum(1 for l in next_five_lines if count_valid_words(l) > 10)
        logging.debug(f"Next 5 lines from line {i}: {[l.strip() for l in next_five_lines]}")
        logging.debug(f"Number of 'long' lines in the next 5: {long_lines_count}")

        if long_lines_count >= 3:
            logging.info(f"Condition met at line {i}: 3 out of 5 lines have more than 10 words.")
            logging.info(f"Including the 5 lines that triggered the condition in the output.")
            toc_entries.extend({'heading': l, 'page_number': None} for l in next_five_lines if l.strip())
            logging.info("Stopping further processing.")
            break

        if line:
            toc_entries.append({'heading': line, 'page_number': None})
            logging.info(f"Added TOC entry: {line}")

    logging.info(f"TOC extraction completed. {len(toc_entries)} entries found.")
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
        
        text_content = '\n'.join(text_content.splitlines()[:700])

        toc_entries = extract_toc_entries_clean(text_content)

        output_file_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file_name)[0]}.txt")
        with open(output_file_path, 'w', encoding='utf-8') as toc_file:
            for entry in toc_entries:
                toc_file.write(f"{entry['heading']}\n")

        processed_files.append(file_name)  # Add the file name to the list

    # Print summary after processing all files
    if processed_files:
        print(f"{len(processed_files)} files have been processed: {', '.join(processed_files)}")