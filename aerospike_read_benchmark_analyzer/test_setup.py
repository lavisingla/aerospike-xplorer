#!/usr/bin/env python3
"""
Test script to verify that the Aerospike Read Benchmark Analysis tools are set up correctly.
This script checks if all required packages are installed and if the scripts are executable.
"""

import sys
import os
import importlib
import subprocess

def check_package(package_name):
    """Check if a Python package is installed."""
    try:
        importlib.import_module(package_name)
        print(f"✓ {package_name} is installed")
        return True
    except ImportError:
        print(f"✗ {package_name} is NOT installed")
        return False

def check_script(script_path):
    """Check if a script exists and is executable."""
    if not os.path.exists(script_path):
        print(f"✗ {script_path} does NOT exist")
        return False
    
    if not os.access(script_path, os.X_OK):
        print(f"✗ {script_path} is NOT executable")
        return False
    
    print(f"✓ {script_path} exists and is executable")
    return True

def main():
    """Main function to run the tests."""
    print("\n" + "="*60)
    print("Aerospike Read Benchmark Analysis - Setup Test")
    print("="*60)
    
    # Check required packages
    print("\nChecking required packages:")
    packages = ['pandas', 'numpy', 'matplotlib', 'seaborn', 'jinja2']
    all_packages_installed = all(check_package(pkg) for pkg in packages)
    
    # Check scripts
    print("\nChecking scripts:")
    scripts = [
        'extract_benchmark_data.py',
        'visualize_benchmark_data.py',
        'generate_benchmark_report.py',
        'analyze_benchmark.py',
        'example.sh'
    ]
    all_scripts_ok = all(check_script(script) for script in scripts)
    
    # Check directory structure
    print("\nChecking directory structure:")
    directories = ['hdr_stats', 'read_latency_results']
    all_dirs_ok = True
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"✗ {directory} directory does NOT exist")
            all_dirs_ok = False
        elif not os.path.isdir(directory):
            print(f"✗ {directory} is NOT a directory")
            all_dirs_ok = False
        else:
            print(f"✓ {directory} directory exists")
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary:")
    print("="*60)
    
    if all_packages_installed:
        print("✓ All required packages are installed")
    else:
        print("✗ Some required packages are missing")
        print("  Run: pip install -r requirements.txt")
    
    if all_scripts_ok:
        print("✓ All scripts are present and executable")
    else:
        print("✗ Some scripts are missing or not executable")
        print("  Run: chmod +x *.py example.sh")
    
    if all_dirs_ok:
        print("✓ Directory structure is correct")
    else:
        print("✗ Directory structure is incorrect")
        print("  Make sure 'hdr_stats' and 'read_latency_results' directories exist")
    
    # Final verdict
    if all_packages_installed and all_scripts_ok and all_dirs_ok:
        print("\n✓ All tests passed! The setup is correct.")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
