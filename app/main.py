import os
import shutil
import glob
from Fitz_TOC_Extractor_1 import process_pdfs as process_manual_toc
# from custom_function_to_extract_pdf_2 import process_pdfs_in_directory as process_custom_toc
from Custom_TOC_Extractor_2 import process_txt_files_in_directory, extract_text_pages
# from custom_function_to_extract_pdf_21 import process_txt_files_in_directory, extract_text_pages
from Filtering_Structuring_3 import filtering_main_3

def extract_text_from_failed_pdfs(failed_pdfs_folder, extracted_output_folder):
    os.makedirs(extracted_output_folder, exist_ok=True)
    
    pdf_files = glob.glob(os.path.join(failed_pdfs_folder, '*.pdf'))

    print("\n", "#"*70)
    print("\n**** Extracting text from failed PDFs ****")
    
    for pdf_file in pdf_files:
        filename = os.path.splitext(os.path.basename(pdf_file))[0]
        text_output_path = os.path.join(extracted_output_folder, f'{filename}.txt')
        
        # Extract the text content from the failed PDFs using your existing PDF-to-text extraction logic
        text_pages = extract_text_pages(pdf_file)
        with open(text_output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(text_pages))  # Save extracted content to text file
        
        print(f"Extracted content from {pdf_file} and saved to {text_output_path}")
    
    print("#" * 100)

def create_final_output(output_folder):
    # Define folder paths
    folder_03 = os.path.join(output_folder, 'Filters_03', '03')
    folder_02 = os.path.join(output_folder, '02')
    folder_01 = os.path.join(output_folder, '01')
    final_output_folder = os.path.join(output_folder, 'Final_Output')

    # Create the final output folder if it doesn't exist
    os.makedirs(final_output_folder, exist_ok=True)

    # Track the files already copied
    copied_files = set()

    # Step 1: Copy all files from folder_03
    for file_name in os.listdir(folder_03):
        src_file = os.path.join(folder_03, file_name)
        dest_file = os.path.join(final_output_folder, file_name)
        shutil.copy2(src_file, dest_file)
        copied_files.add(file_name)

    # Step 2: Copy only files from folder_02 not in folder_03
    for file_name in os.listdir(folder_02):
        if file_name not in copied_files:
            src_file = os.path.join(folder_02, file_name)
            dest_file = os.path.join(final_output_folder, file_name)
            shutil.copy2(src_file, dest_file)
            copied_files.add(file_name)

    # Step 3: Copy only files from folder_01 not in folder_02 or folder_03
    for file_name in os.listdir(folder_01):
        if file_name not in copied_files:
            src_file = os.path.join(folder_01, file_name)
            dest_file = os.path.join(final_output_folder, file_name)
            shutil.copy2(src_file, dest_file)

    print("Files have been successfully organized in the Final_Output folder.")

# Main process function that orchestrates everything
def final_process_pdfs(data_folder, output_folder, header_height=70, footer_height=50, remove_negative_pages=False):
    """
    Process all PDFs, first trying the manual TOC extraction method.
    If the TOC extraction fails (No TOC, or N/A), or the TOC offset is zero, or the TOC has <=30 lines, 
    the second custom extraction method is applied.
    Parameters:
    - data_folder: Folder containing the PDF files.
    - output_folder: Folder where the TOC files will be saved.
    - remove_negative_pages: Boolean to remove TOC entries with negative page numbers.
    - header_height: Height of the header to extract text from.
    - footer_height: Height of the footer to extract text from.
    """
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Output folder for manual TOC extractor (renamed to 01)
    manual_output_folder = os.path.join(output_folder, "01")
    os.makedirs(manual_output_folder, exist_ok=True)

    # Temporary folder for PDFs with failed TOC extraction (renamed to 02)
    failed_pdfs_folder = os.path.join(output_folder, "02")
    os.makedirs(failed_pdfs_folder, exist_ok=True)

    # Folder for extracted text files from failed PDFs
    extracted_output_folder = os.path.join(output_folder, "extracted_content")
    os.makedirs(extracted_output_folder, exist_ok=True)

    # Use a set to avoid duplicates
    failed_pdfs = set()

    def manual_toc_callback(pdf_name, toc_status, offset=0):
        """Callback function to track failed TOC extraction results and zero offset cases."""
        if toc_status in ["N/A", "No TOC"]:
            failed_pdfs.add(pdf_name)

    print("Processing PDFs with the manual TOC extractor...")
    
    # Run the manual TOC extractor and track failed PDFs
    process_manual_toc(data_folder, manual_output_folder, header_height, footer_height, remove_negative_pages, callback=manual_toc_callback)

    # New Condition 4: Check TOC text files for line count <=30
    toc_text_files = glob.glob(os.path.join(manual_output_folder, '*.txt'))
    for toc_file in toc_text_files:
        try:
            with open(toc_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            line_count = len(lines)
            if line_count <= 30:
                # Extract the corresponding PDF filename
                pdf_filename = os.path.splitext(os.path.basename(toc_file))[0] + '.pdf'
                if pdf_filename not in failed_pdfs:
                    failed_pdfs.add(pdf_filename)
                    print(f"\nAdded '{pdf_filename}' to failed PDFs due to TOC line count <= 30.")
        except Exception as e:
            print(f"Error reading '{toc_file}': {e}")
            # Optionally, add to failed_pdfs if TOC file can't be read
            pdf_filename = os.path.splitext(os.path.basename(toc_file))[0] + '.pdf'
            failed_pdfs.add(pdf_filename)
    
    second_script_ran = False
    if failed_pdfs:
        print(f"Found {len(failed_pdfs)} PDFs requiring custom processing based on TOC extraction failures or line count condition.")

        # Copy failed PDFs to the folder for custom processing (don't remove from data folder)
        for failed_pdf in failed_pdfs:
            original_pdf_path = os.path.join(data_folder, failed_pdf)
            if os.path.exists(original_pdf_path):
                failed_pdf_copy_path = os.path.join(failed_pdfs_folder, failed_pdf)
                shutil.copy2(original_pdf_path, failed_pdf_copy_path)
            else:
                print(f"Warning: '{failed_pdf}' not found in '{data_folder}'.")

        # Step 1: Extract content from the failed PDFs and save as text files
        extract_text_from_failed_pdfs(failed_pdfs_folder, extracted_output_folder)

        # Step 2: Process the extracted text files to generate TOC and save to the 02 folder
        process_txt_files_in_directory(extracted_output_folder)
        second_script_ran = True

        # Cleanup: delete only the PDF files from the 02 folder
        pdf_files_in_failed_folder = glob.glob(os.path.join(failed_pdfs_folder, '*.pdf'))
        for pdf_file in pdf_files_in_failed_folder:
            try:
                os.remove(pdf_file)
            except Exception as e:
                print(f"Error deleting '{pdf_file}': {e}")
    else:
        print("All PDFs processed successfully with the manual TOC extractor.")
    
    if second_script_ran:
        print("\nRunning the Filtering_Structuring_3 script...")
        filtering_main_3()
    
    create_final_output(output_folder)
    print("Final output creation is complete.")

# Example usage
if __name__ == "__main__":
    data_folder = "./data"  # Folder containing PDF files
    output_folder = "./output"  # Folder where TOC files will be saved
    final_process_pdfs(data_folder, output_folder, header_height=70, footer_height=50, remove_negative_pages=True)