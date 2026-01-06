import sys
try:
    import dotenv
    print("Dotenv imported successfully")
    with open("verification_result.txt", "w") as f:
        f.write("SUCCESS: Dotenv imported")
except ImportError:
    print("Error: dotenv not found")
    with open("verification_result.txt", "w") as f:
        f.write("FAIL: dotenv not found")
except Exception as e:
    print(f"Error: {e}")
    with open("verification_result.txt", "w") as f:
        f.write(f"FAIL: {e}")
