#!/usr/bin/env python3
"""
Top-level Test Runner for QKD-Secured Online Voting Simulator (TEST_SPEC.md).

Executes:
1. All 18 automated unit and integration tests across 4 Test Suites (test_spec.py)
2. Benchmark evaluations, quantitative summary tables, and presentation figures (generate_test_spec_report.py)

Usage:
    python run_test_spec.py
    python run_test_spec.py --tests-only
    python run_test_spec.py --report-only
"""

import os
import sys
import argparse
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_SRC = ROOT_DIR / "backend" / "src"

if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))


def run_unit_tests() -> bool:
    print("\n" + "=" * 80)
    print("STEP 1: RUNNING AUTOMATED UNIT TESTS (TEST_SPEC.md - Test Suites 1 to 4)")
    print("=" * 80)

    from evaluation import test_spec

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_spec)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_deliverables_report():
    print("\n" + "=" * 80)
    print("STEP 2: GENERATING PRESENTATION DELIVERABLES & PLOTS (Section 4)")
    print("=" * 80)

    from evaluation import generate_test_spec_report, generate_report_figures
    generate_test_spec_report.main()
    generate_report_figures.main()


def main():
    parser = argparse.ArgumentParser(description="Run QKD Voting Simulator TEST_SPEC suite and reports.")
    parser.add_argument("--tests-only", action="store_true", help="Run only the 18 automated unit tests.")
    parser.add_argument("--report-only", action="store_true", help="Generate only the deliverables report and figures.")
    args = parser.parse_args()

    tests_passed = True
    if not args.report_only:
        tests_passed = run_unit_tests()

    if not args.tests_only:
        run_deliverables_report()

    if tests_passed:
        print("\n" + "=" * 80)
        print("ALL TEST SPECIFICATION REQUIREMENTS VERIFIED SUCCESSFULLY!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("SOME TESTS FAILED - Please check error messages above.")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
