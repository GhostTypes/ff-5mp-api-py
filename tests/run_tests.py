"""
Test runner for FlashForge Python API.

This module provides a simple way to run all tests for the FlashForge API.
Supports both uv and traditional Python environments.
"""
import shutil
import subprocess
import sys
from pathlib import Path


def get_python_runner():
    """
    Determine the best Python runner (uv or direct python).
    
    Returns:
        List of command components to run Python
    """
    # Check if we're in a uv project and uv is available
    if shutil.which('uv') and (Path.cwd() / 'pyproject.toml').exists():
        return ['uv', 'run', 'python']
    else:
        return [sys.executable]


def run_tests(verbose: bool = True, coverage: bool = False):
    """
    Run all tests for the FlashForge Python API.
    
    Args:
        verbose: If True, run tests in verbose mode
        coverage: If True, run tests with coverage reporting
    """
    project_root = Path(__file__).parent.parent
    test_dir = project_root / "tests"

    # Get the appropriate Python runner
    python_cmd = get_python_runner()

    # Build pytest command
    cmd = python_cmd + ["-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=flashforge", "--cov-report=html", "--cov-report=term"])

    # Add test directory
    cmd.append(str(test_dir))

    print(f"[*] Running tests with: {' '.join(cmd)}")
    print("-" * 50)

    # Run tests
    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        print("\n[SUCCESS] All tests passed!")
        if coverage:
            coverage_dir = project_root / "htmlcov"
            print(f"[*] Coverage report available at: {coverage_dir / 'index.html'}")
    else:
        print("\n[ERROR] Some tests failed!")
        sys.exit(result.returncode)


def run_discovery_tests():
    """Run only discovery tests."""
    project_root = Path(__file__).parent.parent
    test_file = project_root / "tests" / "test_discovery.py"
    python_cmd = get_python_runner()

    cmd = python_cmd + ["-m", "pytest", "-v", str(test_file)]

    print("[*] Running discovery tests...")
    print("-" * 35)

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def run_parser_tests():
    """Run only parser tests."""
    project_root = Path(__file__).parent.parent
    test_file = project_root / "tests" / "test_parsers.py"
    python_cmd = get_python_runner()

    cmd = python_cmd + ["-m", "pytest", "-v", str(test_file)]

    print("[*] Running parser tests...")
    print("-" * 30)

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def run_linting():
    """Run code quality checks."""
    project_root = Path(__file__).parent.parent
    python_cmd = get_python_runner()

    print("[*] Running code quality checks...")
    print("-" * 40)

    # Run black
    print("[*] Checking code formatting with black...")
    black_cmd = python_cmd + ["-m", "black", "--check", "flashforge/", "tests/", "examples/"]
    black_result = subprocess.run(black_cmd, cwd=project_root)

    # Run ruff
    print("[*] Checking style and imports with ruff...")
    ruff_cmd = python_cmd + ["-m", "ruff", "check", "flashforge/", "tests/", "examples/"]
    ruff_result = subprocess.run(ruff_cmd, cwd=project_root)

    # Run mypy
    print("[*] Checking types with mypy...")
    mypy_cmd = python_cmd + ["-m", "mypy", "flashforge/"]
    mypy_result = subprocess.run(mypy_cmd, cwd=project_root)

    if black_result.returncode == 0 and ruff_result.returncode == 0 and mypy_result.returncode == 0:
        print("[SUCCESS] All quality checks passed!")
        return True
    else:
        print("[ERROR] Some quality checks failed!")
        return False


def format_code():
    """Format code with black and fix issues with ruff."""
    project_root = Path(__file__).parent.parent
    python_cmd = get_python_runner()

    print("[*] Formatting and fixing code...")
    print("-" * 40)

    # Run black for formatting
    print("[*] Formatting code with black...")
    black_cmd = python_cmd + ["-m", "black", "flashforge/", "tests/", "examples/"]
    black_result = subprocess.run(black_cmd, cwd=project_root)

    # Run ruff to fix auto-fixable issues
    print("[*] Auto-fixing issues with ruff...")
    ruff_cmd = python_cmd + ["-m", "ruff", "check", "--fix", "flashforge/", "tests/", "examples/"]
    ruff_result = subprocess.run(ruff_cmd, cwd=project_root)

    if black_result.returncode == 0 and ruff_result.returncode == 0:
        print("[SUCCESS] Code formatting and fixing complete!")
    else:
        print("[ERROR] Some formatting/fixing operations failed!")

    return black_result.returncode == 0 and ruff_result.returncode == 0


def show_environment_info():
    """Show information about the current environment."""
    project_root = Path(__file__).parent.parent
    python_cmd = get_python_runner()

    print("[*] Environment Information")
    print("=" * 30)

    # Show Python version
    version_cmd = python_cmd + ["-c", "import sys; print(f'Python {sys.version}')"]
    subprocess.run(version_cmd, cwd=project_root)

    # Show if we're using uv
    if 'uv' in python_cmd:
        print("[*] Using uv package manager")
        if shutil.which('uv'):
            uv_version = subprocess.run(['uv', '--version'], capture_output=True, text=True)
            if uv_version.returncode == 0:
                print(f"   {uv_version.stdout.strip()}")
    else:
        print("[*] Using standard Python")

    # Show project info
    print(f"[*] Project root: {project_root}")

    # Try to import flashforge to check installation
    import_cmd = python_cmd + ["-c", "import flashforge; print('FlashForge API installed successfully')"]
    import_result = subprocess.run(import_cmd, cwd=project_root, capture_output=True, text=True)

    if import_result.returncode == 0:
        print("[SUCCESS] FlashForge API is importable")
    else:
        print("[ERROR] FlashForge API import failed")
        if import_result.stderr:
            print(f"   Error: {import_result.stderr.strip()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FlashForge API Test Runner")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--quiet", action="store_true", help="Run tests in quiet mode")
    parser.add_argument("--discovery", action="store_true", help="Run only discovery tests")
    parser.add_argument("--parsers", action="store_true", help="Run only parser tests")
    parser.add_argument("--lint", action="store_true", help="Run code quality checks")
    parser.add_argument("--format", action="store_true", help="Format code with black")
    parser.add_argument("--env-info", action="store_true", help="Show environment information")

    args = parser.parse_args()

    if args.env_info:
        show_environment_info()
    elif args.discovery:
        success = run_discovery_tests()
        sys.exit(0 if success else 1)
    elif args.parsers:
        success = run_parser_tests()
        sys.exit(0 if success else 1)
    elif args.lint:
        success = run_linting()
        sys.exit(0 if success else 1)
    elif args.format:
        success = format_code()
        sys.exit(0 if success else 1)
    else:
        run_tests(verbose=not args.quiet, coverage=args.coverage)
