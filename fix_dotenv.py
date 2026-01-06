import os
import sys

# The path from the traceback
file_path = r"C:\Users\ghans\AppData\Roaming\Python\Python313\site-packages\dotenv\__init__.py"

print(f"Targeting file: {file_path}")

try:
    if not os.path.exists(file_path):
        print(f"Error: File not found at: {file_path}")
        sys.exit(1)

    print("Reading file...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"File content length: {len(content)}")
    if "wrom" in content:
        print("Found Typo 'wrom'. Fixing...")
        new_content = content.replace("wrom", "from")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("Success: File patched! 'wrom' changed to 'from'.")
    elif "from typing" in content:
        print("File looks correct. 'from typing' found.")
    else:
        print("Warning: Content does not look like expected header.")
        print(f"First 50 chars: {content[:50]}")

except Exception as e:
    print(f"Failed to patch file: {e}")
    import traceback
    traceback.print_exc()
