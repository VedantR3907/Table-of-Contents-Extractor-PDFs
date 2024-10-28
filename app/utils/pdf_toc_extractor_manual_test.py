import fitz  # PyMuPDF
import os

def extract_pdf_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    doc.close()
    return toc

def write_toc_to_file(toc, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for level, title, page_number in toc:
            # Create indentation based on the level
            indent = '    ' * (level - 1)
            # Format the line with title and page number aligned
            formatted_line = f"{indent}{title}{'.' * (80 - len(indent + title) - len(str(page_number)))}{page_number}"
            f.write(formatted_line + '\n')

def process_pdfs(data_folder, output_folder):
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Iterate over all PDF files in the data folder
    for filename in os.listdir(data_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(data_folder, filename)
            output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
            
            toc = extract_pdf_toc(pdf_path)
            if toc:
                write_toc_to_file(toc, output_file)
                print(f"TOC for '{filename}' saved to '{output_file}'.")
            else:
                print(f"No TOC found for '{filename}'.")

# Example usage
data_folder = "./app/data"  # Folder containing PDF files
output_folder = "./app/output/TOC"  # Folder where TOC files will be saved
process_pdfs(data_folder, output_folder)


# Specify the path to your PDF file
pdf_path = "./app/data/thinkpython2.pdf"
# Specify the path for the output text file
output_path = "header_footer_texts.txt"

# Open the PDF document
doc = fitz.open(pdf_path)

# Define the header and footer heights in points (72 points = 1 inch)
header_height = 50  # Adjust this value as needed
footer_height = 50  # Adjust this value as needed

# Open the output file in write mode
with open(output_path, "w", encoding="utf-8") as output_file:
    # Loop through each page in the document
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Get the page dimensions
        rect = page.rect
        # Define the header rectangle (top area of the page)
        header_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + header_height)
        # Define the footer rectangle (bottom area of the page)
        footer_rect = fitz.Rect(rect.x0, rect.y1 - footer_height, rect.x1, rect.y1)
        # Extract text from the header rectangle
        header_text = page.get_text("text", clip=header_rect)
        # Extract text from the footer rectangle
        footer_text = page.get_text("text", clip=footer_rect)
        # Write the extracted header and footer text to the file
        output_file.write(f"Page {page_num + 1} header text:\n")
        output_file.write(header_text.strip() + "\n")
        output_file.write("-" * 40 + "\n")
        output_file.write(f"Page {page_num + 1} footer text:\n")
        output_file.write(footer_text.strip() + "\n")
        output_file.write("=" * 40 + "\n")

# Close the document
doc.close()

