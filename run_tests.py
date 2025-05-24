#!/usr/bin/env python3
"""
Test Runner for OKX Trade Simulator

This script runs all the tests for the OKX Trade Simulator and reports the results.
"""

import unittest
import sys
import os
import time
import logging
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_results.log')
    ]
)

logger = logging.getLogger(__name__)


def discover_and_run_tests(test_dir='tests', pattern='test_*.py', verbosity=2):
    """
    Discover and run all tests in the specified directory.
    
    Args:
        test_dir (str): Directory containing the tests
        pattern (str): Pattern to match test files
        verbosity (int): Verbosity level for test output
    
    Returns:
        unittest.TestResult: The test results
    """
    # Print header
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}Running OKX Trade Simulator Tests")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    # Get the start time
    start_time = time.time()
    
    # Discover tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(test_dir, pattern=pattern)
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=verbosity)
    test_result = test_runner.run(test_suite)
    
    # Get the end time
    end_time = time.time()
    
    # Print summary
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}Test Summary")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    # Calculate total tests
    total_tests = test_result.testsRun
    passed_tests = total_tests - len(test_result.errors) - len(test_result.failures)
    
    # Print results
    print(f"{Fore.GREEN}Passed: {passed_tests}/{total_tests}{Style.RESET_ALL}")
    if test_result.failures:
        print(f"{Fore.RED}Failed: {len(test_result.failures)}{Style.RESET_ALL}")
    if test_result.errors:
        print(f"{Fore.RED}Errors: {len(test_result.errors)}{Style.RESET_ALL}")
    
    # Print time taken
    time_taken = end_time - start_time
    print(f"\nTime taken: {time_taken:.2f} seconds")
    
    # Print failed tests
    if test_result.failures:
        print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
        for failure in test_result.failures:
            print(f"- {failure[0]}")
    
    # Print errors
    if test_result.errors:
        print(f"\n{Fore.RED}Tests with Errors:{Style.RESET_ALL}")
        for error in test_result.errors:
            print(f"- {error[0]}")
    
    # Log results
    logger.info(f"Tests run: {total_tests}")
    logger.info(f"Tests passed: {passed_tests}")
    logger.info(f"Tests failed: {len(test_result.failures)}")
    logger.info(f"Tests with errors: {len(test_result.errors)}")
    logger.info(f"Time taken: {time_taken:.2f} seconds")
    
    return test_result


def run_specific_test(test_name):
    """
    Run a specific test module.
    
    Args:
        test_name (str): Name of the test module to run
    
    Returns:
        unittest.TestResult: The test results
    """
    # Print header
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}Running Test: {test_name}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    # Get the start time
    start_time = time.time()
    
    # Load the test module
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromName(f"tests.{test_name}")
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # Get the end time
    end_time = time.time()
    
    # Print time taken
    time_taken = end_time - start_time
    print(f"\nTime taken: {time_taken:.2f} seconds")
    
    # Log results
    logger.info(f"Test {test_name} completed")
    logger.info(f"Time taken: {time_taken:.2f} seconds")
    
    return test_result


def main():
    """Main entry point for the test runner."""
    # Check if a specific test was requested
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name.startswith('test_') and test_name.endswith('.py'):
            # Remove .py extension
            test_name = test_name[:-3]
        elif not test_name.startswith('test_'):
            test_name = f"test_{test_name}"
        
        # Run the specific test
        result = run_specific_test(test_name)
    else:
        # Run all tests
        result = discover_and_run_tests()
    
    # Return exit code based on test results
    if result.wasSuccessful():
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
