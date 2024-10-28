import os
from openai import OpenAI

# Function to read text from all files in a given folder
def read_text_files_from_folder(folder_path):
    # List to store tuples of filename and file contents
    file_data = []

    # Iterate over all text files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):  # Ensure it's a text file
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                # Append file name and content as a tuple
                file_data.append((filename, file.read()))
    
    return file_data  # Return list of (filename, file content) tuples

# Function to pass content to the LLM model
def call_llama_model(file_content):
    client = OpenAI(
        base_url='http://localhost:11434/v1/',  # Local base URL
        api_key='ollama',  # API key (required but ignored here)
        #  base_url='https://api.groq.com/openai/v1',  # Local base URL
        # api_key='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',  # API key (required but ignored here)
    )

    # System prompt that asks the model to print the content as is
    system_prompt = {
    'role': 'system',
    'content': '''

Your task is to get the Table of Contents (TOC) from the text given to you.

- There may be other irrelevant text in the document. Locate the heading "Table of Contents," "Contents," or "CONTENTS" and extract the Table of Contents from that section. Make sure to capture all topics and subtopics.
- A chapter (or topic/subtopic) may begin with patterns such as "Chapter 1:", "<Chapter Name>:", a chapter number (e.g., "1:"), or "PART 1:". All topics listed after these patterns should be treated as **subtopics** until the next similar pattern is detected.
- Do not extract irrelevant content from the text; only extract the Table of Contents.
- The topics and subtopics in the TOC may be numbered in various formats, including:
  - Roman numerals (i, ii, iii or I, II, III),
  - Decimal numbers (e.g., 1.0, 1.1, 1.1.1),
  - Regular numbers (e.g., 1, 2, 3).

**Goal**:

Extract the Table of Contents **precisely**, ensuring that chapters and their subtopics are properly indented to reflect their hierarchical structure, without altering any original formatting or content.

'''
}



    # User message, the content of the file
    user_message = {
        'role': 'user',
        'content': file_content
    }

    # Call the model with system and user prompts
    chat_completion = client.chat.completions.create(
        messages=[system_prompt, user_message],
        model='llama3.1:8b-instruct-q2_K'  # Model specification with version and size
    )

    # Return the response
    return chat_completion.choices[0].message.content

# Function to write extracted TOC to a specific folder with the same filename as input
def write_toc_to_file(output_folder, filename, toc_content):
    # Construct the output file path
    output_file_path = os.path.join(output_folder, filename)
    
    # Write the TOC to the file in the output folder
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(toc_content)

# Main code to run everything
if __name__ == "__main__":
    # Specify the folder path where text files are located
    input_folder_path = '../output/temp'  # Folder where input text files are located
    output_folder_path = '../output/03'   # Folder where output files should be saved

    # Get all file contents from the input folder
    file_data = read_text_files_from_folder(input_folder_path)

    # Loop through each file content and process it
    for filename, content in file_data:
        # Extract TOC using LLM function
        extracted_toc = call_llama_model(content)
        
        # Write the extracted TOC to a new file in output/03 with the same filename
        write_toc_to_file(output_folder_path, filename, extracted_toc)
    
    print(f"Extracted TOCs saved in {output_folder_path}")