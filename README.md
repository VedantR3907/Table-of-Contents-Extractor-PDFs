![TOC Extractor](app/utils/toc_banner.png)

# TOC Extractor from PDF's

## Overview

The TOC Extractor is a Python-based tool that extracts the Table of Contents (TOC) from PDF files without relying on machine learning (ML), deep learning (DL), or large language models (LLMs). It uses logical Python code and regex patterns for extraction.

For a detailed explanation of how the tool works, refer to the [blog post](https://medium.com/@vedantrajpurohit3907/the-toc-extractor-from-pdfs-b42a3df8236a).

---

## Installation Guide

### Branches Overview

The repository has two branches for different use cases:

- **`main` branch**: Contains the core code along with sample PDFs for testing, covering various domains like IT, Finance, and Storybooks.
- **`TOC_Extactor_without_testing_PDFs` branch**: Contains only the core code without sample PDFs, intended for testing with custom PDFs.

### Clone the Repository

Use the following commands to clone the desired branch:

#### Main Branch (with sample PDFs)
```bash
git clone https://github.com/VedantR3907/Table-of-Contents-Extractor-PDFs.git
```

#### `TOC_Extactor_without_testing_PDFs` Branch (without sample PDFs)
```bash
git clone --branch TOC_Extactor_without_testing_PDFs https://github.com/VedantR3907/Table-of-Contents-Extractor-PDFs.git
```

### Install Dependencies

After cloning, navigate to the project directory and install the required dependencies:
```bash
pip install -r requirements.txt
```

---

## Usage

1. **Prepare PDF Files**:  
   Place your PDF files in the `Data` folder located in the main directory of the project.

2. **Run the Script**:  
   Navigate to the `app` folder and execute the main script:
   ```bash
   cd app
   python main.py
   ```

3. **View the Output**:  
   The results will be saved in the `output` folder with the following structure (The final_output folder contains the final TOC extracted text files for all PDFs):
   ```
   output/
   ├── 01/                     # Output from the first filter
   ├── 02/                     # Output from the second filter
   ├── Filters_03/             # Outputs from sub-filters in the third stage
   │   ├── 01/
   │   ├── 02/
   │   ├── 03/
   ├── extracted_content/      # Extracted content from the PDFs
   └── Final_output/           # Final TOC text files for each PDF
   ```
   > **Note**: Refer to the [blog post](https://medium.com/@vedantrajpurohit3907/the-toc-extractor-from-pdfs-b42a3df8236a) for a detailed explanation of these stages.

---

## Maintenance

### Cleaning Output Folders

To clear all generated outputs, run the following script:
```bash
cd utils
python clear_output_folders.py
```

---

## Additional Information

- Ensure your Python environment is correctly set up to avoid dependency issues.
- For issues or contributions, submit them via GitHub.
