import fitz  # PyMuPDF
import os
import re

def extract_pdf_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    doc.close()
    return toc

def write_toc_to_file(toc, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for level, title, page_number in toc:
            indent = '    ' * (level - 1)
            formatted_line = f"{indent}{title}{'.' * (80 - len(indent + title) - len(str(page_number)))}{page_number}"
            f.write(formatted_line + '\n')

def extract_printed_page_number(text):
    """
    Extract the printed page number from the given text.
    This function looks for the first numeric value in the text.
    """
    numbers = re.findall(r'\b\d+\b', text)
    if numbers:
        return int(numbers[0])
    return None

def calculate_offset(pdf_path, header_height=70, footer_height=50):
    """
    Calculate the most common offset for the printed page numbers in the given PDF file.
    """
    doc = fitz.open(pdf_path)
    offsets = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        rect = page.rect
        
        # Define the header and footer rectangles
        header_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + header_height)
        footer_rect = fitz.Rect(rect.x0, rect.y1 - footer_height, rect.x1, rect.y1)

        # Extract text from the header and footer
        header_text = page.get_text("text", clip=header_rect)
        footer_text = page.get_text("text", clip=footer_rect)

        # Try to extract the printed page number from the header or footer
        header_number = extract_printed_page_number(header_text)
        footer_number = extract_printed_page_number(footer_text)

        # Determine which number to use
        printed_page_number = header_number if header_number is not None else footer_number

        if printed_page_number is not None:
            # Calculate offset: printed page number - actual PDF page number (1-based)
            offset = printed_page_number - (page_num + 1)
            offsets.append(offset)

    doc.close()

    if offsets:
        most_common_offset = max(set(offsets), key=offsets.count)
        return abs(most_common_offset)  # Convert to positive
    else:
        return None

def process_pdfs(data_folder, output_folder, header_height, footer_height, remove_negative_pages=False, callback=None):
    """
    Process all PDFs in the data folder, adjust TOC page numbers, and save to output folder.
    Parameters:
    - data_folder: Folder containing PDF files
    - output_folder: Folder where TOC files will be saved
    - remove_negative_pages: Boolean indicating whether to remove TOC entries with negative page numbers
    - header_height: Height of the header area to extract text from (default is 70 points)
    - footer_height: Height of the footer area to extract text from (default is 50 points)
    - callback: Optional function to call with the PDF filename, TOC status, and offset ("N/A" or "No TOC" or offset value)
    """
    os.makedirs(output_folder, exist_ok=True)

    print("=" * 60)
    print("| {:<5} | {:<40} | {:<8} |".format("Index", "Filename", "Offset"))
    print("=" * 60)

    index = 1

    for filename in os.listdir(data_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(data_folder, filename)
            output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
            
            toc = extract_pdf_toc(pdf_path)
            if toc:
                offset = calculate_offset(pdf_path, header_height, footer_height)
                if offset is not None:
                    adjusted_toc = []
                    for level, title, page_number in toc:
                        adjusted_page_number = page_number - offset
                        if remove_negative_pages and adjusted_page_number < 0:
                            continue
                        adjusted_toc.append((level, title, adjusted_page_number))
                    
                    write_toc_to_file(adjusted_toc, output_file)
                    print("| {:<5} | {:<40} | {:<8} |".format(index, filename, offset))

                    # Callback for non-zero offset
                    if callback:
                        callback(filename, "TOC found", offset)

                else:
                    write_toc_to_file(toc, output_file)
                    print("| {:<5} | {:<40} | {:<8} |".format(index, filename, 0))

                    # Callback for zero offset
                    if callback:
                        callback(filename, "TOC found", 0)
            else:
                print("| {:<5} | {:<40} | {:<8} |".format(index, filename, "No TOC"))
                if callback:
                    callback(filename, "No TOC", 0)

            index += 1

    print("=" * 60)

# Example usage
if __name__ == "__main__":
    data_folder = "./data"  # Folder containing PDF files
    output_folder = "./output/01"  # Folder where TOC files will be saved
    process_pdfs(data_folder, output_folder, header_height=70, footer_height=50,remove_negative_pages=True)