import os

def check_non_ascii(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        non_ascii_chars = [char for char in content if ord(char) > 127]
        if non_ascii_chars:
            print(f"Non-ASCII characters found in {file_path}: {set(non_ascii_chars)}")
        else:
            print(f"No non-ASCII characters found in {file_path}.")

# Check a specific template file
check_non_ascii('authcart/urls.py')  # Update this path
