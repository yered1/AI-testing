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
            "agents",
            "infra",
            "scripts",
            "policies",
            "docs"
        ]
        
        optional_dirs = [
            "ui",
            "tests",
            "config",
            "templates"
        ]
        
        all_good = True
        
        for dir_name in required_dirs:
            dir_path = self.root_dir / dir_name
            exists = dir_path.exists()
            print_status(exists, f"Required directory: {dir_name}")
            if not exists:
                all_good = False
                self.results['failed'].append(f"Missing directory: {dir_name}")
            else:
                self.results['passed'].append(f"Directory exists: {dir_name}")
        
        for dir_name in optional_dirs:
            dir_path = self.root_dir / dir_name
            if dir_path.exists():
                print_status(True, f"Optional directory: {dir_name}")
            else:
                print_warning(f"Optional directory missing: {dir_name}")
                self.results['warnings'].append(f"Optional directory missing: {dir_name}")
        
        return all_good
    
    def check_key_files(self) -> bool:
        """Check for essential files"""
        print_header("Checking Key Files")
        
        essential_files = [
            "README.md",
            "infra/docker-compose.yml",
            "scripts/manage.sh",
            ".gitignore"
        ]
        
        config_files = [
            ".env.example",
            ".env"
        ]
        
        all_good = True
        
        for file_path in essential_files:
            full_path = self.root_dir / file_path
            exists = full_path.exists()
            print_status(exists, f"Essential file: {file_path}")
            if not exists:
                all_good = False
                self.results['failed'].append(f"Missing file: {file_path}")
            else:
                self.results['passed'].append(f"File exists: {file_path}")
        
        for file_path in config_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                print_status(True, f"Config file: {file_path}")
            else:
                print_warning(f"Config file missing: {file_path}")
                if file_path == ".env":
                    print_info("Create .env by copying: cp .env.example .env")
        
        return all_good
    
    def check_docker_setup(self) -> bool:
        """Verify Docker and Docker Compose are available"""
        print_header("Checking Docker Setup")
        
        all_good = True
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            docker_version = result.stdout.strip()
            print_status(True, f"Docker installed: {docker_version}")
            self.results['passed'].append("Docker is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_status(False, "Docker not found")
            self.results['failed'].append("Docker not installed")
            all_good = False
        
        # Check Docker Compose
        try:
            # Try docker compose (v2)
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True, check=True)
            compose_version = result.stdout.strip()
            print_status(True, f"Docker Compose v2: {compose_version}")
            self.results['passed'].append("Docker Compose v2 is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try docker-compose (v1)
                result = subprocess.run(['docker-compose', '--version'], 
                                      capture_output=True, text=True, check=True)
                compose_version = result.stdout.strip()
                print_status(True, f"Docker Compose v1: {compose_version}")
                self.results['passed'].append("Docker Compose v1 is installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print_status(False, "Docker Compose not found")
                self.results['failed'].append("Docker Compose not installed")
                all_good = False
        
        # Check if Docker daemon is running
        try:
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True, check=True)
            print_status(True, "Docker daemon is running")
            self.results['passed'].append("Docker daemon is running")
        except subprocess.CalledProcessError:
            print_status(False, "Docker daemon is not running")
            print_info("Start Docker daemon with: sudo systemctl start docker")
            self.results['failed'].append("Docker daemon not running")
            all_good = False
        
        return all_good
    
    def check_python_environment(self) -> bool:
        """Check Python version and required packages"""
        print_header("Checking Python Environment")
        
        all_good = True
        
        # Check Python version
        python_version = sys.version_info
        version_str = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
        
        if python_version.major == 3 and python_version.minor >= 9:
            print_status(True, f"Python version: {version_str} (>= 3.9 required)")
            self.results['passed'].append(f"Python {version_str}")
        else:
            print_status(False, f"Python version: {version_str} (>= 3.9 required)")
            self.results['failed'].append(f"Python version too old: {version_str}")
            all_good = False
        
        # Check for required Python packages
        required_packages = ['requests', 'pydantic', 'sqlalchemy', 'alembic']
        
        for package in required_packages:
            try:
                __import__(package)
                print_status(True, f"Python package: {package}")
            except ImportError:
                print_warning(f"Python package missing: {package}")
                self.results['warnings'].append(f"Missing package: {package}")
        
        return all_good
    
    def check_cleanup_results(self) -> bool:
        """Check if cleanup was successful"""
        print_header("Checking Cleanup Results")
        
        # Check for junk that should have been removed
        junk_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/.DS_Store",
            "**/scripts/*_v[0-9]*.sh"  # Old versioned scripts
        ]
        
        junk_found = []
        
        for pattern in junk_patterns:
            # Use glob to find files
            if "**" in pattern:
                found = list(self.root_dir.glob(pattern))
            else:
                found = list(self.root_dir.glob(pattern))
            
            if found and "archived_overlays" not in str(found[0]):
                junk_found.extend(found[:5])  # Limit to first 5 for display
        
        if not junk_found:
            print_status(True, "No junk files found")
            self.results['passed'].append("Cleanup successful")
            return True
        else:
            print_status(False, f"Found {len(junk_found)} junk files:")
            for junk_file in junk_found[:5]:
                print(f"    - {junk_file.relative_to(self.root_dir)}")
            if len(junk_found) > 5:
                print(f"    ... and {len(junk_found) - 5} more")
            self.results['warnings'].append(f"Found {len(junk_found)} junk files")
            return False
    
    def check_agent_structure(self) -> bool:
        """Check agent directories and structure"""
        print_header("Checking Agent Structure")
        
        agents_dir = self.root_dir / "agents"
        if not agents_dir.exists():
            print_status(False, "Agents directory not found")
            self.results['failed'].append("Agents directory missing")
            return False
        
        expected_agents = [
            "zap_agent",
            "nuclei_agent",
            "semgrep_agent"
        ]
        
        found_agents = []
        for agent in agents_dir.iterdir():
            if agent.is_dir() and not agent.name.startswith('.'):
                found_agents.append(agent.name)
        
        print_info(f"Found {len(found_agents)} agents:")
        for agent in found_agents:
            is_expected = agent in expected_agents
            if is_expected:
                print_status(True, f"Agent: {agent}")
                self.results['passed'].append(f"Agent found: {agent}")
            else:
                print_info(f"  Agent: {agent}")
        
        return len(found_agents) > 0
    
    def check_orchestrator_structure(self) -> bool:
        """Check orchestrator directory structure"""
        print_header("Checking Orchestrator Structure")
        
        orch_dir = self.root_dir / "orchestrator"
        if not orch_dir.exists():
            print_status(False, "Orchestrator directory not found")
            self.results['failed'].append("Orchestrator directory missing")
            return False
        
        required_components = [
            "app.py",
            "models",
            "routers",
            "alembic"
        ]
        
        all_good = True
        for component in required_components:
            component_path = orch_dir / component
            exists = component_path.exists()
            print_status(exists, f"Orchestrator component: {component}")
            if not exists:
                all_good = False
                self.results['failed'].append(f"Missing orchestrator component: {component}")
        
        # Check for agent_sdk
        sdk_path = orch_dir / "agent_sdk"
        if sdk_path.exists():
            print_status(True, "Agent SDK found")
            self.results['passed'].append("Agent SDK present")
        else:
            print_warning("Agent SDK not found (optional)")
        
        return all_good
    
    def test_docker_compose(self) -> bool:
        """Test if Docker Compose file is valid"""
        print_header("Testing Docker Compose Configuration")
        
        compose_file = self.root_dir / "infra" / "docker-compose.yml"
        
        if not compose_file.exists():
            print_status(False, "Docker Compose file not found")
            self.results['failed'].append("Docker Compose file missing")
            return False
        
        try:
            # Test config validity
            result = subprocess.run(
                ['docker', 'compose', '-f', str(compose_file), 'config'],
                capture_output=True, text=True, check=True
            )
            print_status(True, "Docker Compose configuration is valid")
            self.results['passed'].append("Docker Compose config valid")
            
            # Parse services
            result = subprocess.run(
                ['docker', 'compose', '-f', str(compose_file), 'config', '--services'],
                capture_output=True, text=True, check=True
            )
            services = result.stdout.strip().split('\n')
            print_info(f"Found {len(services)} services: {', '.join(services)}")
            
            return True
        except subprocess.CalledProcessError as e:
            print_status(False, "Docker Compose configuration is invalid")
            print_info(f"Error: {e.stderr}")
            self.results['failed'].append("Docker Compose config invalid")
            return False
    
    def generate_report(self):
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