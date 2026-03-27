#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTS Python Installation Helper

Checks for required dependencies and provides installation instructions.
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"✗ Python 3.7+ required (found {version.major}.{version.minor})")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_module(module_name, import_name=None):
    """Check if a Python module is installed"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        print(f"✓ {module_name}")
        return True
    except ImportError:
        print(f"✗ {module_name} (install with: pip install {module_name})")
        return False


def check_command(command):
    """Check if a command is available in PATH"""
    try:
        subprocess.run([command, '--version'], capture_output=True, timeout=2, check=False)
        print(f"✓ {command}")
        return True
    except FileNotFoundError:
        print(f"✗ {command}")
        return False


def main():
    print("HTS Python System - Dependency Check\n")
    print("=" * 50)
    
    print("\nPython Version:")
    python_ok = check_python_version()
    
    print("\nRequired Python Packages:")
    numpy_ok = check_module('numpy')
    scipy_ok = check_module('scipy')
    pysptk_ok = check_module('pysptk')
    
    print("\nOptional Python Packages:")
    pylstraight_ok = check_module('pylstraight', 'pylstraight')
    check_module('matplotlib')
    
    print("\nExternal Tools:")
    hts_ok = check_command('HGenASCIIData')  # HTS tool
    
    print("\n" + "=" * 50)
    
    # Summary
    required_ok = python_ok and numpy_ok and scipy_ok and pysptk_ok
    
    if required_ok:
        print("\n✓ All required packages installed!")
        if not hts_ok:
            print("\n⚠ Note: HTS toolkit not found")
            print("  Install from: http://speech.sys.i.is.tohoku.ac.jp/hts/")
    else:
        print("\n✗ Some required packages are missing.")
        print("\nQuick install:")
        print("  pip install numpy scipy pysptk")
    
    return 0 if required_ok else 1


if __name__ == '__main__':
    sys.exit(main())
