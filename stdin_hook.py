
# stdin compatibility hook for windowed applications
import sys
import os
import threading
import tkinter as tk
from tkinter import simpledialog

# Store the original stdin for applications that might need it
original_stdin = sys.stdin

# Create a dummy stdin that won't crash when accessed
class DummyStdin:
    def __init__(self):
        self.encoding = 'utf-8'
        
    def read(self, *args, **kwargs):
        return ""
        
    def readline(self, *args, **kwargs):
        return self._get_input("Enter input:")
        
    def readlines(self, *args, **kwargs):
        return [self.readline()]
        
    def _get_input(self, prompt):
        # Create a simple dialog to get user input
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        try:
            result = simpledialog.askstring("Input Required", prompt)
            if result is None:  # User cancelled
                return ""
            return result + "\n"
        except:
            return ""
        finally:
            try:
                root.destroy()
            except:
                pass

# This function replaces the built-in input() function
# to work in windowed mode by showing a dialog
def _patched_input(prompt=""):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    try:
        result = simpledialog.askstring("Input Required", prompt)
        if result is None:  # User cancelled
            return ""
        return result
    except:
        return ""
    finally:
        try:
            root.destroy()
        except:
            pass

# Only patch if we're in windowed mode (no console)
try:
    # Try to write to stdout to check if we have a console
    sys.stdout.write("")
except:
    # Replace stdin with our custom handler
    sys.stdin = DummyStdin()
    
    # Replace the built-in input function
    try:
        __builtins__['input'] = _patched_input
    except:
        # Different approach for some Python versions
        import builtins
        builtins.input = _patched_input
        
    print("Stdin/input handling patched for windowed mode")
