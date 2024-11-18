import os
import re
import shutil
import glob
from functools import partial
import threading
import multiprocessing as mp
from rich.console import Console
from rich.panel import Panel
from concurrent.futures import ProcessPoolExecutor, as_completed
from Fitz_TOC_Extractor_1 import process_pdfs as process_manual_toc
# from custom_function_to_extract_pdf_2 import process_pdfs_in_directory as process_custom_toc
from Custom_TOC_Extractor_2 import process_txt_files_in_directory, extract_text_from_pdf, progress_monitor
# from custom_function_to_extract_pdf_21 import process_txt_files_in_directory, extract_text_pages
from Filtering_Structuring_3 import filtering_main_3

console = Console()

def extract_text_from_failed_pdfs(failed_pdfs_folder, extracted_output_folder):
    os.makedirs(extracted_output_folder, exist_ok=True)
    
    # Get list of PDF files
    pdf_files = glob.glob(os.path.join(failed_pdfs_folder, '*.pdf'))
    
    if not pdf_files:
        print("No PDF files found in the specified folder.")
        return
    
    # Create a multiprocessing queue for progress updates
    manager = mp.Manager()
    progress_queue = manager.Queue()
    
    # Start the progress monitor in a separate thread
    total_pdfs = len(pdf_files)
    progress_thread = threading.Thread(
        target=progress_monitor, 
        args=(progress_queue, total_pdfs)
    )
    progress_thread.start()
    
    print("\n", "#"*70)
    print(f"\n**** Extracting text from {total_pdfs} PDFs using {mp.cpu_count()} processes ****\n")
    
    # Process PDFs in parallel using ProcessPoolExecutor
    extract_func = partial(extract_text_from_pdf, 
                         extracted_output_folder=extracted_output_folder,
                         progress_queue=progress_queue)
    
    results = []
    with ProcessPoolExecutor(max_workers=mp.cpu_count()) as executor:
        # Submit all PDF processing jobs
        future_to_pdf = {
            executor.submit(extract_func, pdf_file): pdf_file 
            for pdf_file in pdf_files
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_pdf):
            success, filename = future.result()
            results.append((success, filename))
    
    # Wait for progress monitor to finish
    progress_thread.join()
    
    # Print summary
    successful = sum(1 for success, _ in results if success)
    failed = total_pdfs - successful
    
    print("\n", "#"*70)
    print("\nProcessing Summary:")
    print(f"- Successfully processed: {successful} PDFs")
    print(f"- Failed to process: {failed} PDFs")
    print("#" * 70)

def check_for_numbered_lines(toc_file):
    """Check if there are at least 50 consecutive lines that contain numbers and not words."""
    with open(toc_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    numbered_line_count = 0

    for line in lines:
        line = line.strip()
        
        # Use regex to check if line contains at least one digit and no letters
        if re.search(r'\d', line) and not re.search(r'[a-zA-Z]', line):
            numbered_line_count += 1

            # If we hit 50 numbered lines, return True
            if numbered_line_count >= 50:
                return True
        else:
            numbered_line_count = 0  # Reset if line contains letters or no digits
            
    return False


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

    console.print(Panel("Output has been saved to the Final_output folder.", 
                       style="bold green", 
                       subtitle="Process Complete"))

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
            print ('')
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
            if line_count <= 25:
                # Extract the corresponding PDF filename
                pdf_filename = os.path.splitext(os.path.basename(toc_file))[0] + '.pdf'
                if pdf_filename not in failed_pdfs:
                    failed_pdfs.add(pdf_filename)
                    print(f"\nAdded '{pdf_filename}' to failed PDFs due to TOC line count <= 30.")
            elif check_for_numbered_lines(toc_file):
                pdf_filename = os.path.splitext(os.path.basename(toc_file))[0] + '.pdf'
                if pdf_filename not in failed_pdfs:
                    failed_pdfs.add(pdf_filename)
                    print(f"\nAdded '{pdf_filename}' to failed PDFs due to 50 consecutive numbered lines.")
        except Exception as e:
            print(f"Error reading '{toc_file}': {e}")
            # Optionally, add to failed_pdfs if TOC file can't be read
            pdf_filename = os.path.splitext(os.path.basename(toc_file))[0] + '.pdf'
            failed_pdfs.add(pdf_filename)
    
    second_script_ran = False
    if failed_pdfs:
        print(f"❌Found {len(failed_pdfs)} failed from first method:", ", ".join(failed_pdfs))

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

# Example usage
if __name__ == "__main__":
    data_folder = "./data"  # Folder containing PDF files
    output_folder = "./output"  # Folder where TOC files will be saved
    final_process_pdfs(data_folder, output_folder, header_height=70, footer_height=50, remove_negative_pages=True)