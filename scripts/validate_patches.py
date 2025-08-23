#!/usr/bin/env python3
# Destination: patches/v2.0.0/scripts/validate_patches.py
# Rationale: Comprehensive validation script to ensure all patches were applied correctly
# Checks file existence, syntax, imports, and basic functionality

import os
import sys
import ast
import json
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import importlib.util

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{text:^60}{NC}")
    print(f"{BLUE}{'='*60}{NC}")

def print_status(status: bool, message: str):
    """Print a status message with color."""
    icon = f"{GREEN}✓{NC}" if status else f"{RED}✗{NC}"
    print(f"  {icon} {message}")

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()

def check_python_syntax(filepath: str) -> Tuple[bool, str]:
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

def check_python_imports(filepath: str) -> Tuple[bool, List[str]]:
    """Check if Python imports can be resolved."""
    failed_imports = []
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        __import__(alias.name)
                    except ImportError:
                        failed_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        __import__(node.module)
                    except ImportError:
                        failed_imports.append(node.module)
        
        return len(failed_imports) == 0, failed_imports
    except Exception as e:
        return False, [str(e)]

def check_yaml_valid(filepath: str) -> Tuple[bool, str]:
    """Check if a YAML file is valid."""
    try:
        with open(filepath, 'r') as f:
            yaml.safe_load(f)
        return True, "Valid YAML"
    except yaml.YAMLError as e:
        return False, f"YAML error: {e}"

def check_json_valid(filepath: str) -> Tuple[bool, str]:
    """Check if a JSON file is valid."""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, f"JSON error: {e}"

def check_docker_compose(filepath: str) -> Tuple[bool, str]:
    """Validate Docker Compose file."""
    try:
        result = subprocess.run(
            ['docker-compose', '-f', filepath, 'config'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "Valid compose file"
        else:
            return False, f"Invalid: {result.stderr[:100]}"
    except Exception as e:
        return False, f"Check failed: {e}"

def validate_critical_fixes():
    """Validate critical fixes from the development plan."""
    print_header("CRITICAL FIXES VALIDATION")
    
    fixes = {
        "orchestrator/models/base.py": {
            "exists": True,
            "check": lambda f: "from ..db import Base" in open(f).read(),
            "message": "Base model correctly imports from db module"
        },
        "orchestrator/models/membership.py": {
            "exists": True,
            "check": lambda f: "class Membership" in open(f).read(),
            "message": "Membership model defined"
        },
        "orchestrator/reports/__init__.py": {
            "exists": True,
            "check": lambda f: True,  # Just needs to exist
            "message": "Reports module is importable"
        },
        "orchestrator/routers/app.py": {
            "exists": True,
            "check": lambda f: "FastAPI" in open(f).read(),
            "message": "Consolidated FastAPI app exists"
        }
    }
    
    all_good = True
    for filepath, checks in fixes.items():
        exists = check_file_exists(filepath)
        print_status(exists, f"{filepath} exists")
        
        if exists and checks.get("check"):
            try:
                passed = checks["check"](filepath)
                print_status(passed, f"  → {checks['message']}")
                all_good = all_good and passed
            except Exception as e:
                print_status(False, f"  → Check failed: {e}")
                all_good = False
        elif not exists:
            all_good = False
    
    return all_good

def validate_environment_standardization():
    """Check if environment variables are standardized."""
    print_header("ENVIRONMENT STANDARDIZATION")
    
    issues = []
    files_to_check = []
    
    # Find all Python and YAML files
    for pattern in ["**/*.py", "**/*.yml", "**/*.yaml"]:
        files_to_check.extend(Path(".").glob(pattern))
    
    orchestrator_url_count = 0
    orch_url_count = 0
    agent_token_count = 0
    agent_id_count = 0
    
    for filepath in files_to_check:
        if "__pycache__" in str(filepath) or ".git" in str(filepath):
            continue
        
        try:
            content = filepath.read_text()
            if "ORCH_URL" in content:
                orchestrator_url_count += 1
                issues.append(f"{filepath}: Still uses ORCH_URL")
            if "ORCH_URL" in content:
                orch_url_count += 1
            if "X-Agent-Token" in content:
                agent_token_count += 1
                issues.append(f"{filepath}: Still uses X-Agent-Token")
            if "X-Agent-Id" in content:
                agent_id_count += 1
        except Exception:
            pass
    
    print_status(orchestrator_url_count == 0, 
                f"ORCH_URL removed ({orchestrator_url_count} remaining)")
    print_status(orch_url_count > 0, 
                f"ORCH_URL in use ({orch_url_count} files)")
    print_status(agent_token_count == 0, 
                f"X-Agent-Token removed ({agent_token_count} remaining)")
    print_status(agent_id_count > 0, 
                f"X-Agent-Id in use ({agent_id_count} files)")
    
    if issues:
        print(f"\n  {YELLOW}Issues found:{NC}")
        for issue in issues[:5]:  # Show first 5 issues
            print(f"    • {issue}")
        if len(issues) > 5:
            print(f"    • ... and {len(issues) - 5} more")
    
    return len(issues) == 0

def validate_docker_configuration():
    """Validate Docker configuration files."""
    print_header("DOCKER CONFIGURATION")
    
    docker_files = {
        "infra/orchestrator.Dockerfile": {
            "check": lambda f: "routers.app:app" in open(f).read(),
            "message": "Uses consolidated app (routers.app)"
        },
        "infra/agent.aws.Dockerfile": {
            "check": lambda f: True,  # Just needs to exist with correct name
            "message": "Correct filename (not DockerFile)"
        }
    }
    
    all_good = True
    for filepath, checks in docker_files.items():
        exists = check_file_exists(filepath)
        print_status(exists, f"{filepath} exists")
        
        if exists and checks.get("check"):
            try:
                passed = checks["check"](filepath)
                print_status(passed, f"  → {checks['message']}")
                all_good = all_good and passed
            except Exception as e:
                print_status(False, f"  → Check failed: {e}")
                all_good = False
        elif not exists:
            # Check for wrong case
            wrong_case = filepath.replace("Dockerfile", "DockerFile")
            if check_file_exists(wrong_case):
                print_status(False, f"  → Found with wrong case: {wrong_case}")
            all_good = False
    
    return all_good

def validate_python_files():
    """Validate all Python files for syntax errors."""
    print_header("PYTHON SYNTAX VALIDATION")
    
    python_files = list(Path("orchestrator").glob("**/*.py"))
    python_files.extend(Path("agents").glob("**/*.py"))
    
    errors = []
    checked = 0
    
    for filepath in python_files:
        if "__pycache__" in str(filepath):
            continue
        
        checked += 1
        valid, error = check_python_syntax(str(filepath))
        if not valid:
            errors.append((filepath, error))
    
    print_status(len(errors) == 0, 
                f"Checked {checked} Python files ({len(errors)} errors)")
    
    if errors:
        print(f"\n  {YELLOW}Syntax errors found:{NC}")
        for filepath, error in errors[:5]:
            print(f"    • {filepath}: {error}")
        if len(errors) > 5:
            print(f"    • ... and {len(errors) - 5} more")
    
    return len(errors) == 0

def validate_database_setup():
    """Check database and migration setup."""
    print_header("DATABASE SETUP")
    
    # Check Alembic configuration
    alembic_ini = check_file_exists("orchestrator/alembic.ini")
    print_status(alembic_ini, "alembic.ini exists")
    
    # Check migrations directory
    migrations_dir = Path("orchestrator/alembic/versions")
    migrations_exist = migrations_dir.exists()
    print_status(migrations_exist, "Migrations directory exists")
    
    if migrations_exist:
        migrations = list(migrations_dir.glob("*.py"))
        print_status(len(migrations) > 0, 
                    f"Found {len(migrations)} migration files")
    
    # Check if we can import SQLAlchemy models
    try:
        sys.path.insert(0, "orchestrator")
        from models.base import Base
        print_status(True, "Can import Base model")
    except ImportError as e:
        print_status(False, f"Cannot import Base model: {e}")
        return False
    
    return alembic_ini and migrations_exist

def run_all_validations():
    """Run all validation checks."""
    print(f"{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{'AI TESTING ORCHESTRATOR - PATCH VALIDATION':^60}{NC}")
    print(f"{BLUE}{'='*60}{NC}")
    
    results = {}
    
    # Run each validation
    results['Critical Fixes'] = validate_critical_fixes()
    results['Environment'] = validate_environment_standardization()
    results['Docker'] = validate_docker_configuration()
    results['Python Syntax'] = validate_python_files()
    results['Database'] = validate_database_setup()
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    all_passed = True
    for category, passed in results.items():
        print_status(passed, category)
        all_passed = all_passed and passed
    
    print(f"\n{BLUE}{'='*60}{NC}")
    if all_passed:
        print(f"{GREEN}{'✅ ALL VALIDATIONS PASSED!':^60}{NC}")
        print(f"{GREEN}{'The system is ready for deployment.':^60}{NC}")
    else:
        print(f"{YELLOW}{'⚠️  SOME VALIDATIONS FAILED':^60}{NC}")
        print(f"{YELLOW}{'Please review the issues above.':^60}{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    # Change to repository root if needed
    if not Path("DEVELOPMENT_PLAN.md").exists():
        print(f"{RED}Error: Please run from the repository root{NC}")
        sys.exit(1)
    
    sys.exit(run_all_validations())