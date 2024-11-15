import os
import re

# Define paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '03')
OUTPUT_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '04')

def extract_clean_toc(text):
    toc_start_phrases = ["Table of Contents", "Contents", "CONTENTS", "Index"]
    toc_start = None
    for phrase in toc_start_phrases:
        match = re.search(phrase, text)
        if match:
            toc_start = match.end()
            break
    
    if toc_start is None:
        return "No TOC found."
    
    toc_text = text[toc_start:]
    
    chapter_pattern = re.compile(
        r'^(Chapter \d+|Lecture \d+|Module[-\d]+|PART \d+|[IVXLCDM]+\.|\d+:\s*.+|\d+(\.\d+)*(\.0)?)',
        re.IGNORECASE
    )
    
    lines = toc_text.splitlines()
    structured_toc = []
    level_stack = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = chapter_pattern.match(line)
        if match:
            numbering = match.group(1)
            current_level = determine_level(numbering)
            
            while level_stack and level_stack[-1] >= current_level:
                level_stack.pop()
            
            level_stack.append(current_level)
            indentation = '    ' * (len(level_stack) - 1)
            structured_toc.append(f"{indentation}{line}")
        else:
            if level_stack:
                indentation = '    ' * len(level_stack)
                structured_toc.append(f"{indentation}{line}")
            else:
                structured_toc.append(line)
        
        if len(line.split()) > 20:
            break
    
    return "\n".join(structured_toc)

def determine_level(numbering):
    if re.match(r'^Chapter \d+', numbering, re.IGNORECASE):
        return 1
    elif re.match(r'^\d+:\s*', numbering):
        return 1
    elif numbering.endswith('.0'):
        return 1
    elif re.match(r'^\d+(\.\d+)+$', numbering):
        return numbering.count('.') + 1
    elif re.match(r'^\d+$', numbering):
        return 2
    elif re.match(r'^[IVXLCDM]+\.', numbering, re.IGNORECASE):
        return 1
    else:
        return 2

def process_txt_files(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    
    processed_files = []  # List to store processed file names

    for txt_file in os.listdir(input_folder):
        if txt_file.endswith(".txt"):
            input_file_path = os.path.join(input_folder, txt_file)
            output_file_path = os.path.join(output_folder, txt_file)
            
            with open(input_file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            structured_toc = extract_clean_toc(text_content)
            
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                output_file.write(structured_toc)
            
            processed_files.append(txt_file)  # Add the file name to the list

    # Print summary after processing all files
    if processed_files:
        print(f"{len(processed_files)} files have been processed: {', '.join(processed_files)}")

if __name__ == "__main__":
    process_txt_files(INPUT_FOLDER, OUTPUT_FOLDER)