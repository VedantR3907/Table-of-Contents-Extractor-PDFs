from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(
    base_url='http://localhost:11434/v1/',  # Replace with actual API URL if needed
    api_key='ollama',  # Replace with actual API key if needed
)

# Function to read the text file content
def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

# Define system prompt for extracting topics, subtopics, and page numbers
system_prompt = """
Get me the table of content from the above
"""

# Read the text content from the file
file_path = '../output/robert-kiyosaki-the-real-book-of-real-estate.txt'  # Replace with the actual path to your text file
text_content = read_text_from_file(file_path)

# Combine the system prompt and the text content
full_prompt = system_prompt + text_content

# Make the chat completion request
chat_completion = client.chat.completions.create(
    messages=[
        {
            'role': 'system',
            'content': system_prompt
        },
        {
            'role': 'user',
            'content': text_content
        }
    ],
    model='llama3.2:1b',  # Replace with the desired model
)

# Print or process the extracted topics and subtopics with page numbers
print(chat_completion.choices[0].message.content)