# Smart PyInstaller Builder

A GUI tool that simplifies creating executable files from Python projects.

## Features

- Automatic detection of main script files
- Smart dependency analysis
- Easy inclusion of data files and resources
- Customizable build options
- Support for console and windowed applications

## Usage

1. Run `build_exe.py` to open the graphical interface
2. Select your main Python file or let the tool auto-detect it
3. Configure build options as needed
4. Click "Build" to create your executable

## Requirements

- Python 3.x
- PyInstaller
- Tkinter (included with most Python installations)

## Building from Source

To build this tool as an executable itself:

```bash
pyinstaller --onefile --windowed --name EXEBUI --add-data "stdin_hook.py:." build_exe.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

![Screenshot (25)](https://github.com/user-attachments/assets/8383449f-d4c2-4fb1-856a-e54711ffed0e)
