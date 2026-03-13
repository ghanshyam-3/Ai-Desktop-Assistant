import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def main():
    root = tk.Tk()
    root.withdraw() # Hide the main window

    print("Opening file dialog...")
    messagebox.showinfo("Select File", "Please select the 'client_secret_....json' or 'credentials.json' file you downloaded from Google Cloud.")

    file_path = filedialog.askopenfilename(
        title="Select Google Credentials JSON",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )

    if not file_path:
        print("No file selected.")
        return

    # Target path
    target_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    target_path = os.path.join(target_dir, "credentials.json")

    print(f"Selected: {file_path}")
    print(f"Target: {target_path}")

    try:
        shutil.copy2(file_path, target_path)
        print("Success! File copied to backend/credentials.json")
        messagebox.showinfo("Success", "Credentials file installed successfully!\n\nNow we will try to authenticate...")
        
        # Run auth script immediately? Or let user do it?
        # Let's simple return so user can run auth script separately or we chain it.
        
    except Exception as e:
        print(f"Error copying file: {e}")
        messagebox.showerror("Error", f"Failed to copy file: {e}")

if __name__ == "__main__":
    main()
