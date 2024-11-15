import os
import re
import shutil
import logging

# Define paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '02')
OUTPUT_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '03')
LOG_FOLDER = os.path.join(ROOT_DIR, 'Output', 'Filters_03', '03_logs')  # Log folder

# Create log folder if it doesn't exist
os.makedirs(LOG_FOLDER, exist_ok=True)

# Regular expressions
chapter_part_pattern = re.compile(
    r'^(Chapter|Part)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|[IVXLCDM]+)[\s\-\.:]?',
    re.IGNORECASE
)
page_number_pattern = re.compile(r'.*\s+(\d+|[IVXLCDM]+|\d+-\d+)$', re.IGNORECASE)
line_start_pattern = re.compile(r'^(\d+(\.\d+)*|[IVXLCDM]+\.?)', re.IGNORECASE)

def process_text_file(file_path, log_file_path):
    # Configure logging for this file
    logger = logging.getLogger(os.path.basename(file_path))
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    logger.info(f"Starting processing for file: {file_path}")
    logger.info(f"Total lines in file: {len(lines)}\n")

    processed_lines = []
    removal_triggered = False
    idx = 0
    apply_first_condition = len(lines) > 350  # Apply if there are more than 350 lines
    # Initialize separate counters
    non_chapter_lines_count = 0
    non_page_number_lines_count = 0
    page_number_lines_count = 0
    minimum_page_number_lines = 10

    # Log the application of the first condition based on line count
    if apply_first_condition:
        logger.info("First condition will be applied (file has more than 350 lines).")
    else:
        logger.info("First condition will be skipped (file has 350 lines or fewer).")

    # Define keywords and compile the keyword search pattern
    section_keywords = [
        "INTRODUCTION", "ACKNOWLEDGMENTS", "ACKNOWLEDGEMENTS",
        "APPENDIX", "ACKNOWLEDGEMENT",
        "Introduction", "Acknowledgments", "Acknowledgements",
        "Appendix", "Acknowledgement"
    ]
    keyword_pattern = re.compile(r'\b(' + '|'.join(section_keywords) + r')\b')

    while idx < len(lines):
        line = lines[idx].strip()
        logger.info(f"\nProcessing line {idx + 1}: '{line}'")

        line_added = False

        # Apply the first condition (only if more than 350 lines)
        if apply_first_condition:
            logger.info("Applying first condition (chapter/part pattern check).")
            if chapter_part_pattern.match(line):
                logger.info(f"Line {idx + 1}: Matches chapter/part pattern.")
                non_chapter_lines_count = 0  # Reset consecutive non-chapter line count
                processed_lines.append(line + '\n')
                line_added = True
                logger.info(f"Line {idx + 1} added to processed_lines.")
            else:
                if non_chapter_lines_count == 0:
                    non_chapter_start_idx = idx  # Start index for non-chapter lines sequence
                    logger.info(f"Starting new sequence of non-chapter lines at line {idx + 1}.")
                non_chapter_lines_count += 1
                logger.info(f"Line {idx + 1}: Does not match chapter/part pattern.")
                logger.info(f"Consecutive non-chapter lines count: {non_chapter_lines_count}")
                if non_chapter_lines_count >= 15:
                    logger.info("15 consecutive lines without chapter/part indicators detected.")
                    logger.info(f"Triggering removal of lines starting from line {non_chapter_start_idx + 1}.")
                    processed_lines = processed_lines[:non_chapter_start_idx + 1]
                    removal_triggered = True
                    break
        else:
            logger.info("First condition not applied.")

        # Apply the second condition: Check for page numbers at the end
        if page_number_pattern.match(line) and len(line.split()) > 1:
            page_number_lines_count += 1
            non_page_number_lines_count = 0  # Reset consecutive non-page-number line count
            logger.info(f"Line {idx + 1}: Ends with page number.")
            logger.info(f"Total page-numbered lines so far: {page_number_lines_count}")
            if not line_added:
                processed_lines.append(line + '\n')
                line_added = True
                logger.info(f"Line {idx + 1} added to processed_lines.")
        else:
            if non_page_number_lines_count == 0:
                non_page_number_start_idx = idx
                logger.info(f"Starting new sequence of non-page-numbered lines at line {idx + 1}.")
            non_page_number_lines_count += 1
            logger.info(f"Consecutive non-page-number lines count: {non_page_number_lines_count}")

            if non_page_number_lines_count >= 5 and page_number_lines_count >= minimum_page_number_lines:
                logger.info("5 consecutive lines without page numbers detected after minimum page-numbered lines met.")
                logger.info(f"Triggering removal of lines starting from line {non_page_number_start_idx}.")
                processed_lines = processed_lines[:non_page_number_start_idx]
                removal_triggered = True
                break
            else:
                logger.info(f"Line {idx + 1} not added to processed_lines at this point.")

        # Apply the third condition only after the first 15 lines
        if idx >= 15:
            logger.info("Applying third condition (keyword detection).")
            keyword_match = keyword_pattern.search(line)
            if keyword_match:
                keyword_found = keyword_match.group()
                logger.info(f"Keyword '{keyword_found}' found at line {idx + 1}.")

                # Add the current line with the keyword
                if not line_added:
                    processed_lines.append(line + '\n')
                    line_added = True

                # Look ahead for next 5 lines
                check_idx = idx + 1
                temp_lines = []
                consecutive_no_keyword = 0

                while check_idx < len(lines) and consecutive_no_keyword < 5:
                    next_line = lines[check_idx].strip()
                    logger.info(f"Checking line {check_idx + 1} after '{keyword_found}': '{next_line}'")

                    next_keyword_match = keyword_pattern.search(next_line)
                    if next_keyword_match:
                        # Found another keyword, add all accumulated lines
                        temp_lines.append(next_line + '\n')
                        consecutive_no_keyword = 0
                        logger.info(f"Found new keyword '{next_keyword_match.group()}' at line {check_idx + 1}")
                    else:
                        temp_lines.append(next_line + '\n')
                        consecutive_no_keyword += 1
                        logger.info(f"No keyword found. Consecutive lines without keyword: {consecutive_no_keyword}")

                    check_idx += 1

                # Handle both cases: reached 5 consecutive lines or hit end of file
                if consecutive_no_keyword == 5:
                    logger.info(f"5 consecutive lines without keywords after '{keyword_found}'.")
                    # Remove the last 5 lines (non-keyword lines)
                    processed_lines.extend(temp_lines[:-5])
                    logger.info(f"Removing content starting from line {check_idx - 4}.")
                    removal_triggered = True
                    break
                elif check_idx >= len(lines):
                    logger.info(f"Reached end of file while checking consecutive lines after '{keyword_found}'.")
                    # If we didn't complete 5 lines but reached end of file, remove all accumulated non-keyword lines
                    if consecutive_no_keyword > 0:
                        last_keyword_idx = len(temp_lines) - consecutive_no_keyword
                        processed_lines.extend(temp_lines[:last_keyword_idx])
                        logger.info(f"Removing last {consecutive_no_keyword} lines as they are non-keyword lines at file end.")
                    removal_triggered = True
                    break
                else:
                    # Add all accumulated lines if we didn't reach 5 consecutive non-keyword lines
                    processed_lines.extend(temp_lines)
                    idx = check_idx - 1
            elif not line_added:
                processed_lines.append(line + '\n')
                line_added = True
                logger.info(f"Line {idx + 1} added to processed_lines.")
        else:
            # Before the 15th line, simply add the line without keyword checks
            if not line_added:
                processed_lines.append(line + '\n')
                line_added = True
                logger.info(f"Line {idx + 1} added to processed_lines (within first 15 lines).")

        idx += 1

    # Log final processing outcome
    if removal_triggered:
        logger.info("\nProcessing stopped due to unmet conditions. Remaining lines excluded.")
    else:
        logger.info("\nAll conditions applied successfully. Final processed lines ready.")

    # Close logging handler
    logger.removeHandler(handler)
    handler.close()

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

            # Copy the file to output folder, regardless of processing
            shutil.copy2(input_file_path, output_file_path)

            # Process the file and write output
            processed_content = process_text_file(input_file_path, log_file_path)
            if processed_content:
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(processed_content)
                processed_files.append(filename)

    # Final summary log
    if processed_files:
        print(f"{len(processed_files)} files have been processed and saved in {output_folder}.")
        print(f"Logs are available in {log_folder}")
    else:
        print(f"All files copied to {output_folder}. No files required processing.")

if __name__ == "__main__":
    process_folder(INPUT_FOLDER, OUTPUT_FOLDER, LOG_FOLDER)