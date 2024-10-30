import os
import re

# Define paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '01')
OUTPUT_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '02')
LOG_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '02_logs')

def is_numbering(line):
    numbering_patterns = [
        r'^\s*\d+(\s|[\.\):])',
        r'^\s*\d+\.\d+',
        r'^\s*[IVXLCDM]+(\s|[\.\):])',
        r'^\s*[•\-–—]\s',
        r'^\s*\([a-zA-Z0-9]+\)',
        r'^\s*[a-zA-Z]\)',
        r'^\s*(Chapter|Part|Act)\s+\d+.*',                        # 7. Chapter/Part/Act followed by a number (e.g., 'Chapter 1: Introduction', 'Part 3)', 'Act 4')
        r'^\s*(Chapter|Part|Act)\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|I|II|III|IV|V|VI|VII|VIII|IX|X).*',  # 8. Chapter/Part/Act followed by a written number or Roman numeral (e.g., 'Chapter one: Overview', 'Act III, Scene One')

    ]
    for pattern in numbering_patterns:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    return False

def process_file(file_path, log_file):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    processed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if is_numbering(line):
            log_file.write(f"Numbered line detected, resetting counter: {line.strip()}\n")
            processed_lines.append(line)
            i += 1
        else:
            non_numbering_counter = 0
            sequence_lines = []
            log_file.write(f"Starting counter at line {i+1}: {line.strip()} -------> counter {non_numbering_counter}\n")
            while i < len(lines) and not is_numbering(lines[i]):
                sequence_lines.append(lines[i])
                non_numbering_counter += 1
                log_file.write(f"Continuing counter at line {i+1}: {lines[i].strip()} -------> counter {non_numbering_counter}\n")
                i += 1

            if non_numbering_counter >= 5:
                total_words = sum(len(re.findall(r'\w+', l)) for l in sequence_lines)  # noqa: E741
                average_words = total_words / non_numbering_counter
                log_file.write(f"Non-numbered block identified (Average words: {average_words}):\n{''.join(sequence_lines)}\n")

                if average_words > 6:
                    log_file.write(f"Block removed:\n{''.join(sequence_lines)}\n")
                    continue
                else:
                    log_file.write(f"Block kept:\n{''.join(sequence_lines)}\n")
                    processed_lines.extend(sequence_lines)
            else:
                log_file.write(f"Block kept (less than 5 lines):\n{''.join(sequence_lines)}\n")
                processed_lines.extend(sequence_lines)

    return processed_lines

def process_folder(input_folder, output_folder, log_folder):
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(log_folder, exist_ok=True)

    processed_files = []  # List to store processed file names

    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)
            log_file_path = os.path.join(log_folder, f"{os.path.splitext(filename)[0]}.log")

            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                processed_lines = process_file(input_file_path, log_file)

            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.writelines(processed_lines)

            processed_files.append(filename)  # Add the file name to the list

    # Print summary after processing all files
    if processed_files:
        print(f"{len(processed_files)} files have been processed: {', '.join(processed_files)}")

if __name__ == "__main__":
    process_folder(INPUT_FOLDER, OUTPUT_FOLDER, LOG_FOLDER)
