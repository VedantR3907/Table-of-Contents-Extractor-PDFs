import pdfplumber
import re
# from PyPDF2 import PdfReader  # noqa: F401
import os
import queue
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console
import glob

def extract_text_from_pdf(pdf_file, extracted_output_folder, progress_queue):
    try:
        filename = os.path.splitext(os.path.basename(pdf_file))[0]
        text_output_path = os.path.join(extracted_output_folder, f'{filename}.txt')
        
        # Initialize variables for progress tracking
        progress_queue.put(('start', filename))
        
        text_chunks = []
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            
            # Process pages in batches for better performance
            batch_size = 5  # Adjust batch size based on your needs
            for batch_start in range(0, total_pages, batch_size):
                batch_end = min(batch_start + batch_size, total_pages)
                batch_pages = pdf.pages[batch_start:batch_end]
                
                # Process batch of pages
                batch_texts = []
                for page in batch_pages:
                    # Optimize text extraction settings
                    text = page.extract_text(x_tolerance=3, y_tolerance=3)
                    batch_texts.append(text)
                
                text_chunks.extend(batch_texts)
                
                # Report progress
                progress = (batch_end / total_pages) * 100
                progress_queue.put(('progress', filename, progress))
        
        # Write all text at once
        with open(text_output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text_chunks))
        
        progress_queue.put(('complete', filename))
        return True, filename
        
    except Exception as e:
        progress_queue.put(('error', filename, str(e)))
        return False, filename

def progress_monitor(progress_queue, total_pdfs):
    console = Console()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        expand=True,
        console=console
    ) as progress:
        # Initialize progress bars
        tasks = {}
        completed = set()
        errors = set()

        while len(completed) + len(errors) < total_pdfs:
            try:
                msg = progress_queue.get(timeout=1)
                msg_type = msg[0]
                filename = msg[1]

                if msg_type == 'start':
                    tasks[filename] = progress.add_task(f"[cyan]{filename}", total=100)
                elif msg_type == 'progress':
                    progress.update(tasks[filename], completed=msg[2])
                elif msg_type == 'complete':
                    progress.update(tasks[filename], completed=100)
                    completed.add(filename)
                elif msg_type == 'error':
                    progress.update(tasks[filename], description=f"[red]{filename} - Error!")
                    errors.add(filename)
            except queue.Empty:
                continue

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

    lines = lines[:700]

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
# def extract_bookmarks(pdf_path):
#     reader = PdfReader(pdf_path)
#     bookmarks = []

#     def recurse_outline(outline, parent_title=''):
#         for item in outline:
#             if isinstance(item, list):
#                 recurse_outline(item, parent_title)
#             else:
#                 title = (parent_title + ' ' + item.title).strip()
#                 page_number = reader.get_destination_page_number(item) + 1
#                 bookmarks.append({'heading': title, 'page_number': page_number})
    
#     try:
#         recurse_outline(reader.outline)
#     except AttributeError:
#         pass
#     return bookmarks

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
def extract_pdf_toc(pdf_path, extracted_output_folder, progress_queue):
    text_pages = []
    # Call extract_text_from_pdf for text extraction
    success, filename = extract_text_from_pdf(pdf_path, extracted_output_folder, progress_queue)
    
    if success:
        text_output_path = os.path.join(extracted_output_folder, f'{filename}.txt')
        with open(text_output_path, 'r', encoding='utf-8') as f:
            text_pages = f.readlines()
    else:
        print(f"Failed to extract text from {pdf_path}.")
    
    toc_entries = extract_toc_entries('\n'.join(text_pages))
    if not toc_entries:
        toc_entries = extract_headings_from_text(text_pages)

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

        text_content = '\n'.join(text_content.splitlines()[:700])

        toc_entries = extract_toc_entries(text_content)

        toc_output_path = os.path.join(output_dir_toc, f'{filename}.txt')
        with open(toc_output_path, 'w', encoding='utf-8') as toc_file:
            for entry in toc_entries:
                page_number = entry['page_number'] if entry['page_number'] is not None else ''
                toc_file.write(f"{entry['heading']} ...... {page_number}\n")
    print("#"*100)

# New function to process custom PDFs directly, without altering the existing file-based workflow
def process_custom_pdfs_directly(pdf_paths, output_base_dir='./output'):
    """
    Process specific PDFs directly for TOC extraction and save both extracted content and TOC results 
    to the same structure as the primary workflow.
    """
    output_dir_toc = os.path.join(output_base_dir, '02')  # TOC output for custom PDFs
    extracted_output_folder = os.path.join(output_base_dir, 'extracted_content')  # Extracted content directory

    os.makedirs(output_dir_toc, exist_ok=True)
    os.makedirs(extracted_output_folder, exist_ok=True)

    progress_queue = queue.Queue()
    total_pdfs = len(pdf_paths)
    from threading import Thread
    progress_thread = Thread(target=progress_monitor, args=(progress_queue, total_pdfs))
    progress_thread.start()

    for pdf_path in pdf_paths:
        filename = os.path.splitext(os.path.basename(pdf_path))[0]

        # Extract text using the updated extract_text_from_pdf function
        extract_text_from_pdf(pdf_path, extracted_output_folder, progress_queue)

        # Extract TOC entries
        text_output_path = os.path.join(extracted_output_folder, f'{filename}.txt')
        with open(text_output_path, 'r', encoding='utf-8') as content_file:
            text_content = content_file.read()

        toc_entries = extract_toc_entries(text_content)

        # Save the TOC entries
        toc_output_path = os.path.join(output_dir_toc, f'{filename}.txt')
        with open(toc_output_path, 'w', encoding='utf-8') as toc_file:
            for entry in toc_entries:
                page_number = entry['page_number'] if entry['page_number'] is not None else ''
                toc_file.write(f"{entry['heading']} ...... {page_number}\n")

    # Wait for progress monitoring to complete
    progress_thread.join()


# Example usage of the new custom PDF processing function without affecting the main workflow
if __name__ == "__main__":
    # List of specific PDF files to process
    pdf_files = [
        "./data/robert-kiyosaki-the-real-book-of-real-estate.pdf",  # Replace with your PDF file paths
        "./data/Master_ Chess Tactics, Chess Openings, and Chess Strategies.pdf",  # Add more file paths as needed
    ]

    # Base output directory for extracted content and TOC
    output_base_dir = "./output"

    if not pdf_files:
        print("No PDF files provided for processing.")
    else:
        print(f"Processing {len(pdf_files)} specific PDF files...")

        # Call the function to process the custom PDF files
        process_custom_pdfs_directly(pdf_files, output_base_dir)

        print("\nAll specified PDFs processed successfully. Check the output directory for results.")
