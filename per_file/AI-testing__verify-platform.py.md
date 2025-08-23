# File: AI-testing/verify-platform.py

- Size: 15681 bytes
- Kind: text
- SHA256: e77e179c6e62958d16914de4a568b379a74f3849ffda5af821bd5ed293de3d77

## Python Imports

```
json, os, pathlib, subprocess, sys, time, typing
```

## Head (first 60 lines)

```
#!/usr/bin/env python3
"""
AI-Testing Platform Verification Script
Checks the health and completeness of the platform after cleanup
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import time

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(message: str):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{message}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

def print_status(status: bool, message: str):
    """Print status with color coding"""
    if status:
        print(f"  {Colors.GREEN}✓{Colors.RESET} {message}")
    else:
        print(f"  {Colors.RED}✗{Colors.RESET} {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"  {Colors.YELLOW}⚠{Colors.RESET} {message}")

def print_info(message: str):
    """Print info message"""
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {message}")

class PlatformVerifier:
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        self.root_dir = Path.cwd()
    
    def check_directory_structure(self) -> bool:
        """Verify the expected directory structure exists"""
        print_header("Checking Directory Structure")
        
        required_dirs = [
            "orchestrator",
```

## Tail (last 60 lines)

```
        """Generate final verification report"""
        print_header("Verification Report")
        
        total_passed = len(self.results['passed'])
        total_failed = len(self.results['failed'])
        total_warnings = len(self.results['warnings'])
        
        print(f"{Colors.GREEN}Passed: {total_passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {total_failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {total_warnings}{Colors.RESET}")
        
        if total_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Platform verification PASSED!{Colors.RESET}")
            print("The platform is ready to use.")
            print("\nNext steps:")
            print("1. Copy environment file: cp .env.example .env")
            print("2. Start services: ./scripts/manage.sh full-start")
            print("3. Access UI: http://localhost:8080/ui")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ Platform verification FAILED{Colors.RESET}")
            print("\nFailed checks:")
            for failure in self.results['failed']:
                print(f"  - {failure}")
            print("\nPlease address these issues before proceeding.")
        
        if total_warnings > 0:
            print(f"\n{Colors.YELLOW}Warnings:{Colors.RESET}")
            for warning in self.results['warnings'][:5]:
                print(f"  - {warning}")
            if len(self.results['warnings']) > 5:
                print(f"  ... and {len(self.results['warnings']) - 5} more")
    
    def run(self):
        """Run all verification checks"""
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("=" * 60)
        print("AI-Testing Platform Verification")
        print("=" * 60)
        print(f"{Colors.RESET}")
        
        # Run all checks
        self.check_directory_structure()
        self.check_key_files()
        self.check_docker_setup()
        self.check_python_environment()
        self.check_cleanup_results()
        self.check_agent_structure()
        self.check_orchestrator_structure()
        self.test_docker_compose()
        
        # Generate report
        self.generate_report()

def main():
    """Main entry point"""
    verifier = PlatformVerifier()
    verifier.run()

if __name__ == "__main__":
    main()
```

