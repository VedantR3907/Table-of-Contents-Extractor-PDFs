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
        r'^\s*[\u2022\-\u2013\u2014]\s',
        r'^\s*\([a-zA-Z0-9]+\)',
        r'^\s*[a-zA-Z]\)',
        r'^\s*(Chapter|Part|Act)\s+\d+.*',
        r'^\s*(Chapter|Part|Act)\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|I|II|III|IV|V|VI|VII|VIII|IX|X).*',
    ]
    for pattern in numbering_patterns:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    return False

def has_ending_number_or_range(line):
    """
    Check if the line ends with a number or a number range (e.g., "3-7").
    Exclude lines that resemble addresses by ensuring the number isn't part of a postal code or similar.
    """
    match = re.search(r'\b\d+(-\d+)?$', line)
    if match:
        if re.search(r'\b\d{3}\s*\d{3}$', line):
            return False
        return True
    return False

def contains_dots_sequence(line):
    """Check if the line contains multiple dots in a row (e.g., '.....')."""
    return bool(re.search(r'\.{5,}', line))

def is_only_symbols(line):
    """
    Check if the line contains only symbols.
    Symbols are defined as characters that are neither alphanumeric nor whitespace.
    """
    return bool(re.match(r'^[^\w\s]+$', line))

def is_only_decimal_numbers(line):
    """
    Check if the line contains only decimal numbers or decimal numbers separated by spaces.
    Examples:
        - "2015-16 2016-17 2017-18 2018-19 2019-20"
        - "62.7"
        - "05.11"
        - "96.51 82.71"
        - "27.21"
    """
    return bool(re.match(r'^(\d+\.\d+|\d+-\d+)(\s+(\d+\.\d+|\d+-\d+))*$', line))

def contains_reset_keyword(line):
    """
    Check if the line contains any of the specified keywords that should reset the counter.
    Keywords: Index, Acknowledgements, Acknowledgement, Introduction, Appendix
    """
    reset_keywords = ['Index', 'Acknowledgements', 'Acknowledgement', 'Introduction', 'Appendix', 'Conclusion', 'Conclusions']
    pattern = r'\b(' + '|'.join(reset_keywords) + r')\b'
    return bool(re.search(pattern, line, re.IGNORECASE))

def process_file(file_path, log_file):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:1000]

    processed_lines = []
    i = 0
    consecutive_dotted_lines = 0
    toc_found = False  # Flag to indicate if TOC phrase is found
    skip_lines_after_toc = 0

    while i < len(lines):
        original_line = lines[i].strip()
        line = re.sub(r'[\u25CB\s]+', ' ', original_line)

        # Check for TOC phrase
        if not toc_found and re.search(r'\b(Table of Contents|Contents)\b', line, re.IGNORECASE):
            log_file.write(f"TOC phrase found at line {i+1}: {line}\n")
            toc_found = True
            skip_lines_after_toc = 5
            processed_lines.append(line + '\n')  # Add TOC line to output
            i += 1
            continue

        # Skip lines after the TOC phrase
        if skip_lines_after_toc > 0:
            log_file.write(f"Skipping line {i+1} after TOC (counter not applied): {line}\n")
            processed_lines.append(line + '\n')  # Add skipped lines to output
            skip_lines_after_toc -= 1
            i += 1
            continue

        # Skip lines that are only symbols or only decimal numbers
        if is_only_symbols(line):
            log_file.write(f"Skipped line (only symbols): {line}\n")
            i += 1
            continue
        if is_only_decimal_numbers(line):
            log_file.write(f"Skipped line (only decimal numbers): {line}\n")
            i += 1
            continue

        if contains_dots_sequence(line):
            consecutive_dotted_lines += 1
        else:
            consecutive_dotted_lines = 0

        if consecutive_dotted_lines >= 5:
            log_file.write(f"Consecutive lines with dots detected starting from line {i - 4}.\n")

            while i < len(lines):
                dotted_line = re.sub(r'[\u25CB\s]+', ' ', lines[i].strip())
                if not contains_dots_sequence(dotted_line):
                    log_file.write(f"Non-dotted line encountered below dotted lines: {dotted_line}\n")
                else:
                    processed_lines.append(dotted_line + '\n')
                i += 1
            consecutive_dotted_lines = 0
            continue

        # **New condition: Check for reset keywords**
        if contains_reset_keyword(line):
            log_file.write(f"Reset keyword found at line {i+1}: {line}\n")
            processed_lines.append(line + '\n')
            i += 1
            continue

        if has_ending_number_or_range(line) or is_numbering(line):
            processed_lines.append(line + '\n')
            i += 1
            continue

        non_numbering_counter = 0
        sequence_lines = []
        log_file.write(f"Starting counter at line {i+1}: {line} -------> counter {non_numbering_counter}\n")

        while i < len(lines):
            current_line_original = lines[i].strip()
            current_line = re.sub(r'[\u25CB\s]+', ' ', current_line_original)

            # **Check for reset keywords within sequence**
            if contains_reset_keyword(current_line):
                log_file.write(f"Reset keyword found within sequence at line {i+1}: {current_line}\n")
                processed_lines.append(current_line + '\n')
                i += 1
                break

            if is_numbering(current_line) or has_ending_number_or_range(current_line):
                break

            if is_only_symbols(current_line):
                log_file.write(f"Skipped line within sequence (only symbols): {current_line}\n")
                i += 1
                continue
            if is_only_decimal_numbers(current_line):
                log_file.write(f"Skipped line within sequence (only decimal numbers): {current_line}\n")
                i += 1
                continue

            sequence_lines.append(current_line + '\n')
            non_numbering_counter += 1
            log_file.write(f"Continuing counter at line {i+1}: {current_line} -------> counter {non_numbering_counter}\n")
            i += 1

        if non_numbering_counter >= 5:
            total_words = sum(len(re.findall(r'\w+', l)) for l in sequence_lines)  # noqa: E741
            average_words = total_words / non_numbering_counter
            log_file.write(f"Non-numbered block identified (Average words: {average_words}):\n{''.join(sequence_lines)}\n")

            if average_words < 6.8 and non_numbering_counter >= 50:
                log_file.write("Block removed due to line count >= 50 with low average words.\n")
                continue
            elif average_words > 6.8:
                log_file.write("Block removed due to high average words.\n")
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

    processed_files = []

    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)
            log_file_path = os.path.join(log_folder, f"{os.path.splitext(filename)[0]}.log")

            with open(log_file_path, 'w', encoding='utf-8') as log_file:
                processed_lines = process_file(input_file_path, log_file)

            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.writelines(processed_lines)

            processed_files.append(filename)

    if processed_files:
        print(f"{len(processed_files)} files have been processed: {', '.join(processed_files)}")

if __name__ == "__main__":
    process_folder(INPUT_FOLDER, OUTPUT_FOLDER, LOG_FOLDER)
