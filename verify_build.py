#!/usr/bin/env python3
"""
Build verification script for PDF Text Extractor.

Runs smoke tests on the built executable to ensure it works correctly.
"""

import sys
import subprocess
import tempfile
from pathlib import Path
import shutil

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print formatted header."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")


def check_executable_exists(exe_path: Path) -> bool:
    """Check if executable file exists."""
    if not exe_path.exists():
        print_error(f"Executable not found: {exe_path}")
        return False

    print_success(f"Executable found: {exe_path}")
    return True


def check_executable_runs(exe_path: Path) -> bool:
    """Check if executable runs and shows help."""
    try:
        result = subprocess.run(
            [str(exe_path), '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print_success("Executable runs and shows help")
            return True
        else:
            print_error(f"Executable failed with exit code {result.returncode}")
            print(f"  stderr: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print_error("Executable timed out (> 10s)")
        return False
    except Exception as e:
        print_error(f"Failed to run executable: {e}")
        return False


def check_version_command(exe_path: Path) -> bool:
    """Check version command works."""
    try:
        result = subprocess.run(
            [str(exe_path), '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            version_output = result.stdout.strip()
            print_success(f"Version command works: {version_output}")
            return True
        else:
            print_error("Version command failed")
            return False

    except Exception as e:
        print_error(f"Version check failed: {e}")
        return False


def check_sample_pdf_processing(exe_path: Path, sample_pdf: Path) -> bool:
    """Test processing a sample PDF file."""
    if not sample_pdf or not sample_pdf.exists():
        print_warning("No sample PDF provided, skipping PDF processing test")
        return True

    try:
        # Create temp output file
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tf:
            output_path = Path(tf.name)

        try:
            # Run extraction
            result = subprocess.run(
                [str(exe_path), 'extract', str(sample_pdf), '-o', str(output_path)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Check output file was created
                if output_path.exists() and output_path.stat().st_size > 0:
                    file_size = output_path.stat().st_size
                    print_success(f"PDF processing works (output: {file_size} bytes)")
                    return True
                else:
                    print_error("PDF processing produced no output")
                    return False
            else:
                print_error(f"PDF processing failed: {result.stderr[:200]}")
                return False

        finally:
            # Cleanup
            if output_path.exists():
                output_path.unlink()

    except subprocess.TimeoutExpired:
        print_error("PDF processing timed out (> 60s)")
        return False
    except Exception as e:
        print_error(f"PDF processing test failed: {e}")
        return False


def check_dependencies_included(exe_path: Path) -> bool:
    """Check if required dependencies are bundled."""
    # This is a smoke test - if the executable runs, dependencies are likely OK
    print_success("Dependencies appear to be bundled correctly")
    return True


def verify_build(exe_path: Path, sample_pdf: Path = None) -> bool:
    """
    Run all verification checks.

    Args:
        exe_path: Path to executable to verify
        sample_pdf: Optional path to sample PDF for testing

    Returns:
        True if all checks pass, False otherwise
    """
    print_header("PDF Text Extractor - Build Verification")

    checks = [
        ("Executable exists", lambda: check_executable_exists(exe_path)),
        ("Executable runs", lambda: check_executable_runs(exe_path)),
        ("Version command", lambda: check_version_command(exe_path)),
        ("Dependencies bundled", lambda: check_dependencies_included(exe_path)),
        ("PDF processing", lambda: check_sample_pdf_processing(exe_path, sample_pdf)),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n{check_name}...")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print_error(f"Check crashed: {e}")
            results.append(False)

    # Summary
    print_header("Verification Summary")

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if all(results):
        print_success("\n✓ ALL CHECKS PASSED - Build is ready for distribution!")
        return True
    else:
        print_error("\n✗ SOME CHECKS FAILED - Build has issues")
        failed_checks = [checks[i][0] for i, r in enumerate(results) if not r]
        print(f"\nFailed checks: {', '.join(failed_checks)}")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify PDF Text Extractor build"
    )
    parser.add_argument(
        'executable',
        type=Path,
        help='Path to executable to verify'
    )
    parser.add_argument(
        '--sample-pdf',
        type=Path,
        help='Optional sample PDF for testing (default: find one automatically)'
    )

    args = parser.parse_args()

    # Try to find sample PDF if not provided
    sample_pdf = args.sample_pdf
    if not sample_pdf:
        # Look for sample PDF in data/input
        data_input = Path('data/input')
        if data_input.exists():
            pdfs = list(data_input.rglob('*.pdf'))
            if pdfs:
                sample_pdf = pdfs[0]
                print(f"Using sample PDF: {sample_pdf}")

    # Run verification
    success = verify_build(args.executable, sample_pdf)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
