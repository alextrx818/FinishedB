#!/usr/bin/env python3
"""
Sports Bot Comprehensive Diagnostic Test Suite

This diagnostic framework thoroughly tests all components of the Sports Bot system
to ensure they meet established standards and functionality.

Usage:
    python3 diagnostics.py [options]

Options:
    --all           Run all tests (default)
    --api           Test API connectivity only
    --db            Test database operations only
    --telegram      Test Telegram integration only
    --monitor       Test match data monitor only
    --logging       Test logging system only
    --integration   Test component integration only
    --verbose       Show detailed output
    --report        Generate HTML report
"""

import os
import sys
import argparse
import datetime
import json
import importlib
import traceback

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../..'))
sys.path.append(project_root)

# Test result class
class TestResult:
    """Stores the result of a single diagnostic test"""
    def __init__(self, name, passed, message="", details=None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.datetime.now()
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }

# Test modules to be imported dynamically
TEST_MODULES = [
    "api_tests", 
    "db_tests", 
    "telegram_tests", 
    "monitor_tests",
    "logging_tests", 
    "integration_tests"
]

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Sports Bot Diagnostic Tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--api", action="store_true", help="Test API connectivity")
    parser.add_argument("--db", action="store_true", help="Test database operations")
    parser.add_argument("--telegram", action="store_true", help="Test Telegram integration")
    parser.add_argument("--monitor", action="store_true", help="Test match data monitor")
    parser.add_argument("--logging", action="store_true", help="Test logging system")
    parser.add_argument("--integration", action="store_true", help="Test component integration")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    
    args = parser.parse_args()
    
    # If no specific tests are specified, run all tests
    if not (args.api or args.db or args.telegram or args.monitor or 
            args.logging or args.integration):
        args.all = True
    
    return args

def import_test_module(module_name):
    """Dynamically import a test module"""
    try:
        # First try to import from the local 'tests' directory
        spec = importlib.util.find_spec(f"tests.{module_name}")
        if spec:
            return importlib.import_module(f"tests.{module_name}")
        
        # Then try the absolute path
        module_path = os.path.join(script_dir, "tests", f"{module_name}.py")
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        
        print(f"Warning: Could not find test module {module_name}")
        return None
    except Exception as e:
        print(f"Error importing test module {module_name}: {e}")
        return None

def run_tests(args):
    """Run the specified diagnostic tests"""
    test_results = {}
    
    def print_section(title):
        """Print a section header"""
        print("\n" + "=" * 80)
        print(f" {title} ".center(80))
        print("=" * 80)
    
    print_section("SPORTS BOT DIAGNOSTIC TESTS")
    print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {project_root}")
    
    # Import and execute test modules
    for module_name in TEST_MODULES:
        # Determine if this module should be run
        should_run = False
        if args.all:
            should_run = True
        elif (module_name == "api_tests" and args.api or
              module_name == "db_tests" and args.db or
              module_name == "telegram_tests" and args.telegram or
              module_name == "monitor_tests" and args.monitor or
              module_name == "logging_tests" and args.logging or
              module_name == "integration_tests" and args.integration):
            should_run = True
        
        if not should_run:
            continue
        
        print_section(f"Running {module_name}")
        
        # Import the module
        module = import_test_module(module_name)
        if not module:
            test_results[module_name] = [
                TestResult(
                    name=f"{module_name}_import", 
                    passed=False, 
                    message=f"Failed to import {module_name}"
                )
            ]
            continue
        
        # Execute tests in the module
        try:
            # Look for a run_tests function in the module
            if hasattr(module, "run_tests"):
                results = module.run_tests(verbose=args.verbose)
                test_results[module_name] = results
                
                # Print summary for this module
                passed = sum(1 for result in results if result.passed)
                total = len(results)
                print(f"\nResults: {passed}/{total} tests passed")
                
                # Print details of failed tests
                failed = [result for result in results if not result.passed]
                if failed:
                    print("\nFailed tests:")
                    for result in failed:
                        print(f"  - {result.name}: {result.message}")
            else:
                print(f"Warning: {module_name} does not contain a run_tests function")
                test_results[module_name] = [
                    TestResult(
                        name=f"{module_name}_function", 
                        passed=False, 
                        message=f"{module_name} does not contain a run_tests function"
                    )
                ]
        except Exception as e:
            print(f"Error running tests in {module_name}: {e}")
            traceback.print_exc()
            test_results[module_name] = [
                TestResult(
                    name=f"{module_name}_execution", 
                    passed=False, 
                    message=f"Error running tests: {str(e)}"
                )
            ]
    
    return test_results

def save_results(results):
    """Save test results to a JSON file"""
    # Create results directory if it doesn't exist
    results_dir = os.path.join(project_root, "logs", "diagnostics")
    os.makedirs(results_dir, exist_ok=True)
    
    # Format results for serialization
    serializable_results = {}
    for module_name, module_results in results.items():
        serializable_results[module_name] = [result.to_dict() for result in module_results]
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(results_dir, f"diagnostics_{timestamp}.json")
    
    # Write to file
    with open(filename, "w") as f:
        json.dump(serializable_results, f, indent=2)
    
    return filename

def generate_report(results, results_file):
    """Generate an HTML report from test results"""
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(project_root, "logs", "diagnostics", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(reports_dir, f"diagnostic_report_{timestamp}.html")
    
    # Count overall stats
    total_tests = 0
    total_passed = 0
    for module_results in results.values():
        total_tests += len(module_results)
        total_passed += sum(1 for result in module_results if result.passed)
    
    pass_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    overall_status = "PASS" if pass_percentage >= 95 else "FAIL"
    
    # Generate HTML
    with open(report_file, "w") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Sports Bot Diagnostic Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ 
            padding: 15px; 
            background-color: {("#dff0d8" if overall_status == "PASS" else "#f2dede")}; 
            border: 1px solid {("#d6e9c6" if overall_status == "PASS" else "#ebccd1")}; 
            border-radius: 4px; 
            margin-bottom: 20px;
        }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .details {{ font-family: monospace; white-space: pre; margin: 10px 0; padding: 10px; background-color: #f8f8f8; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <h1>Sports Bot Diagnostic Report</h1>
    <p>Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Status:</strong> <span class="{'pass' if overall_status == 'PASS' else 'fail'}">{overall_status}</span></p>
        <p><strong>Tests:</strong> {total_passed}/{total_tests} passed ({pass_percentage:.1f}%)</p>
    </div>
""")
        
        # Add details for each module
        for module_name, module_results in results.items():
            module_total = len(module_results)
            module_passed = sum(1 for result in module_results if result.passed)
            module_percentage = (module_passed / module_total * 100) if module_total > 0 else 0
            
            f.write(f"""
    <h2>{module_name} ({module_passed}/{module_total} passed, {module_percentage:.1f}%)</h2>
    <table>
        <tr>
            <th>Test</th>
            <th>Status</th>
            <th>Message</th>
        </tr>
""")
            
            for result in module_results:
                status_class = "pass" if result.passed else "fail"
                status_text = "PASS" if result.passed else "FAIL"
                
                f.write(f"""
        <tr>
            <td>{result.name}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{result.message}</td>
        </tr>
""")
            
            f.write("    </table>")
        
        f.write("""
    <hr>
    <p><small>Sports Bot Diagnostic Framework</small></p>
</body>
</html>
""")
    
    return report_file

def display_summary(results):
    """Display a summary of test results"""
    print("\n" + "=" * 80)
    print(" TEST RESULTS SUMMARY ".center(80))
    print("=" * 80)
    
    total_tests = 0
    total_passed = 0
    
    for module_name, module_results in results.items():
        module_total = len(module_results)
        module_passed = sum(1 for result in module_results if result.passed)
        
        print(f"\n{module_name}:")
        print(f"  Passed: {module_passed}/{module_total} ({module_passed/module_total*100:.1f}%)")
        
        # List failed tests
        failed = [result for result in module_results if not result.passed]
        if failed:
            print("  Failed tests:")
            for result in failed:
                print(f"    - {result.name}: {result.message}")
        
        total_tests += module_total
        total_passed += module_passed
    
    # Overall summary
    print("\n" + "-" * 80)
    if total_tests > 0:
        print(f"OVERALL: {total_passed}/{total_tests} tests passed ({total_passed/total_tests*100:.1f}%)")
        if total_passed == total_tests:
            print("\n✅ All tests passed! System is functioning according to standards.")
        else:
            print(f"\n❌ {total_tests - total_passed} tests failed. See details above.")
    else:
        print("No tests were run!")

def main():
    """Main entry point for the diagnostics framework"""
    args = parse_args()
    results = run_tests(args)
    display_summary(results)
    
    # Save results to file
    results_file = save_results(results)
    print(f"\nResults saved to: {results_file}")
    
    # Generate HTML report if requested
    if args.report:
        report_file = generate_report(results, results_file)
        print(f"HTML report generated: {report_file}")

if __name__ == "__main__":
    main()
