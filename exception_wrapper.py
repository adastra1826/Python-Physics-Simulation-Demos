"""
Exception wrapper utility for running physics simulations.
This wrapper catches exceptions and formats stack traces to remove full
file paths, making error messages cleaner and more readable.
"""

import traceback
import re
from template import main


if __name__ == "__main__":
    print("This exception wrapper runs the main script but hides the full filepath from stack traces.")
    try:
        main()
    except BaseException:
        lines = traceback.format_exc().splitlines()
        for line in lines:
            print(f"{re.sub(r'File \".*[\\/]([^\\/]+.py)\"', r'File "\1"', line)}")