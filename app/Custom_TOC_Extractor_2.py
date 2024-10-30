import pdfplumber
import re
from PyPDF2 import PdfReader  # noqa: F401
import os
import glob

def extract_text_pages(pdf_path):
    text_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract the full text from each page without processing each word individually
            text = page.extract_text()
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
        line = re.sub(r'[○\s]+', ' ', lines[i].strip())
        next_line = re.sub(r'[○\s]+', ' ', lines[i+1].strip()) if i+1 < len(lines) else None

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
    output_dir_toc = './output/02'
    os.makedirs(output_dir_toc, exist_ok=True)

    txt_files = glob.glob(os.path.join(directory, '*.txt'))

    for txt_file in txt_files:
        filename = os.path.splitext(os.path.basename(txt_file))[0]

        with open(txt_file, 'r', encoding='utf-8') as f:
            text_content = f.read()

        toc_entries = extract_toc_entries(text_content)

        toc_output_path = os.path.join(output_dir_toc, f'{filename}.txt')
        with open(toc_output_path, 'w', encoding='utf-8') as toc_file:
            for entry in toc_entries:
                page_number = entry['page_number'] if entry['page_number'] is not None else ''
                toc_file.write(f"{entry['heading']} ...... {page_number}\n")
        
        print(f"\nProcessed {txt_file} - TOC saved.")
    print("#"*100)

# New function to process custom PDFs directly, without altering the existing file-based workflow
def process_custom_pdfs_directly(pdf_paths, output_base_dir='./output'):
    """
    Process specific PDFs directly for TOC extraction and save both extracted content and TOC results 
    to the same structure as the primary workflow.
    """
    output_dir_toc = os.path.join(output_base_dir, '02')  # TOC output for custom PDFs
    content_dir = os.path.join(output_base_dir, 'extracted_content')  # Extracted content directory

    os.makedirs(output_dir_toc, exist_ok=True)
    os.makedirs(content_dir, exist_ok=True)

    for pdf_path in pdf_paths:
        filename = os.path.splitext(os.path.basename(pdf_path))[0]
        
        print(f"\n**** Processing file: {pdf_path} ****")
        
        # Extract text pages and save the content
        text_pages = extract_text_pages(pdf_path)
        content_output_path = os.path.join(content_dir, f'{filename}.txt')
        with open(content_output_path, 'w', encoding='utf-8') as content_file:
            content_file.write('\n'.join(text_pages))
        print(f"Extracted content from {pdf_path} saved to {content_output_path}")
        
        # Extract TOC entries from the text and save them
        toc_entries = extract_toc_entries('\n'.join(text_pages))
        toc_output_path = os.path.join(output_dir_toc, f'{filename}.txt')
        with open(toc_output_path, 'w', encoding='utf-8') as toc_file:
            for entry in toc_entries:
                page_number = entry['page_number'] if entry['page_number'] is not None else ''
                toc_file.write(f"{entry['heading']} ...... {page_number}\n")
        
        print(f"Processed {pdf_path} - TOC saved to {toc_output_path}")
        print("************************************")


# Example usage of the new custom PDF processing function without affecting the main workflow
if __name__ == "__main__":
    # Uncomment the line below to process custom PDFs directly
    # process_custom_pdfs_directly(["./data/Things That Matter- Three Decades of Passions, Pastimes and Politics ( PDFDrive ).pdf"])

    # Retain the main workflow for processing files from the first code file
    txt_directory = "./output/extracted_content"  # Directory containing text files
    process_txt_files_in_directory(txt_directory)