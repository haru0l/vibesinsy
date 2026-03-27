#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTS Training Utilities

This module provides utility functions for the HTS training script.
"""

import os
import subprocess
import struct
from pathlib import Path


def read_binary_file(filepath, dtype='f', count=-1):
    """
    Read binary file data
    
    Args:
        filepath: Path to binary file
        dtype: Data type ('f' for float, 'd' for double, 'i' for int)
        count: Number of elements to read (-1 for all)
    
    Returns:
        List of values
    """
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        if dtype == 'f':
            format_char = '<f'  # little-endian float
        elif dtype == 'd':
            format_char = '<d'  # little-endian double
        elif dtype == 'i':
            format_char = '<i'  # little-endian int
        else:
            format_char = '<f'
        
        size = struct.calcsize(format_char)
        num_elements = len(data) // size
        
        if count > 0:
            num_elements = min(num_elements, count)
        
        values = []
        for i in range(num_elements):
            value, = struct.unpack_from(format_char, data, i * size)
            values.append(value)
        
        return values
    except Exception as e:
        print(f"Error reading binary file {filepath}: {e}")
        return []


def write_binary_file(filepath, data, dtype='f'):
    """
    Write binary file data
    
    Args:
        filepath: Path to output file
        data: List of values to write
        dtype: Data type ('f' for float, 'd' for double, 'i' for int)
    """
    try:
        if dtype == 'f':
            format_char = '<f'  # little-endian float
        elif dtype == 'd':
            format_char = '<d'  # little-endian double
        elif dtype == 'i':
            format_char = '<i'  # little-endian int
        else:
            format_char = '<f'
        
        with open(filepath, 'wb') as f:
            for value in data:
                f.write(struct.pack(format_char, value))
    except Exception as e:
        print(f"Error writing binary file {filepath}: {e}")


def execute_command(cmd, shell=True, verbose=False):
    """
    Execute a shell command
    
    Args:
        cmd: Command string or list
        shell: Use shell execution (default: True)
        verbose: Print command before executing (default: False)
    
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    if verbose:
        print(f"Executing: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        print(f"Error executing command: {e}")
        return -1, "", str(e)


def create_directories(base_path, dirs):
    """
    Create multiple directories
    
    Args:
        base_path: Base directory path
        dirs: List of subdirectory names
    """
    for dir_name in dirs:
        if base_path:
            full_path = os.path.join(base_path, dir_name)
        else:
            full_path = dir_name
        
        Path(full_path).mkdir(parents=True, exist_ok=True)


def get_files_with_extension(directory, extension):
    """
    Get all files with specific extension in directory
    
    Args:
        directory: Directory path
        extension: File extension (e.g., '.lab', '.cmp')
    
    Returns:
        List of file paths
    """
    files = []
    try:
        for file_path in Path(directory).glob(f'*{extension}'):
            if file_path.is_file():
                files.append(str(file_path))
    except Exception as e:
        print(f"Error listing files in {directory}: {e}")
    
    return sorted(files)


def read_label_file(filepath):
    """
    Read HTS label file
    
    Args:
        filepath: Path to label file
    
    Returns:
        List of tuples (start_time, end_time, label)
    """
    labels = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(maxsplit=2)
                if len(parts) >= 3:
                    start = int(parts[0])
                    end = int(parts[1])
                    label = parts[2]
                    labels.append((start, end, label))
    except Exception as e:
        print(f"Error reading label file {filepath}: {e}")
    
    return labels


def write_label_file(filepath, labels):
    """
    Write HTS label file
    
    Args:
        filepath: Path to output file
        labels: List of tuples (start_time, end_time, label)
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for start, end, label in labels:
                f.write(f"{start} {end} {label}\n")
    except Exception as e:
        print(f"Error writing label file {filepath}: {e}")


def read_scp_file(filepath):
    """
    Read SCP (Script) file
    
    Args:
        filepath: Path to SCP file
    
    Returns:
        List of file paths
    """
    files = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    files.append(line)
    except Exception as e:
        print(f"Error reading SCP file {filepath}: {e}")
    
    return files


def write_scp_file(filepath, files):
    """
    Write SCP (Script) file
    
    Args:
        filepath: Path to output file
        files: List of file paths
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for file_path in files:
                f.write(f"{file_path}\n")
    except Exception as e:
        print(f"Error writing SCP file {filepath}: {e}")


def read_list_file(filepath):
    """
    Read model list file
    
    Args:
        filepath: Path to list file
    
    Returns:
        List of model names
    """
    models = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    models.append(line)
    except Exception as e:
        print(f"Error reading list file {filepath}: {e}")
    
    return models


def write_list_file(filepath, models):
    """
    Write model list file
    
    Args:
        filepath: Path to output file
        models: List of model names
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for model in models:
                f.write(f"{model}\n")
    except Exception as e:
        print(f"Error writing list file {filepath}: {e}")


def get_file_size(filepath):
    """
    Get file size in bytes
    
    Args:
        filepath: Path to file
    
    Returns:
        File size in bytes, or 0 if file doesn't exist
    """
    try:
        return os.path.getsize(filepath)
    except (OSError, FileNotFoundError):
        return 0


def remove_file(filepath):
    """
    Remove a file
    
    Args:
        filepath: Path to file
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error removing file {filepath}: {e}")


def remove_files(pattern_or_list):
    """
    Remove files matching pattern or in list
    
    Args:
        pattern_or_list: Glob pattern or list of file paths
    """
    if isinstance(pattern_or_list, str):
        # Glob pattern
        for file_path in Path('.').glob(pattern_or_list):
            remove_file(str(file_path))
    else:
        # List of files
        for file_path in pattern_or_list:
            remove_file(file_path)


def copy_file(src, dst):
    """
    Copy a file
    
    Args:
        src: Source file path
        dst: Destination file path
    """
    try:
        import shutil
        shutil.copy2(src, dst)
    except Exception as e:
        print(f"Error copying file from {src} to {dst}: {e}")


def append_file(src, dst):
    """
    Append contents of source file to destination file
    
    Args:
        src: Source file path
        dst: Destination file path
    """
    try:
        with open(src, 'r', encoding='utf-8', errors='ignore') as f_src:
            with open(dst, 'a', encoding='utf-8') as f_dst:
                f_dst.write(f_src.read())
    except Exception as e:
        print(f"Error appending file {src} to {dst}: {e}")


def file_size_matches(filepath, expected_size):
    """
    Check if file size matches expected size
    
    Args:
        filepath: Path to file
        expected_size: Expected file size in bytes
    
    Returns:
        True if sizes match, False otherwise
    """
    return get_file_size(filepath) == expected_size


def find_files_recursive(directory, pattern='*'):
    """
    Find all files matching pattern recursively
    
    Args:
        directory: Root directory to search
        pattern: Glob pattern to match
    
    Returns:
        List of matching file paths
    """
    files = []
    try:
        for file_path in Path(directory).rglob(pattern):
            if file_path.is_file():
                files.append(str(file_path))
    except Exception as e:
        print(f"Error searching directory {directory}: {e}")
    
    return sorted(files)


if __name__ == '__main__':
    # Test utilities
    print("HTS Training Utilities loaded successfully")
    
    # Example: Read binary file
    # data = read_binary_file('test.cmp', dtype='f')
    
    # Example: Read label file
    # labels = read_label_file('test.lab')
