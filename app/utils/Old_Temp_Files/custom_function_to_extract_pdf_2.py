import pdfplumber
import re
from PyPDF2 import PdfReader  # noqa: F401
import os
import glob

def group_words_into_lines(words):
    # Sort words by their vertical (top) position first, then by horizontal (x0) position
    words = sorted(words, key=lambda w: (w['top'], w['x0']))

    lines = []
    current_line = []
    last_top = None
    last_x1 = None  # Track the rightmost position of the previous word (x1)

    for word in words:
        word_top = word['top']
        word_x0 = word['x0']  # Left boundary of the word
        word_text = word['text']

        # If it's a new line (significant change in Y-coordinate), start a new line
        if last_top is not None and abs(word_top - last_top) > 5:
            # Join words in the current line into a string and add to lines
            lines.append(' '.join([w['text'] for w in current_line]))
            current_line = []
            last_x1 = None  # Reset last_x1 for the new line

        # If this word is very close to the previous word horizontally, merge them without space
        if last_x1 is not None and abs(word_x0 - last_x1) < 2:  # Only merge if the words are VERY close
            current_line[-1]['text'] += word_text
        else:
            # Otherwise, add the word as a new entry in the current line with a space between words
            current_line.append(word)

        # Update the tracking variables
        last_top = word_top
        last_x1 = word['x1']  # Right boundary of the word

    # Append the last line if there are remaining words
    if current_line:
        lines.append(' '.join([w['text'] for w in current_line]))

    return lines

# Function to extract text from each page of the PDF
def extract_text_pages(pdf_path):
    text_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract words instead of full lines to avoid broken words across lines
            words = page.extract_words()
            
            # Manually combine words into lines based on their positions
            lines = group_words_into_lines(words)
            
            # Join the lines back into text, simulating the page text
            text = '\n'.join(lines)
            text_pages.append(text)
    return text_pages




# Function to parse TOC line using regular expressions
def parse_toc_line(line, next_line=None):
    toc_patterns = [
        r'^\s*(?P<numbering>[IVXLC]+\.*|\d+\.\d*|\d+)\s+(?P<heading>.*?)\s+\.{2,}\s+(?P<page>\d+)$',
        r'^\s*(?P<numbering>[IVXLC]+\.*|\d+\.\d*|\d+)\s+(?P<heading>.*?)\s+(?P<page>\d+)$',
        r'^\s*(?P<numbering>[IVXLC]+\.*|\d+\.\d*|\d+)\s+(?P<heading>.*)$',
        r'^\s*(?P<heading>.*?)\s+\.{2,}\s+(?P<page>\d+)$',
        r'^\s*(?P<heading>.*?)\s+(?P<page>\d+)$',
        r'^\s*(?P<heading>.+?)\s*\.{2,}\s*(?P<page>\d+)\s*(Chapter\s+\d+)?$',
        r'^\s*(?P<heading>.+?)\s*(?P<page>\d+)\s*$',
        r'^\s*(?P<chapter>Chapter\s+\d+)\s*\.{2,}\s*(?P<page>\d+)$',
        r'^\s*(PART\s+\d+:\s+)?(?P<heading>.+?)(\.{2,}|\s+)(?P<page>\d+)$',
        r'^\s*(?P<numbering>\d+|\d+\.\d+|PART \d+)\s+(?P<heading>.+?)(\.{2,}|\s+)(?P<page>\d+)$',
        r'^\s*(?P<heading>.+?)\s+(\.{2,})\s*(?P<page>\d+)$',
    ]

    for pattern in toc_patterns:
        match = re.match(pattern, line)
        if match:
            numbering = match.groupdict().get('numbering', '').strip()
            heading = match.group('heading').strip()
            page = match.groupdict().get('page')
            full_heading = f"{numbering} {heading}".strip() if numbering else heading
            entry = {'heading': full_heading}
            if page:
                entry['page_number'] = int(page)
            else:
                entry['page_number'] = None
            return entry

    if next_line:
        combined_line = line + ' ' + next_line.strip()
        for pattern in toc_patterns:
            match = re.match(pattern, combined_line)
            if match:
                numbering = match.groupdict().get('numbering', '').strip()
                heading = match.group('heading').strip()
                page = match.groupdict().get('page')
                full_heading = f"{numbering} {heading}".strip() if numbering else heading
                entry = {'heading': full_heading}
                if page:
                    entry['page_number'] = int(page)
                else:
                    entry['page_number'] = None
                return entry

    return None

# Extract TOC entries from the PDF
def extract_toc_entries(text_content):
    toc_phrases = ["Table of Contents", "Contents", "Index", "CONTENTS"]
    toc_start_index = None
    for phrase in toc_phrases:
        toc_start_index = text_content.find(phrase)
        if toc_start_index != -1:
            break

    if toc_start_index == -1:
        return []

    toc_text = text_content[toc_start_index:]
    lines = toc_text.split('\n')

    toc_entries = []
    toc_started = False
    non_match_count = 0
    max_non_match = 5
    last_page_number = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        next_line = lines[i+1].strip() if i+1 < len(lines) else None

        if not toc_started:
            if any(phrase in line for phrase in toc_phrases):
                toc_started = True
            i += 1
            continue

        if not line:
            i += 1
            continue

        entry = parse_toc_line(line, next_line)
        if entry:
            if entry['page_number'] is None:
                entry['page_number'] = last_page_number
            else:
                last_page_number = entry['page_number']
            toc_entries.append(entry)
            non_match_count = 0
            i += 1
            if next_line and entry['heading'].endswith(next_line.strip()):
                i += 1
        else:
            non_match_count += 1
            if non_match_count >= max_non_match:
                break
            i += 1

    return toc_entries

# Extract bookmarks from the PDF (if available)
def extract_bookmarks(pdf_path):
    reader = PdfReader(pdf_path)
    bookmarks = []

    def recurse_outline(outline, parent_title=''):
        for item in outline:
            if isinstance(item, list):
                recurse_outline(item, parent_title)
            else:
                title = (parent_title + ' ' + item.title).strip()
                page_number = reader.get_destination_page_number(item) + 1
                bookmarks.append({'heading': title, 'page_number': page_number})
    
    try:
        recurse_outline(reader.outline)
    except AttributeError:
        pass
    return bookmarks

# Extract headings based on patterns in the text
def extract_headings_from_text(text_pages):
    headings = []
    heading_patterns = [
        r'^\s*CHAPTER\s+\d+.*',
        r'^\s*Chapter\s+\d+.*',
        r'^\s*Section\s+\d+.*',
        r'^\s*Appendix\s+[A-Z].*',
        r'^\s*[IVXLC]+\.\s+.*',
    ]
    combined_pattern = re.compile('|'.join(heading_patterns), re.IGNORECASE)

    for page_num, text in enumerate(text_pages, start=1):
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if combined_pattern.match(line):
                headings.append({'heading': line.strip(), 'page_number': page_num})
    return headings

# Main function to extract TOC and text from PDFs
def extract_pdf_toc(pdf_path):
    text_pages = extract_text_pages(pdf_path)
    toc_entries = extract_toc_entries(text_pages)
    if not toc_entries:
        toc_entries = extract_headings_from_text(text_pages)

    # bookmarks = extract_bookmarks(pdf_path)
    # if bookmarks:
    #     toc_entries.extend(bookmarks)

    unique_entries = {(entry['heading'], entry['page_number']): entry for entry in toc_entries}
    toc_entries = list(unique_entries.values())
    toc_entries.sort(key=lambda x: (x['page_number'] or 0, x['heading']))

    return toc_entries, text_pages

# Process all PDFs in the directory and save TOC and content
def process_txt_files_in_directory(directory):
    output_dir_toc = './output/02'  # Save TOC in 02 folder
    os.makedirs(output_dir_toc, exist_ok=True)

    txt_files = glob.glob(os.path.join(directory, '*.txt'))

    for txt_file in txt_files:
        filename = os.path.splitext(os.path.basename(txt_file))[0]

        # Read text content from the saved text file
        with open(txt_file, 'r', encoding='utf-8') as f:
            text_content = f.read()

        # Extract TOC entries from the text content
        toc_entries = extract_toc_entries(text_content)

        # Save the TOC entries
        toc_output_path = os.path.join(output_dir_toc, f'{filename}.txt')
        with open(toc_output_path, 'w', encoding='utf-8') as toc_file:
            for entry in toc_entries:
                page_number = entry['page_number'] if entry['page_number'] is not None else ''
                toc_file.write(f"{entry['heading']} ...... {page_number}\n")

        print(f"Processed {txt_file} - TOC saved.")

if __name__ == "__main__":
    txt_directory = "./output/extracted_content"  # Directory containing text files
    process_txt_files_in_directory(txt_directory)