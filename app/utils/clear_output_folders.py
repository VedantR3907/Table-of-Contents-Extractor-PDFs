import os

def clear_folder(folder_path):
    """
    Deletes all files inside the specified folder.
    """
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    else:
        print(f"Folder does not exist: {folder_path}")

if __name__ == "__main__":
    # Define the folder paths to clear
    root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))

    folders_to_clear = [
        os.path.join(root_folder, '01'),
        os.path.join(root_folder, '02'),
        os.path.join(root_folder, 'extracted_content'),
        os.path.join(root_folder, 'Filters_03', '01'),
        os.path.join(root_folder, 'Filters_03', '02'),
        os.path.join(root_folder, 'Filters_03', '02_Logs'),
        os.path.join(root_folder, 'Filters_03', '03'),
        os.path.join(root_folder, 'Filters_03', '03_Logs'),
        os.path.join(root_folder, 'Filters_03', '04'),
        os.path.join(root_folder, 'Final_Output')
    ]

    # Clear each folder
    for folder in folders_to_clear:
        print(f"Clearing files in folder: {folder}")
        clear_folder(folder)

    print("All specified folders have been cleared of files.")
