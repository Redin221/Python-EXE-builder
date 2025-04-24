#!/usr/bin/env python
"""
Smart PyInstaller Wrapper
-------------------------
Automatically creates an executable from Python projects with intelligent detection
of entry points, dependencies, and resources.
"""

import os
import sys
import subprocess
import platform
import glob
import importlib
import pkgutil
import re
import json
import shutil
import threading
import time
from typing import List, Dict, Set, Tuple, Optional
import datetime

# GUI imports
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

class BuilderUI:
    """GUI interface for SmartExeBuilder"""
    def __init__(self, root, builder):
        self.root = root
        self.builder = builder
        self.selected_files = set()
        self.excluded_files = set()
        self.is_building = False
        
        # Set up the UI
        self.root.title("Smart PyInstaller Builder")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create tabs
        self.files_tab = ttk.Frame(self.notebook)
        self.options_tab = ttk.Frame(self.notebook)
        self.build_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.files_tab, text="Files")
        self.notebook.add(self.options_tab, text="Options")
        self.notebook.add(self.build_tab, text="Build")
        
        # Setup Files Tab
        self.setup_files_tab()
        
        # Setup Options Tab
        self.setup_options_tab()
        
        # Setup Build Tab
        self.setup_build_tab()
        
        # Scan for files on startup
        self.root.after(100, self.scan_project)
        
    def scan_project(self):
        """Scan the project for files"""
        self.log_message("Scanning project directory...")
        self.builder.scan_project()
        self.refresh_file_lists()
        if not self.builder.main_file:
            self.builder.main_file = self.builder.detect_main_file()
        self.main_file_entry.delete(0, tk.END)
        if self.builder.main_file:
            self.main_file_entry.insert(0, self.builder.main_file)
        self.log_message(f"Found {len(self.builder.detected_files)} files in project")
    
    def refresh_file_lists(self):
        """Refresh the file list displays"""
        # Python files
        self.python_files_list.delete(0, tk.END)
        for file in sorted(self.builder.python_files):
            self.python_files_list.insert(tk.END, file)
            if file in self.selected_files:
                self.python_files_list.itemconfig(tk.END, {'bg': '#e6ffe6'})  # Light green
            elif file in self.excluded_files:
                self.python_files_list.itemconfig(tk.END, {'bg': '#ffe6e6'})  # Light red
        
        # Data files
        self.data_files_list.delete(0, tk.END)
        for file in sorted(self.builder.data_files):
            self.data_files_list.insert(tk.END, file)
            if file in self.selected_files:
                self.data_files_list.itemconfig(tk.END, {'bg': '#e6ffe6'})  # Light green
            elif file in self.excluded_files:
                self.data_files_list.itemconfig(tk.END, {'bg': '#ffe6e6'})  # Light red
        
        # Resource files
        self.resource_files_list.delete(0, tk.END)
        for file in sorted(self.builder.resource_files):
            self.resource_files_list.insert(tk.END, file)
            if file in self.selected_files:
                self.resource_files_list.itemconfig(tk.END, {'bg': '#e6ffe6'})  # Light green
            elif file in self.excluded_files:
                self.resource_files_list.itemconfig(tk.END, {'bg': '#ffe6e6'})  # Light red
    
    def setup_files_tab(self):
        """Setup the Files tab with file selection controls"""
        # Main file selection
        main_file_frame = ttk.Frame(self.files_tab)
        main_file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(main_file_frame, text="Main File:").pack(side=tk.LEFT, padx=5)
        self.main_file_entry = ttk.Entry(main_file_frame, width=50)
        self.main_file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(main_file_frame, text="Browse", command=self.browse_main_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(main_file_frame, text="Detect", command=self.detect_main_file).pack(side=tk.LEFT, padx=5)
        
        # Directory inclusion
        dir_frame = ttk.LabelFrame(self.files_tab, text="Include Directories with Structure")
        dir_frame.pack(fill=tk.X, pady=5)
        
        dir_controls = ttk.Frame(dir_frame)
        dir_controls.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dir_controls, text="Directory:").pack(side=tk.LEFT, padx=5)
        self.dir_entry = ttk.Entry(dir_controls, width=30)
        self.dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(dir_controls, text="Browse", command=self.browse_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(dir_controls, text="Add", command=self.add_directory).pack(side=tk.LEFT, padx=5)
        
        # Directory list
        dir_list_frame = ttk.Frame(dir_frame)
        dir_list_frame.pack(fill=tk.X, padx=10, pady=5, expand=True)
        
        dir_scroll = ttk.Scrollbar(dir_list_frame)
        dir_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dir_list = tk.Listbox(dir_list_frame, height=4, yscrollcommand=dir_scroll.set)
        self.dir_list.pack(fill=tk.X, expand=True)
        dir_scroll.config(command=self.dir_list.yview)
        
        ttk.Button(dir_frame, text="Remove Selected", command=self.remove_directory).pack(anchor=tk.E, padx=10, pady=5)
        
        # Create frame for file lists
        lists_frame = ttk.Frame(self.files_tab)
        lists_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Python Files
        python_frame = ttk.LabelFrame(lists_frame, text="Python Files")
        python_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        python_scroll = ttk.Scrollbar(python_frame)
        python_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.python_files_list = tk.Listbox(python_frame, selectmode=tk.EXTENDED, yscrollcommand=python_scroll.set)
        self.python_files_list.pack(fill=tk.BOTH, expand=True)
        python_scroll.config(command=self.python_files_list.yview)
        
        python_buttons = ttk.Frame(python_frame)
        python_buttons.pack(fill=tk.X)
        ttk.Button(python_buttons, text="Include", command=lambda: self.mark_files(self.python_files_list, True)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(python_buttons, text="Exclude", command=lambda: self.mark_files(self.python_files_list, False)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Data Files
        data_frame = ttk.LabelFrame(lists_frame, text="Data Files")
        data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        data_scroll = ttk.Scrollbar(data_frame)
        data_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.data_files_list = tk.Listbox(data_frame, selectmode=tk.EXTENDED, yscrollcommand=data_scroll.set)
        self.data_files_list.pack(fill=tk.BOTH, expand=True)
        data_scroll.config(command=self.data_files_list.yview)
        
        data_buttons = ttk.Frame(data_frame)
        data_buttons.pack(fill=tk.X)
        ttk.Button(data_buttons, text="Include", command=lambda: self.mark_files(self.data_files_list, True)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(data_buttons, text="Exclude", command=lambda: self.mark_files(self.data_files_list, False)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Resource Files
        resource_frame = ttk.LabelFrame(lists_frame, text="Resource Files")
        resource_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        resource_scroll = ttk.Scrollbar(resource_frame)
        resource_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.resource_files_list = tk.Listbox(resource_frame, selectmode=tk.EXTENDED, yscrollcommand=resource_scroll.set)
        self.resource_files_list.pack(fill=tk.BOTH, expand=True)
        resource_scroll.config(command=self.resource_files_list.yview)
        
        resource_buttons = ttk.Frame(resource_frame)
        resource_buttons.pack(fill=tk.X)
        ttk.Button(resource_buttons, text="Include", command=lambda: self.mark_files(self.resource_files_list, True)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(resource_buttons, text="Exclude", command=lambda: self.mark_files(self.resource_files_list, False)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Bottom controls
        bottom_frame = ttk.Frame(self.files_tab)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(bottom_frame, text="Refresh Files", command=self.scan_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Reset Exclusions", command=self.reset_exclusions).pack(side=tk.LEFT, padx=5)
    
    def setup_options_tab(self):
        """Setup the Options tab with build configuration controls"""
        options_frame = ttk.Frame(self.options_tab, padding=10)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Application options
        app_frame = ttk.LabelFrame(options_frame, text="Application Options")
        app_frame.pack(fill=tk.X, pady=5)
        
        app_grid = ttk.Frame(app_frame)
        app_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Application name
        ttk.Label(app_grid, text="Application Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.app_name_var = tk.StringVar()
        ttk.Entry(app_grid, textvariable=self.app_name_var, width=30).grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # Icon file
        ttk.Label(app_grid, text="Icon File:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.icon_file_frame = ttk.Frame(app_grid)
        self.icon_file_frame.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.icon_file_var = tk.StringVar()
        ttk.Entry(self.icon_file_frame, textvariable=self.icon_file_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.icon_file_frame, text="Browse", command=self.browse_icon).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.icon_file_frame, text="Detect", command=self.detect_icon).pack(side=tk.LEFT)
        
        # Build options
        build_frame = ttk.LabelFrame(options_frame, text="Build Options")
        build_frame.pack(fill=tk.X, pady=5)
        
        build_grid = ttk.Frame(build_frame)
        build_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Mode options
        ttk.Label(build_grid, text="Application Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        mode_frame = ttk.Frame(build_grid)
        mode_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.console_mode_var = tk.BooleanVar(value=self.builder.console_mode)
        ttk.Radiobutton(mode_frame, text="Console", variable=self.console_mode_var, value=True).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="GUI (Windowed)", variable=self.console_mode_var, value=False).pack(side=tk.LEFT, padx=5)
        
        # Distribution format
        ttk.Label(build_grid, text="Distribution Format:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        format_frame = ttk.Frame(build_grid)
        format_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.one_file_var = tk.BooleanVar(value=self.builder.one_file)
        ttk.Radiobutton(format_frame, text="Single File", variable=self.one_file_var, value=True).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="Directory", variable=self.one_file_var, value=False).pack(side=tk.LEFT, padx=5)
        
        # Optimization level
        ttk.Label(build_grid, text="Optimization Level:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        optimization_frame = ttk.Frame(build_grid)
        optimization_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.optimize_level_var = tk.IntVar(value=self.builder.optimize_level)
        ttk.Radiobutton(optimization_frame, text="None", variable=self.optimize_level_var, value=0).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(optimization_frame, text="Basic", variable=self.optimize_level_var, value=1).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(optimization_frame, text="Full", variable=self.optimize_level_var, value=2).pack(side=tk.LEFT, padx=5)
        
        # Clean build
        self.clean_build_var = tk.BooleanVar(value=self.builder.clean_build)
        ttk.Checkbutton(build_grid, text="Clean Build (Remove previous build files)", variable=self.clean_build_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Verbose output
        self.verbose_var = tk.BooleanVar(value=self.builder.verbose)
        ttk.Checkbutton(build_grid, text="Verbose Output", variable=self.verbose_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # MT5 detection
        self.mt5_detection_var = tk.BooleanVar(value=self.builder.mt5_detection)
        ttk.Checkbutton(build_grid, text="MetaTrader 5 Detection and Optimization", variable=self.mt5_detection_var).grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Output directories
        output_frame = ttk.LabelFrame(options_frame, text="Output Directories")
        output_frame.pack(fill=tk.X, pady=5)
        
        output_grid = ttk.Frame(output_frame)
        output_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Build directory
        ttk.Label(output_grid, text="Build Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.build_dir_frame = ttk.Frame(output_grid)
        self.build_dir_frame.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.build_dir_var = tk.StringVar(value=self.builder.build_dir)
        ttk.Entry(self.build_dir_frame, textvariable=self.build_dir_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.build_dir_frame, text="Browse", command=self.browse_build_dir).pack(side=tk.LEFT, padx=5)
        
        # Dist directory
        ttk.Label(output_grid, text="Distribution Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.dist_dir_frame = ttk.Frame(output_grid)
        self.dist_dir_frame.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.dist_dir_var = tk.StringVar(value=self.builder.dist_dir)
        ttk.Entry(self.dist_dir_frame, textvariable=self.dist_dir_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.dist_dir_frame, text="Browse", command=self.browse_dist_dir).pack(side=tk.LEFT, padx=5)
        
        # Save/load config buttons
        config_frame = ttk.Frame(options_frame)
        config_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(config_frame, text="Save Configuration", command=self.save_config_ui).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_frame, text="Load Configuration", command=self.load_config_ui).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_frame, text="Reset to Defaults", command=self.reset_config).pack(side=tk.LEFT, padx=5)
    
    def setup_build_tab(self):
        """Setup the Build tab with build controls and log output"""
        build_frame = ttk.Frame(self.build_tab, padding=10)
        build_frame.pack(fill=tk.BOTH, expand=True)
        
        # Command preview
        preview_frame = ttk.LabelFrame(build_frame, text="Command Preview")
        preview_frame.pack(fill=tk.X, pady=5)
        
        self.command_preview = tk.Text(preview_frame, height=5, wrap=tk.WORD)
        self.command_preview.pack(fill=tk.X, padx=10, pady=10)
        self.command_preview.config(state=tk.DISABLED)
        
        # Build controls
        control_frame = ttk.Frame(build_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Generate Command", command=self.update_command_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Build Executable", command=self.build_executable).pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(control_frame, orient=tk.HORIZONTAL, length=300, mode='determinate', variable=self.progress_var)
        self.progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Log output
        log_frame = ttk.LabelFrame(build_frame, text="Build Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_output = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_output.config(state=tk.DISABLED)
        
        # Output location
        output_frame = ttk.Frame(build_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Executable Location:").pack(side=tk.LEFT, padx=5)
        self.executable_location = ttk.Entry(output_frame, width=50)
        self.executable_location.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Open Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
    
    def mark_files(self, listbox, include=True):
        """Mark selected files for inclusion or exclusion"""
        selected_indices = listbox.curselection()
        if not selected_indices:
            return
            
        files = [listbox.get(i) for i in selected_indices]
        
        for file in files:
            if include:
                self.selected_files.add(file)
                if file in self.excluded_files:
                    self.excluded_files.remove(file)
            else:
                self.excluded_files.add(file)
                if file in self.selected_files:
                    self.selected_files.remove(file)
        
        self.refresh_file_lists()
    
    def clear_selection(self):
        """Clear all file selections"""
        self.selected_files.clear()
        self.refresh_file_lists()
    
    def reset_exclusions(self):
        """Reset all file exclusions"""
        self.excluded_files.clear()
        self.refresh_file_lists()
    
    def browse_main_file(self):
        """Browse for the main Python file"""
        filename = filedialog.askopenfilename(
            title="Select Main Python File",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")],
            initialdir=self.builder.project_dir
        )
        if filename:
            # Convert to relative path if within project directory
            if os.path.commonpath([filename, self.builder.project_dir]) == self.builder.project_dir:
                filename = os.path.relpath(filename, self.builder.project_dir)
            self.main_file_entry.delete(0, tk.END)
            self.main_file_entry.insert(0, filename)
            self.builder.main_file = filename
    
    def detect_main_file(self):
        """Detect the main Python file"""
        main_file = self.builder.detect_main_file()
        if main_file:
            self.main_file_entry.delete(0, tk.END)
            self.main_file_entry.insert(0, main_file)
            self.log_message(f"Detected main file: {main_file}")
        else:
            messagebox.showwarning("Detection Failed", "Could not automatically detect the main file. Please select it manually.")
    
    def browse_icon(self):
        """Browse for an icon file"""
        filename = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=[("Icon Files", "*.ico"), ("All Files", "*.*")],
            initialdir=self.builder.project_dir
        )
        if filename:
            # Convert to relative path if within project directory
            if os.path.commonpath([filename, self.builder.project_dir]) == self.builder.project_dir:
                filename = os.path.relpath(filename, self.builder.project_dir)
            self.icon_file_var.set(filename)
    
    def detect_icon(self):
        """Detect an icon file"""
        icon_file = self.builder.detect_icon()
        if icon_file:
            self.icon_file_var.set(icon_file)
            self.log_message(f"Detected icon file: {icon_file}")
        else:
            messagebox.showwarning("Detection Failed", "Could not automatically detect an icon file.")
    
    def browse_build_dir(self):
        """Browse for build directory"""
        directory = filedialog.askdirectory(
            title="Select Build Directory",
            initialdir=os.path.dirname(self.builder.build_dir)
        )
        if directory:
            self.build_dir_var.set(directory)
    
    def browse_dist_dir(self):
        """Browse for distribution directory"""
        directory = filedialog.askdirectory(
            title="Select Distribution Directory",
            initialdir=os.path.dirname(self.builder.dist_dir)
        )
        if directory:
            self.dist_dir_var.set(directory)
    
    def save_config_ui(self):
        """Save the current configuration"""
        self.update_builder_from_ui()
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=self.builder.project_dir,
            defaultextension=".json"
        )
        if filename:
            try:
                self.builder.save_config_to_file(filename)
                self.log_message(f"Configuration saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving configuration: {e}")
    
    def load_config_ui(self):
        """Load a configuration file"""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=self.builder.project_dir
        )
        if filename:
            try:
                self.builder.load_config_from_file(filename)
                self.update_ui_from_builder()
                self.log_message(f"Configuration loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Load Error", f"Error loading configuration: {e}")
    
    def reset_config(self):
        """Reset configuration to defaults"""
        if messagebox.askyesno("Reset Configuration", "Are you sure you want to reset all configuration to defaults?"):
            self.builder = SmartExeBuilder(self.builder.project_dir)
            self.update_ui_from_builder()
            self.log_message("Configuration reset to defaults")
    
    def update_ui_from_builder(self):
        """Update UI elements from builder settings"""
        # Main file
        self.main_file_entry.delete(0, tk.END)
        if self.builder.main_file:
            self.main_file_entry.insert(0, self.builder.main_file)
        
        # Options
        self.app_name_var.set(self.builder.app_name or "")
        self.icon_file_var.set(self.builder.icon_file or "")
        self.console_mode_var.set(self.builder.console_mode)
        self.one_file_var.set(self.builder.one_file)
        self.optimize_level_var.set(self.builder.optimize_level)
        self.clean_build_var.set(self.builder.clean_build)
        self.verbose_var.set(self.builder.verbose)
        self.mt5_detection_var.set(self.builder.mt5_detection)
        self.build_dir_var.set(self.builder.build_dir)
        self.dist_dir_var.set(self.builder.dist_dir)
        
        # Update directory list
        self.update_directory_list()
        
        # Refresh file lists
        self.refresh_file_lists()
    
    def update_builder_from_ui(self):
        """Update builder settings from UI elements"""
        # Main file
        self.builder.main_file = self.main_file_entry.get()
        
        # Options
        self.builder.app_name = self.app_name_var.get() or None
        self.builder.icon_file = self.icon_file_var.get() or None
        self.builder.console_mode = self.console_mode_var.get()
        self.builder.one_file = self.one_file_var.get()
        self.builder.optimize_level = self.optimize_level_var.get()
        self.builder.clean_build = self.clean_build_var.get()
        self.builder.verbose = self.verbose_var.get()
        self.builder.mt5_detection = self.mt5_detection_var.get()
        self.builder.build_dir = self.build_dir_var.get()
        self.builder.dist_dir = self.dist_dir_var.get()
        
        # Update file lists based on selections
        self.builder.data_files = [f for f in self.builder.data_files if f not in self.excluded_files]
        self.builder.resource_files = [f for f in self.builder.resource_files if f not in self.excluded_files]
        
        # Add selected files if they're not already categorized
        for file in self.selected_files:
            if file not in self.builder.data_files and file not in self.builder.resource_files:
                if file.endswith(('.json', '.csv', '.txt', '.xml', '.html', '.css')):
                    self.builder.data_files.append(file)
                elif file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
                    self.builder.resource_files.append(file)
    
    def update_command_preview(self):
        """Update the command preview"""
        self.update_builder_from_ui()
        if not self.builder.main_file:
            messagebox.showwarning("Missing Main File", "Please specify the main Python file.")
            return
            
        try:
            cmd = self.builder.generate_command(self.builder.main_file)
            cmd_str = " ".join(cmd)
            
            self.command_preview.config(state=tk.NORMAL)
            self.command_preview.delete(1.0, tk.END)
            self.command_preview.insert(tk.END, cmd_str)
            self.command_preview.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Command Generation Error", str(e))
    
    def log_message(self, message, level="INFO"):
        """Add a message to the log output"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_output.config(state=tk.NORMAL)
        self.log_output.insert(tk.END, log_line)
        self.log_output.see(tk.END)
        self.log_output.config(state=tk.DISABLED)
    
    def build_executable(self):
        """Start the build process"""
        if self.is_building:
            messagebox.showinfo("Build in Progress", "A build is already in progress.")
            return
            
        self.update_builder_from_ui()
        
        if not self.builder.main_file:
            messagebox.showwarning("Missing Main File", "Please specify the main Python file.")
            return
        
        # Prepare the builder
        self.is_building = True
        self.progress_var.set(0)
        
        # Clear the log
        self.log_output.config(state=tk.NORMAL)
        self.log_output.delete(1.0, tk.END)
        self.log_output.config(state=tk.DISABLED)
        
        # Override the builder's log method to update our UI
        original_log = self.builder.log
        def ui_log(message, level="INFO"):
            original_log(message, level)
            self.log_message(message, level)
            # Update progress based on message content
            if "completed successfully" in message:
                self.progress_var.set(100)
                self.executable_location.delete(0, tk.END)
                
                # Try to find the executable path
                exe_name = os.path.splitext(os.path.basename(self.builder.main_file))[0]
                if platform.system() == "Windows":
                    exe_path = os.path.join(self.builder.dist_dir, exe_name, f"{exe_name}.exe") if not self.builder.one_file else os.path.join(self.builder.dist_dir, f"{exe_name}.exe")
                else:
                    exe_path = os.path.join(self.builder.dist_dir, exe_name, exe_name) if not self.builder.one_file else os.path.join(self.builder.dist_dir, exe_name)
                    
                if os.path.exists(exe_path):
                    self.executable_location.insert(0, exe_path)
            elif "starting" in message.lower():
                self.progress_var.set(10)
            elif "scanning" in message.lower():
                self.progress_var.set(20)
            elif "analyzing" in message.lower():
                self.progress_var.set(30)
            elif "generating" in message.lower():
                self.progress_var.set(40)
            elif "running pyinstaller" in message.lower():
                self.progress_var.set(50)
            
            # Force update the UI
            self.root.update_idletasks()
            
        self.builder.log = ui_log
        
        # Run the build in a separate thread
        def run_build():
            try:
                success = self.builder.build()
                if success:
                    messagebox.showinfo("Build Complete", "Executable built successfully!")
                else:
                    messagebox.showerror("Build Failed", "Failed to build executable. Check the log for details.")
            except Exception as e:
                messagebox.showerror("Build Error", str(e))
            finally:
                self.is_building = False
                self.builder.log = original_log  # Restore original log method
        
        build_thread = threading.Thread(target=run_build)
        build_thread.daemon = True
        build_thread.start()
    
    def open_output_folder(self):
        """Open the output folder in the file explorer"""
        location = self.executable_location.get()
        if not location:
            location = self.builder.dist_dir
            
        folder = os.path.dirname(location)
        
        if not os.path.exists(folder):
            messagebox.showwarning("Folder Not Found", "The output folder does not exist yet.")
            return
            
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", folder])
            else:  # Linux
                subprocess.call(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
    
    def browse_directory(self):
        """Browse for a directory to include"""
        directory = filedialog.askdirectory(
            title="Select Directory to Include",
            initialdir=self.builder.project_dir
        )
        if directory:
            # Convert to relative path if within project directory
            if os.path.commonpath([directory, self.builder.project_dir]) == self.builder.project_dir:
                directory = os.path.relpath(directory, self.builder.project_dir)
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
    
    def add_directory(self):
        """Add a directory to be included with structure preserved"""
        directory = self.dir_entry.get().strip()
        if directory:
            if self.builder.include_directory(directory):
                self.update_directory_list()
                self.dir_entry.delete(0, tk.END)
    
    def remove_directory(self):
        """Remove a directory from the include list"""
        selected_indices = self.dir_list.curselection()
        if not selected_indices:
            return
            
        # Get directories to remove
        for i in reversed(selected_indices):  # Reverse to avoid index shifting issues
            directory_entry = self.builder.include_directories[i]
            self.builder.include_directories.pop(i)
            self.log_message(f"Removed directory {directory_entry[0]} from included directories")
            
        self.update_directory_list()
    
    def update_directory_list(self):
        """Update the directory list display"""
        self.dir_list.delete(0, tk.END)
        for directory, destination in self.builder.include_directories:
            self.dir_list.insert(tk.END, f"{directory} → {destination}")
            
class SmartExeBuilder:
    def __init__(self, project_dir: str = None, main_file: str = None):
        """Initialize the builder with project directory and optional main file"""
        self.project_dir = project_dir or os.getcwd()
        self.main_file = main_file
        self.detected_files = []
        self.python_files = []
        self.resource_files = []
        self.data_files = []
        self.hidden_imports = set()
        self.binary_files = []
        self.excluded_packages = ['__pycache__', 'build', 'dist', 'venv', 'env', '.venv', '.env', '.git', '.github']
        self.console_mode = True
        self.one_file = False
        self.icon_file = None
        self.build_dir = os.path.join(self.project_dir, 'build')
        self.dist_dir = os.path.join(self.project_dir, 'dist')
        self.clean_build = True
        self.verbose = True
        self.bundle_level = 3  # 0-3, with 3 being most aggressive bundling
        self.optimize_level = 2  # Python optimization level (0-2)
        self.target_platform = platform.system().lower()  # Auto-detect platform
        self.app_name = None  # Custom application name
        self.mt5_detection = True  # Whether to auto-detect MetaTrader 5
        self.mt5_path = None  # Path to MetaTrader 5 installation
        self.skip_timestamp = False  # Skip setting timestamp (helps with permission issues)
        self.alt_temp_dir = None  # Alternative temp directory if default has permission issues
        self.include_directories = []  # Directories to include with their structure
        self.excluded_directories = []  # Directories to exclude
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamps and levels"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_pyinstaller(self) -> bool:
        """Check if PyInstaller is installed and install it if not"""
        try:
            import PyInstaller
            self.log(f"PyInstaller {PyInstaller.__version__} found")
            return True
        except ImportError:
            self.log("PyInstaller not found. Installing...", "WARNING")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
                self.log("PyInstaller installed successfully", "SUCCESS")
                return True
            except subprocess.CalledProcessError:
                self.log("Failed to install PyInstaller. Please install manually.", "ERROR")
                return False
    
    def scan_project(self):
        """Scan the project directory to detect files"""
        self.log(f"Scanning project directory: {self.project_dir}")
        
        # Get all files in the project directory
        for root, dirs, files in os.walk(self.project_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_packages]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_dir)
                
                # Skip build artifacts
                if any(rel_path.startswith(pkg) for pkg in self.excluded_packages):
                    continue
                
                self.detected_files.append(rel_path)
                
                # Categorize by file type
                if file.endswith('.py'):
                    self.python_files.append(rel_path)
                elif file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
                    self.resource_files.append(rel_path)
                elif file.endswith(('.json', '.csv', '.txt', '.xml', '.html', '.css')):
                    self.data_files.append(rel_path)
                elif file.endswith(('.dll', '.so', '.dylib')):
                    self.binary_files.append(rel_path)
        
        # Scan for potential directories that might need to be included
        self.detect_important_directories()
            
        self.log(f"Found {len(self.detected_files)} files in project")
        self.log(f"  - Python files: {len(self.python_files)}")
        self.log(f"  - Resource files: {len(self.resource_files)}")
        self.log(f"  - Data files: {len(self.data_files)}")
        self.log(f"  - Binary files: {len(self.binary_files)}")
    
    def detect_important_directories(self):
        """Detect directories that might need to be included with structure preserved"""
        important_dirs = []
        
        # Common names for directories that often need to be included
        potential_dirs = ['templates', 'static', 'assets', 'resources', 'config', 'data', 'images', 'themes', 'locales', 'i18n']
        
        for root, dirs, files in os.walk(self.project_dir):
            for dir_name in dirs:
                if dir_name in potential_dirs or dir_name.lower() in potential_dirs:
                    rel_path = os.path.relpath(os.path.join(root, dir_name), self.project_dir)
                    # Skip if it's part of excluded packages
                    if any(rel_path.startswith(pkg) for pkg in self.excluded_packages):
                        continue
                    important_dirs.append(rel_path)
        
        if important_dirs:
            self.log(f"Detected potential directory structures that might need inclusion: {important_dirs}")
            self.log("Use include_directory() method or --include-dir option to include these with structure")
    
    def include_directory(self, directory_path, destination=None):
        """
        Add a directory to be included in the build with its structure
        
        Args:
            directory_path: Path to the directory to include
            destination: Optional destination relative to the executable
        """
        # Convert to relative path if within project directory
        if os.path.isabs(directory_path) and os.path.commonpath([directory_path, self.project_dir]) == self.project_dir:
            directory_path = os.path.relpath(directory_path, self.project_dir)
            
        # Make sure the directory exists
        abs_path = os.path.join(self.project_dir, directory_path) if not os.path.isabs(directory_path) else directory_path
        if not os.path.isdir(abs_path):
            self.log(f"Warning: Directory {directory_path} does not exist", "WARNING")
            return False
            
        # Set destination to match source directory structure if not specified
        if destination is None:
            destination = os.path.dirname(directory_path) or "."
            
        directory_entry = (directory_path, destination)
        if directory_entry not in self.include_directories:
            self.include_directories.append(directory_entry)
            self.log(f"Added directory {directory_path} to be included in build (destination: {destination})")
            return True
        return False
        
    def exclude_directory(self, directory_path):
        """Exclude a directory from the build"""
        # Convert to relative path if within project directory
        if os.path.isabs(directory_path) and os.path.commonpath([directory_path, self.project_dir]) == self.project_dir:
            directory_path = os.path.relpath(directory_path, self.project_dir)
            
        if directory_path not in self.excluded_directories:
            self.excluded_directories.append(directory_path)
            self.log(f"Excluded directory {directory_path} from build")
            return True
        return False
    
    def detect_main_file(self) -> Optional[str]:
        """Try to detect the main entry point file"""
        if self.main_file and os.path.exists(os.path.join(self.project_dir, self.main_file)):
            self.log(f"Using provided main file: {self.main_file}")
            return self.main_file
        
        # Look for common main file names
        common_names = ['main.py', 'app.py', 'run.py', 'start.py', 'cli.py']
        for name in common_names:
            if name in self.python_files:
                self.log(f"Detected main file by common name: {name}")
                return name
        
        # Look for files with if __name__ == "__main__" pattern
        for py_file in self.python_files:
            file_path = os.path.join(self.project_dir, py_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content:
                        self.log(f"Detected main file with __main__ check: {py_file}")
                        return py_file
            except:
                continue
        
        # If only one Python file exists, use it
        if len(self.python_files) == 1:
            self.log(f"Only one Python file in project, using as main: {self.python_files[0]}")
            return self.python_files[0]
            
        # Get the largest Python file
        largest_file = None
        largest_size = 0
        for py_file in self.python_files:
            file_path = os.path.join(self.project_dir, py_file)
            size = os.path.getsize(file_path)
            if size > largest_size:
                largest_size = size
                largest_file = py_file
        
        if largest_file:
            self.log(f"Using largest Python file as main: {largest_file}", "WARNING")
            return largest_file
            
        self.log("Could not detect main file. Please specify manually.", "ERROR")
        return None
    
    def analyze_imports(self, file_path: str) -> Set[str]:
        """Analyze Python file to detect imports"""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Match import statements
            import_patterns = [
                r'^\s*import\s+(\S+)(?:\s+as\s+\S+)?',  # import xxx [as yyy]
                r'^\s*from\s+(\S+)\s+import',  # from xxx import
                r'__import__\([\'"](.+?)[\'"]\)',  # __import__('xxx')
                r'importlib\.import_module\([\'"](.+?)[\'"]\)',  # importlib.import_module('xxx')
            ]
            
            for pattern in import_patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    module_name = match.group(1)
                    # Extract the top-level package
                    top_package = module_name.split('.')[0]
                    imports.add(top_package)
            
        except Exception as e:
            self.log(f"Error analyzing imports in {file_path}: {e}", "ERROR")
        
        return imports
    
    def detect_dependencies(self):
        """Detect project dependencies from import statements"""
        self.log("Analyzing dependencies...")
        all_imports = set()
        
        # Analyze each Python file
        for py_file in self.python_files:
            file_path = os.path.join(self.project_dir, py_file)
            file_imports = self.analyze_imports(file_path)
            all_imports.update(file_imports)
        
        # Filter out standard library modules
        stdlib_modules = set(sys.builtin_module_names)
        stdlib_modules.update([m[1] for m in pkgutil.iter_modules()])
        
        # Filter out project's own modules
        project_modules = set(os.path.splitext(os.path.basename(py_file))[0] for py_file in self.python_files)
        
        # Add common problematic hidden imports
        potential_hidden_imports = {
            'pandas': ['pandas._libs.tslibs.timedeltas', 'pandas._libs.tslibs.nattype', 'pandas._libs.tslibs.np_datetime'],
            'numpy': ['numpy.random.common', 'numpy.random.bounded_integers', 'numpy.random.entropy'],
            'matplotlib': ['matplotlib.backends.backend_tkagg'],
            'sqlalchemy': ['sqlalchemy.ext.baked'],
            'tkinter': ['tkinter.commondialog'],
            'PyQt5': ['PyQt5.sip'],
            'MetaTrader5': ['MetaTrader5', 'MetaTrader5.common', 'MetaTrader5.constants', 'MetaTrader5.utils']
        }
        
        for import_name in all_imports:
            if import_name in potential_hidden_imports:
                self.hidden_imports.update(potential_hidden_imports[import_name])
        
        # Special handling for MetaTrader5
        if 'MetaTrader5' in all_imports or any('MetaTrader5' in imp for imp in all_imports):
            self.detect_mt5_dependencies()
        
        self.log(f"Detected {len(all_imports)} imports, {len(self.hidden_imports)} hidden imports")
    
    def detect_mt5_dependencies(self):
        """Detect and handle MetaTrader 5 specific dependencies"""
        if not self.mt5_detection:
            return
            
        self.log("Detected MetaTrader 5 - adding specific optimizations", "INFO")
        
        # Try to find MT5 installation path
        mt5_paths = []
        
        if platform.system() == "Windows":
            # Common MT5 installation paths on Windows
            program_files_paths = [
                os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
            ]
            
            for base_path in program_files_paths:
                mt5_paths.extend([
                    os.path.join(base_path, 'MetaTrader 5'),
                    os.path.join(base_path, 'MetaTrader5')
                ])
                
        elif platform.system() == "Darwin":  # macOS
            # Common MT5 installation paths on macOS
            mt5_paths = [
                '/Applications/MetaTrader 5.app',
                os.path.expanduser('~/Applications/MetaTrader 5.app')
            ]
        
        # Find MT5 terminal path
        for path in mt5_paths:
            if os.path.exists(path):
                self.mt5_path = path
                self.log(f"Found MetaTrader 5 installation at: {path}")
                break
        
        # Add MT5 specific data files if found
        if self.mt5_path:
            # Look for specific MT5 files that might be needed
            mt5_data_files = [
                ('MQL5', 'MQL5'),
                ('Config', 'Config'),
                ('Logs', 'Logs')
            ]
            
            for src, dst in mt5_data_files:
                full_src = os.path.join(self.mt5_path, src)
                if os.path.exists(full_src):
                    self.log(f"Adding MT5 data directory: {src}")
                    # Add to PyInstaller command later
        
        # Add special MT5 hidden imports
        mt5_hidden_imports = [
            'MetaTrader5.symbols_get',
            'MetaTrader5.order_send',
            'MetaTrader5.positions_get',
            'MetaTrader5.account_info',
            'MetaTrader5.terminal_info',
            'MetaTrader5.copy_rates_from'
        ]
        
        self.hidden_imports.update(mt5_hidden_imports)
    
    def detect_icon(self) -> Optional[str]:
        """Try to find an icon file for the application"""
        icon_extensions = ['.ico', '.icns']
        
        # Look for common icon names
        common_names = ['icon', 'app_icon', 'application', 'logo', 'favicon']
        
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                file_name, ext = os.path.splitext(file.lower())
                
                if ext in icon_extensions:
                    if file_name in common_names:
                        self.log(f"Found icon file: {file_path}")
                        return file_path
        
        for resource in self.resource_files:
            _, ext = os.path.splitext(resource.lower())
            if ext in icon_extensions:
                self.log(f"Using resource as icon: {resource}")
                return resource
                
        # On Windows, try to create a default icon if none is found
        if platform.system() == "Windows" and not self.icon_file:
            try:
                self.log("No icon found, attempting to create a default icon")
                default_icon_path = os.path.join(self.project_dir, "default_icon.ico")
                # If we have PIL installed, we can generate a simple icon
                try:
                    from PIL import Image, ImageDraw
                    
                    # Create a simple colored square icon
                    img = Image.new('RGBA', (256, 256), color=(0, 120, 212))
                    draw = ImageDraw.Draw(img)
                    # Add a simple shape
                    draw.rectangle((50, 50, 206, 206), fill=(255, 255, 255))
                    
                    # Save in multiple sizes as required by ICO format
                    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                    img.save(default_icon_path, format='ICO', sizes=icon_sizes)
                    
                    self.log(f"Created default icon at {default_icon_path}")
                    return default_icon_path
                except ImportError:
                    self.log("PIL not available to create default icon", "WARNING")
            except Exception as e:
                self.log(f"Error creating default icon: {e}", "ERROR")
                
        return None
    
    def generate_command(self, main_file: str) -> List[str]:
        """Generate PyInstaller command with appropriate options"""
        cmd = [sys.executable, '-m', 'PyInstaller']
        
        # Basic options
        if self.one_file:
            cmd.append('--onefile')
        else:
            cmd.append('--onedir')
            
        # Set console/windowed mode with special handling for stdin
        if self.console_mode:
            cmd.append('--console')
        else:
            # Create stdin handler for GUI mode
            stdin_hook = self.generate_stdin_hook()
            stdin_hook_path = os.path.join(self.project_dir, 'stdin_hook.py')
            try:
                with open(stdin_hook_path, 'w') as f:
                    f.write(stdin_hook)
                cmd.extend(['--runtime-hook', stdin_hook_path])
                self.log("Added stdin compatibility hook for windowed mode")
            except:
                self.log("Failed to create stdin compatibility hook", "WARNING")
            
            cmd.append('--windowed')
        
        # Add icon if found - ensure proper formatting and validation
        if self.icon_file:
            # Ensure the icon path is absolute
            if not os.path.isabs(self.icon_file):
                icon_path = os.path.join(self.project_dir, self.icon_file)
            else:
                icon_path = self.icon_file
                
            # Validate icon exists
            if os.path.exists(icon_path):
                self.log(f"Using icon file: {icon_path}")
                # Force icon path to be absolute - this is critical for PyInstaller
                cmd.extend(['--icon', os.path.abspath(icon_path)])
                
                # For Windows, also add resource flags to ensure icon is applied
                if platform.system() == "Windows":
                    # Check if the icon is a valid .ico file
                    if not icon_path.lower().endswith('.ico'):
                        self.log(f"Warning: On Windows, icons should be .ico files. Your icon: {icon_path}", "WARNING")
                    else:
                        self.log(f"Icon file is a valid .ico format", "INFO")
            else:
                self.log(f"Warning: Icon file not found: {icon_path}", "WARNING")
                # Try to find any icon file if specified one doesn't exist
                detected_icon = self.detect_icon()
                if detected_icon:
                    icon_path = os.path.join(self.project_dir, detected_icon)
                    self.log(f"Using detected icon file instead: {icon_path}")
                    cmd.extend(['--icon', os.path.abspath(icon_path)])
                else:
                    self.log("No valid icon file found", "WARNING")
        
        # Add data files
        for data_file in self.data_files:
            separator = ';' if platform.system() == 'Windows' else ':'
            dest_dir = os.path.dirname(data_file) or "."
            cmd.extend(['--add-data', f'{data_file}{separator}{dest_dir}'])
        
        # Add binary files
        for binary_file in self.binary_files:
            separator = ';' if platform.system() == 'Windows' else ':'
            dest_dir = os.path.dirname(binary_file) or "."
            cmd.extend(['--add-binary', f'{binary_file}{separator}{dest_dir}'])
        
        # Add resource files
        for resource_file in self.resource_files:
            separator = ';' if platform.system() == 'Windows' else ':'
            dest_dir = os.path.dirname(resource_file) or "."
            cmd.extend(['--add-data', f'{resource_file}{separator}{dest_dir}'])
            
        # Add directories with structure preserved
        for directory, destination in self.include_directories:
            abs_dir = os.path.join(self.project_dir, directory) if not os.path.isabs(directory) else directory
            if os.path.isdir(abs_dir):
                separator = ';' if platform.system() == 'Windows' else ':'
                cmd.extend(['--add-data', f'{abs_dir}{separator}{destination}'])
                self.log(f"Including directory structure: {directory} -> {destination}")
        
        # Add excluded directories
        for directory in self.excluded_directories:
            cmd.extend(['--exclude-module', directory])
        
        # Add hidden imports
        for hidden_import in self.hidden_imports:
            cmd.extend(['--hidden-import', hidden_import])
        
        # Additional options
        if self.clean_build:
            cmd.append('--clean')
        if not self.verbose:
            cmd.append('--quiet')
        
        # Set optimization level correctly
        if self.optimize_level > 0:
            cmd.extend(['--optimize', str(self.optimize_level)])
        
        # Set name if provided
        if self.app_name:
            cmd.extend(['--name', self.app_name])
        
        # Output directories
        cmd.extend(['--workpath', self.build_dir])
        cmd.extend(['--distpath', self.dist_dir])
        
        # Add option to skip timestamp (helps with permission issues)
        if self.skip_timestamp:
            cmd.append('--no-compile')  # This can help bypass some permission issues
        
        # Alternative temp directory if needed
        if self.alt_temp_dir and os.path.exists(self.alt_temp_dir):
            cmd.extend(['--workpath', self.alt_temp_dir])
        
        # MT5 specific options
        if self.mt5_detection and self.mt5_path:
            # Add runtime hooks for MT5
            hook_content = self.generate_mt5_runtime_hook()
            hook_path = os.path.join(self.project_dir, 'mt5_hook.py')
            try:
                with open(hook_path, 'w') as f:
                    f.write(hook_content)
                cmd.extend(['--runtime-hook', hook_path])
            except:
                self.log("Failed to create MT5 runtime hook", "WARNING")
        
        # Windows specific - manifest for proper admin privileges and version info
        if platform.system() == "Windows":
            # Add proper manifest for exe
            manifest_content = self.generate_manifest()
            manifest_path = os.path.join(self.project_dir, 'app.manifest')
            try:
                with open(manifest_path, 'w') as f:
                    f.write(manifest_content)
                cmd.extend(['--manifest', manifest_path])
                self.log("Added Windows manifest file for proper application behavior")
                self.log("Note: 'win32' in the manifest refers to the Windows platform, not the bit architecture", "INFO")
                self.log("This is the correct value for both 32-bit and 64-bit Windows applications", "INFO")
            except:
                self.log("Failed to create manifest file", "WARNING")
            
            # Force console/windowed mode more explicitly for Windows
            if not self.console_mode:
                if '--console' in cmd:
                    cmd.remove('--console')
                if '--windowed' not in cmd:
                    cmd.append('--windowed')
                cmd.extend(['--uac-admin'])  # Add UAC elevation for proper permissions
            else:
                if '--windowed' in cmd:
                    cmd.remove('--windowed')
                if '--console' not in cmd:
                    cmd.append('--console')
        
        # Add main file
        cmd.append(main_file)
        
        # Debug output of final command
        self.log(f"Final PyInstaller command: {' '.join(cmd)}", "DEBUG")
        
        return cmd

    def generate_stdin_hook(self) -> str:
        """Generate a runtime hook to handle stdin in windowed mode"""
        return """
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
            return result + "\\n"
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
"""

    def generate_manifest(self) -> str:
        """Generate a Windows manifest file for proper application behavior"""
        # Note: win32 refers to the Windows platform, not the bit architecture
        # It's the correct value for both 32-bit and 64-bit Windows applications
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <!-- win32 is the Windows platform identifier, not the bit architecture -->
  <!-- This is correct for both 32-bit and 64-bit Windows applications -->
  <assemblyIdentity type="win32" name="Application" version="1.0.0.0" processorArchitecture="*"/>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 and 11 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <!-- Windows 8.1 -->
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <!-- Windows 8 -->
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <!-- Windows 7 -->
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
      <!-- Windows Vista -->
      <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
    </application>
  </compatibility>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
      <!-- processorArchitecture is automatically set based on the build -->
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
    </dependentAssembly>
  </dependency>
</assembly>
"""

    def generate_mt5_runtime_hook(self) -> str:
        """Generate a runtime hook for MetaTrader 5"""
        return """
# MetaTrader 5 runtime hook
import os
import sys
import importlib.util

def setup_mt5_paths():
    # Try to add MT5 paths to system path if needed
    known_paths = [
        os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'MetaTrader 5'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'MetaTrader 5'),
        '/Applications/MetaTrader 5.app',
        os.path.expanduser('~/Applications/MetaTrader 5.app')
    ]
    
    # Add any found paths to sys.path
    for path in known_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.append(path)
            print(f"Added MT5 path to system path: {path}")

# Set up MetaTrader 5 paths
setup_mt5_paths()

# Pre-import MT5 if available
try:
    import MetaTrader5
    print(f"Successfully pre-loaded MetaTrader5 module")
except Exception as e:
    print(f"Could not pre-load MetaTrader5: {e}")
"""

    def run_command(self, cmd: List[str]) -> bool:
        """Run the PyInstaller command"""
        self.log(f"Running PyInstaller with command: {' '.join(cmd)}")
        
        try:
            # First check if any executable with same name is already running
            if self.app_name:
                exe_name = self.app_name
            else:
                exe_name = os.path.splitext(os.path.basename(self.main_file))[0]
                
            exe_path = os.path.join(self.dist_dir, f"{exe_name}.exe")
            if os.path.exists(exe_path):
                self.log(f"WARNING: The target executable {exe_path} already exists", "WARNING")
                self.log("If the build fails with permission errors, please make sure the executable is not running", "WARNING")
                
                # Try to remove the existing executable if it's not running
                try:
                    os.remove(exe_path)
                    self.log(f"Successfully removed existing executable", "INFO")
                except PermissionError:
                    self.log(f"Could not remove existing executable - it may be in use", "WARNING")
                    self.log("Consider closing any running instances before building", "WARNING")
                    
                    # Ask user to enable skip_timestamp option
                    self.log("Try running with the --skip-timestamp option if you encounter permission errors", "TIP")
            
            process = subprocess.Popen(
                cmd, 
                cwd=self.project_dir,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Stream output
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log(line.strip(), "PYINSTALLER")
            
            process.wait()
            
            if process.returncode == 0:
                self.log("PyInstaller completed successfully", "SUCCESS")
                return True
            else:
                # Check for common error patterns
                if "Permission denied" in ' '.join(line for line in process.stdout):
                    self.log("Permission errors detected. Try these solutions:", "ERROR")
                    self.log("1. Close any running instances of the application", "TIP")
                    self.log("2. Run as administrator", "TIP")
                    self.log("3. Use --skip-timestamp option", "TIP")
                    self.log("4. Try a different output directory", "TIP")
                
                self.log(f"PyInstaller failed with code {process.returncode}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error running PyInstaller: {e}", "ERROR")
            return False
    
    def detect_console_mode(self, main_file: str) -> bool:
        """Detect if the application is GUI or console based"""
        # Check common GUI packages
        gui_packages = ['PyQt5', 'PySide6', 'tkinter', 'wx', 'kivy', 'pygame', 'pyglet']
        file_path = os.path.join(self.project_dir, main_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for GUI toolkit imports
            for package in gui_packages:
                if f"import {package}" in content or f"from {package}" in content:
                    self.log(f"Detected GUI application (using {package})", "INFO")
                    return False
                    
            # Look for stdin usage to determine if it needs console access
            stdin_patterns = ["input(", "sys.stdin", "raw_input("]
            for pattern in stdin_patterns:
                if pattern in content:
                    self.log(f"Detected stdin usage ({pattern}), recommending console mode", "INFO")
                    return True
        except:
            pass
            
        return True  # Default to console mode
    
    def detect_one_file_mode(self) -> bool:
        """Determine if one-file mode is appropriate"""
        # If there are many data files or resources, one-file might not be appropriate
        if len(self.data_files) + len(self.resource_files) > 10:
            self.log("Many data/resource files detected, using directory mode", "INFO")
            return False
            
        return True  # Default to one-file mode
    
    def save_config(self):
        """Save the build configuration to a file"""
        config = {
            "main_file": self.main_file,
            "console_mode": self.console_mode,
            "one_file": self.one_file,
            "icon_file": self.icon_file,
            "hidden_imports": list(self.hidden_imports),
            "clean_build": self.clean_build,
            "verbose": self.verbose,
            "bundle_level": self.bundle_level,
            "excluded_packages": self.excluded_packages,
            "optimize_level": self.optimize_level,
            "target_platform": self.target_platform,
            "app_name": self.app_name,
            "mt5_detection": self.mt5_detection,
            "mt5_path": self.mt5_path,
            "skip_timestamp": self.skip_timestamp,
            "alt_temp_dir": self.alt_temp_dir,
            "include_directories": self.include_directories,
            "excluded_directories": self.excluded_directories
        }
        
        config_file = os.path.join(self.project_dir, 'pyinstaller_config.json')
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        self.log(f"Saved configuration to {config_file}")
    
    def save_config_to_file(self, filename):
        """Save the build configuration to a specific file"""
        config = {
            "main_file": self.main_file,
            "console_mode": self.console_mode,
            "one_file": self.one_file,
            "icon_file": self.icon_file,
            "hidden_imports": list(self.hidden_imports),
            "clean_build": self.clean_build,
            "verbose": self.verbose,
            "bundle_level": self.bundle_level,
            "excluded_packages": self.excluded_packages,
            "optimize_level": self.optimize_level,
            "target_platform": self.target_platform,
            "app_name": self.app_name,
            "mt5_detection": self.mt5_detection,
            "mt5_path": self.mt5_path,
            "skip_timestamp": self.skip_timestamp,
            "alt_temp_dir": self.alt_temp_dir,
            "include_directories": self.include_directories,
            "excluded_directories": self.excluded_directories,
            "python_files": self.python_files,
            "data_files": self.data_files,
            "resource_files": self.resource_files,
            "binary_files": self.binary_files,
            "build_dir": self.build_dir,
            "dist_dir": self.dist_dir
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
            
        self.log(f"Saved configuration to {filename}")
    
    def load_config(self) -> bool:
        """Load build configuration from file if exists"""
        config_file = os.path.join(self.project_dir, 'pyinstaller_config.json')
        if not os.path.exists(config_file):
            return False
            
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            self.main_file = config.get("main_file", self.main_file)
            self.console_mode = config.get("console_mode", self.console_mode)
            self.one_file = config.get("one_file", self.one_file)
            self.icon_file = config.get("icon_file", self.icon_file)
            self.hidden_imports = set(config.get("hidden_imports", []))
            self.clean_build = config.get("clean_build", self.clean_build)
            self.verbose = config.get("verbose", self.verbose)
            self.bundle_level = config.get("bundle_level", self.bundle_level)
            self.excluded_packages = config.get("excluded_packages", self.excluded_packages)
            self.optimize_level = config.get("optimize_level", self.optimize_level)
            self.target_platform = config.get("target_platform", self.target_platform)
            self.app_name = config.get("app_name", self.app_name)
            self.mt5_detection = config.get("mt5_detection", self.mt5_detection)
            self.mt5_path = config.get("mt5_path", self.mt5_path)
            self.skip_timestamp = config.get("skip_timestamp", self.skip_timestamp)
            self.alt_temp_dir = config.get("alt_temp_dir", self.alt_temp_dir)
            self.include_directories = config.get("include_directories", self.include_directories)
            self.excluded_directories = config.get("excluded_directories", self.excluded_directories)
            
            self.log(f"Loaded configuration from {config_file}")
            return True
            
        except Exception as e:
            self.log(f"Error loading configuration: {e}", "ERROR")
            return False
            
    def load_config_from_file(self, filename):
        """Load build configuration from a specific file"""
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
                
            self.main_file = config.get("main_file", self.main_file)
            self.console_mode = config.get("console_mode", self.console_mode)
            self.one_file = config.get("one_file", self.one_file)
            self.icon_file = config.get("icon_file", self.icon_file)
            self.hidden_imports = set(config.get("hidden_imports", []))
            self.clean_build = config.get("clean_build", self.clean_build)
            self.verbose = config.get("verbose", self.verbose)
            self.bundle_level = config.get("bundle_level", self.bundle_level)
            self.excluded_packages = config.get("excluded_packages", self.excluded_packages)
            self.optimize_level = config.get("optimize_level", self.optimize_level)
            self.target_platform = config.get("target_platform", self.target_platform)
            self.app_name = config.get("app_name", self.app_name)
            self.mt5_detection = config.get("mt5_detection", self.mt5_detection)
            self.mt5_path = config.get("mt5_path", self.mt5_path)
            self.skip_timestamp = config.get("skip_timestamp", self.skip_timestamp)
            self.alt_temp_dir = config.get("alt_temp_dir", self.alt_temp_dir)
            self.include_directories = config.get("include_directories", self.include_directories)
            self.excluded_directories = config.get("excluded_directories", self.excluded_directories)
            
            # Optional file lists
            if "python_files" in config:
                self.python_files = config["python_files"]
            if "data_files" in config:
                self.data_files = config["data_files"]
            if "resource_files" in config:
                self.resource_files = config["resource_files"]
            if "binary_files" in config:
                self.binary_files = config["binary_files"]
            if "build_dir" in config:
                self.build_dir = config["build_dir"]
            if "dist_dir" in config:
                self.dist_dir = config["dist_dir"]
            
            self.log(f"Loaded configuration from {filename}")
            return True
            
        except Exception as e:
            self.log(f"Error loading configuration: {e}", "ERROR")
            raise
    
    def build(self):
        """Main build process"""
        self.log("Starting Smart PyInstaller Wrapper", "START")
        self.log(f"Project directory: {self.project_dir}")
        
        # Check PyInstaller installation
        if not self.check_pyinstaller():
            return False
        
        # Try to load saved configuration
        config_loaded = self.load_config()
        
        # Scan project files
        self.scan_project()
        
        # Detect main file if not provided
        if not self.main_file:
            self.main_file = self.detect_main_file()
            if not self.main_file:
                return False
        
        # Analyze dependencies
        self.detect_dependencies()
        
        # Find icon file
        if not self.icon_file:
            self.icon_file = self.detect_icon()
            if self.icon_file:
                self.log(f"Using icon file: {self.icon_file}")
            else:
                self.log("No icon file found or generated", "WARNING")
        
        # Determine console mode if not loaded from config
        if not config_loaded:
            self.console_mode = self.detect_console_mode(self.main_file)
            self.one_file = self.detect_one_file_mode()
        
        # Save configuration for future runs
        self.save_config()
        
        # Generate and run PyInstaller command
        cmd = self.generate_command(self.main_file)
        self.log(f"PyInstaller command: {' '.join(cmd)}", "DEBUG")
        success = self.run_command(cmd)
        
        if success:
            # Verify the build artifacts
            self.verify_build_artifacts()
        
        self.log("Build process completed", "END")
        return success

    def verify_build_artifacts(self):
        """Verify that the build artifacts were created correctly"""
        if self.app_name:
            exe_name = self.app_name
        else:
            exe_name = os.path.splitext(os.path.basename(self.main_file))[0]
            
        if platform.system() == "Windows":
            exe_path = os.path.join(self.dist_dir, exe_name, f"{exe_name}.exe") if not self.one_file else os.path.join(self.dist_dir, f"{exe_name}.exe")
        else:
            exe_path = os.path.join(self.dist_dir, exe_name, exe_name) if not self.one_file else os.path.join(self.dist_dir, exe_name)
            
        if os.path.exists(exe_path):
            self.log(f"Verified executable at: {exe_path}", "SUCCESS")
            
            # On Windows, check if the icon was applied
            if platform.system() == "Windows" and self.icon_file:
                self.log("Note: Icon may not be visible immediately in Windows Explorer.", "INFO")
                self.log("Windows caches icons, so you may need to:", "INFO")
                self.log("1. Refresh Explorer (F5)", "INFO")
                self.log("2. Try clearing the icon cache by restarting Explorer", "INFO")
                self.log("3. Ensure your .ico file is a valid Windows icon (must be .ico format)", "INFO")
                
                # Check if icon is in a format Windows can use
                if not self.icon_file.lower().endswith('.ico'):
                    self.log("WARNING: Your icon file doesn't have a .ico extension, which is required for Windows", "WARNING")
                    self.log("Convert your image to ICO format using an online converter or image editor", "TIP")
            
            return True
        else:
            self.log(f"Could not find expected executable at {exe_path}", "WARNING")
            # Look for the executable in other locations
            for root, _, files in os.walk(self.dist_dir):
                for file in files:
                    if file.endswith('.exe') or (not platform.system() == "Windows" and os.access(os.path.join(root, file), os.X_OK)):
                        self.log(f"Found possible executable at: {os.path.join(root, file)}", "INFO")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart PyInstaller Wrapper - Auto-detects project files and builds an executable')
    parser.add_argument('--main', help='Main Python file (entry point)')
    parser.add_argument('--dir', help='Project directory (defaults to current directory)')
    parser.add_argument('--onefile', action='store_true', help='Create a single executable file')
    parser.add_argument('--console', action='store_true', help='Force console mode')
    parser.add_argument('--windowed', action='store_true', help='Force windowed (GUI) mode')
    parser.add_argument('--icon', help='Icon file path')
    parser.add_argument('--clean', action='store_true', help='Clean build directories before building')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--nogui', action='store_true', help='Run in command-line mode without GUI')
    parser.add_argument('--skip-timestamp', action='store_true', help='Skip setting timestamp (helps with permission issues)')
    parser.add_argument('--output-dir', help='Custom output directory for the executable')
    parser.add_argument('--temp-dir', help='Custom temporary directory for build files')
    parser.add_argument('--include-dir', action='append', help='Include a directory with structure preserved (can be used multiple times)')
    parser.add_argument('--exclude-dir', action='append', help='Exclude a directory from the build (can be used multiple times)')
    
    args = parser.parse_args()
    
    # Initialize the builder
    builder = SmartExeBuilder(project_dir=args.dir, main_file=args.main)
    
    # Apply command line arguments
    if args.onefile:
        builder.one_file = True
    if args.console:
        builder.console_mode = True
    if args.windowed:
        builder.console_mode = False
    if args.icon:
        builder.icon_file = args.icon
    if args.clean:
        builder.clean_build = True
    if args.verbose:
        builder.verbose = True
    if args.skip_timestamp:
        builder.skip_timestamp = True
    if args.output_dir:
        builder.dist_dir = args.output_dir
    if args.temp_dir:
        builder.alt_temp_dir = args.temp_dir
    if args.include_dir:
        for directory in args.include_dir:
            builder.include_directory(directory)
    if args.exclude_dir:
        for directory in args.exclude_dir:
            builder.exclude_directory(directory)
    
    # If --nogui or any command-line options were provided, run in CLI mode
    if args.nogui or any([args.main, args.dir, args.onefile, args.console, args.windowed, args.icon, args.clean, args.verbose, args.skip_timestamp, args.output_dir, args.temp_dir, args.include_dir, args.exclude_dir]):
        # Start the build process
        builder.build()
    else:
        # Launch the GUI
        try:
            root = tk.Tk()
            app = BuilderUI(root, builder)
            root.mainloop()
        except Exception as e:
            print(f"Error launching GUI: {e}")
            print("Falling back to command-line mode...")
            builder.build()

if __name__ == "__main__":
    main() 