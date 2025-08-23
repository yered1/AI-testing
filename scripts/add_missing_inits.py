#!/usr/bin/env python3
# Destination: patches/v2.0.0/scripts/add_missing_inits.py
# Rationale: Python packages require __init__.py files for proper module recognition
# This script scans for Python directories and adds missing __init__.py files

import os
import sys
from pathlib import Path
from typing import List, Set

def find_python_dirs(root_path: Path, exclude_dirs: Set[str]) -> List[Path]:
    """Find all directories containing Python files that should have __init__.py."""
    python_dirs = []
    
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        root_path_obj = Path(root)
        
        # Check if directory contains Python files
        has_py_files = any(f.endswith('.py') for f in files)
        
        if has_py_files:
            # Check if __init__.py is missing
            init_file = root_path_obj / '__init__.py'
            if not init_file.exists():
                python_dirs.append(root_path_obj)
    
    return python_dirs

def create_init_file(dir_path: Path, dry_run: bool = False) -> bool:
    """Create an __init__.py file in the given directory."""
    init_file = dir_path / '__init__.py'
    
    if init_file.exists():
        return False
    
    if dry_run:
        print(f"  [DRY RUN] Would create: {init_file}")
        return True
    
    try:
        # Create with a minimal docstring
        module_name = dir_path.name
        content = f'''"""
{module_name} module.

This file makes the directory a Python package.
"""
'''
        init_file.write_text(content)
        print(f"  ✅ Created: {init_file}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to create {init_file}: {e}")
        return False

def main():
    """Main function to add missing __init__.py files."""
    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    # Set root directory (current directory or specified)
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        root_dir = Path(sys.argv[1])
    else:
        root_dir = Path.cwd()
    
    if not root_dir.exists():
        print(f"Error: Directory {root_dir} does not exist")
        sys.exit(1)
    
    print(f"🔍 Scanning for Python packages in: {root_dir}")
    if dry_run:
        print("  (DRY RUN MODE - No files will be created)")
    print()
    
    # Directories to exclude from scanning
    exclude_dirs = {
        '__pycache__', '.git', '.venv', 'venv', 'env', 
        'node_modules', '.tox', 'dist', 'build', '.pytest_cache',
        'htmlcov', '.mypy_cache', '.ruff_cache', '__MACOSX'
    }
    
    # Find directories needing __init__.py
    python_dirs = find_python_dirs(root_dir, exclude_dirs)
    
    if not python_dirs:
        print("✅ All Python packages already have __init__.py files!")
        return
    
    print(f"📦 Found {len(python_dirs)} directories needing __init__.py files:")
    print()
    
    # Sort for consistent output
    python_dirs.sort()
    
    # Process each directory
    created_count = 0
    for dir_path in python_dirs:
        rel_path = dir_path.relative_to(root_dir)
        
        if verbose:
            print(f"Processing: {rel_path}")
        
        if create_init_file(dir_path, dry_run):
            created_count += 1
    
    print()
    if dry_run:
        print(f"📊 Would create {created_count} __init__.py files")
        print("   Run without --dry-run to actually create the files")
    else:
        print(f"✅ Successfully created {created_count} __init__.py files")

if __name__ == "__main__":
    # Print usage if --help is requested
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""
Usage: python add_missing_inits.py [directory] [options]

Add missing __init__.py files to Python packages.

Arguments:
  directory     Root directory to scan (default: current directory)

Options:
  --dry-run     Show what would be done without making changes
  --verbose,-v  Show detailed processing information
  --help,-h     Show this help message

Examples:
  python add_missing_inits.py                    # Scan current directory
  python add_missing_inits.py ./orchestrator     # Scan specific directory
  python add_missing_inits.py --dry-run          # Preview changes
""")
        sys.exit(0)
    
    main()