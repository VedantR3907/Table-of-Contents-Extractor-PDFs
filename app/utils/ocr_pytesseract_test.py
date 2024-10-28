import os
import cv2
import pytesseract
from pdf2image import convert_from_path

# Path to the tesseract executable (if required on your system)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr_pdf_to_text(pdf_path, output_folder, start_page=1, end_page=None):
    """
    Function to perform OCR on a PDF, extracting text from a range of pages.
    
    :param pdf_path: Path to the input PDF file.
    :param output_folder: Folder where the extracted text file will be saved.
    :param start_page: The page to start processing (1-based index).
    :param end_page: The page to stop processing (1-based index).
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Extract PDF name without extension
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # Full path for output text file
    output_file_path = os.path.join(output_folder, f"{pdf_name}.txt")
    
    # Convert specified range of PDF pages to images
    images = convert_from_path(pdf_path, first_page=start_page, last_page=end_page)
    
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for i, image in enumerate(images):
            # Save the current page image as a temporary file (optional)
            temp_image_path = f"temp_page_{start_page + i}.png"
            image.save(temp_image_path, "PNG")
            
            # Read the saved image using OpenCV
            img = cv2.imread(temp_image_path)
            
            # Convert the image to grayscale for better OCR results
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to clean up the image
            _, thresh_img = cv2.threshold(gray_img, 150, 255, cv2.THRESH_BINARY)
            
            # Perform OCR to extract text from the image
            extracted_text = pytesseract.image_to_string(thresh_img, lang='eng')
            
            # Write the text to the output file with the page number headers
            output_file.write(f"PAGE {start_page + i}\n")
            output_file.write(extracted_text.strip())  # Removing extra newlines from the extracted text
            output_file.write("\n*********************************************\n")
            
            # Optionally, clean up the temporary image file
            os.remove(temp_image_path)

    print(f"OCR complete! Text extracted and saved to {output_file_path}")

# Example usage
pdf_file_path = '../data/robert-kiyosaki-the-real-book-of-real-estate.pdf'
output_directory = '../output'
ocr_pdf_to_text(pdf_file_path, output_directory, start_page=2, end_page=9)  # Process from page 2 to 5
