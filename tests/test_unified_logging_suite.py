#!/usr/bin/env python3
"""
🧪 Unified Logging System Test Suite

Comprehensive test runner for all unified logging system tests.
Runs tests in logical order and provides detailed reporting.

Usage:
    python tests/test_unified_logging_suite.py
    python tests/test_unified_logging_suite.py --quick  # Skip performance tests
    python tests/test_unified_logging_suite.py --verbose  # Detailed output

Author: AI Assistant
Created: 2024
"""

import pytest
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any


class UnifiedLoggingTestSuite:
    """🧪 Comprehensive test suite for unified logging system."""
    
    def __init__(self, verbose: bool = False, quick: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.results = {}
        
    def run_test_category(self, category: str, test_files: List[str]) -> Dict[str, Any]:
        """Run a category of tests and return results."""
        print(f"\n{'='*60}")
        print(f"🧪 Running {category} Tests")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Build pytest command
        cmd_args = ["-v"] if self.verbose else ["-q"]
        cmd_args.extend(["--tb=short", "--color=yes"])
        
        # Add test files
        for test_file in test_files:
            if Path(test_file).exists():
                cmd_args.append(test_file)
            else:
                print(f"⚠️  Warning: Test file not found: {test_file}")
        
        if not any(Path(f).exists() for f in test_files):
            print(f"❌ No test files found for {category}")
            return {"status": "skipped", "duration": 0, "reason": "No test files"}
        
        # Run tests
        try:
            exit_code = pytest.main(cmd_args)
            duration = time.time() - start_time
            
            if exit_code == 0:
                status = "passed"
                print(f"✅ {category} tests completed successfully in {duration:.2f}s")
            else:
                status = "failed"
                print(f"❌ {category} tests failed (exit code: {exit_code}) in {duration:.2f}s")
                
            return {
                "status": status,
                "duration": duration,
                "exit_code": exit_code
            }
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 {category} tests crashed: {e}")
            return {
                "status": "crashed",
                "duration": duration,
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all unified logging tests in logical order."""
        print("🚀 Starting Unified Logging System Test Suite")
        print(f"Mode: {'Quick' if self.quick else 'Full'} | Verbose: {self.verbose}")
        
        # Define test categories and files
        test_categories = [
            {
                "name": "Unit Tests",
                "description": "Core component unit tests",
                "files": [
                    "tests/unit/test_unified_logging.py"
                ]
            },
            {
                "name": "Integration Tests", 
                "description": "Component integration tests",
                "files": [
                    "tests/integration/test_unified_logging_integration.py"
                ]
            },
            {
                "name": "Functional Tests",
                "description": "End-to-end workflow tests", 
                "files": [
                    "tests/functional/test_unified_logging_workflows.py"
                ]
            }
        ]
        
        # Add performance tests if not in quick mode
        if not self.quick:
            test_categories.append({
                "name": "Performance Tests",
                "description": "Performance and load tests",
                "files": [
                    "tests/performance/test_unified_logging_performance.py"
                ]
            })
        
        # Run each test category
        overall_start = time.time()
        
        for category in test_categories:
            result = self.run_test_category(category["name"], category["files"])
            self.results[category["name"]] = result
        
        overall_duration = time.time() - overall_start
        
        # Generate summary report
        self.print_summary_report(overall_duration)
        
        return self.results
    
    def print_summary_report(self, total_duration: float):
        """Print comprehensive summary report."""
        print(f"\n{'='*80}")
        print("📊 UNIFIED LOGGING SYSTEM TEST SUITE SUMMARY")
        print(f"{'='*80}")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["status"] == "passed")
        failed_tests = sum(1 for r in self.results.values() if r["status"] == "failed")
        skipped_tests = sum(1 for r in self.results.values() if r["status"] == "skipped")
        crashed_tests = sum(1 for r in self.results.values() if r["status"] == "crashed")
        
        print(f"📈 Overall Results:")
        print(f"   Total Categories: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏭️  Skipped: {skipped_tests}")
        print(f"   💥 Crashed: {crashed_tests}")
        print(f"   ⏱️  Total Duration: {total_duration:.2f}s")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for category, result in self.results.items():
            status_emoji = {
                "passed": "✅",
                "failed": "❌", 
                "skipped": "⏭️",
                "crashed": "💥"
            }.get(result["status"], "❓")
            
            print(f"   {status_emoji} {category:20} | {result['status']:8} | {result['duration']:6.2f}s")
            
            if result["status"] == "skipped" and "reason" in result:
                print(f"      Reason: {result['reason']}")
            elif result["status"] == "crashed" and "error" in result:
                print(f"      Error: {result['error']}")
        
        # Success rate
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"\n🎯 Success Rate: {success_rate:.1f}%")
            
            if success_rate == 100.0:
                print("🎉 ALL TESTS PASSED! Unified Logging System is ready for production!")
            elif success_rate >= 80.0:
                print("✨ Most tests passed. Minor issues may need attention.")
            elif success_rate >= 60.0:
                print("⚠️  Some issues detected. Review failed tests.")
            else:
                print("🚨 Significant issues detected. System needs attention.")
        
        print(f"{'='*80}")
    
    def run_specific_stage(self, stage: int) -> Dict[str, Any]:
        """Run tests for a specific stage of unified logging implementation."""
        stage_tests = {
            0: ["tests/unit/test_unified_logging.py::TestUnifiedLoggingSystemStage0"],
            1: ["tests/unit/test_unified_logging.py::TestUnifiedLoggingSystemStage1"],
            2: ["tests/unit/test_unified_logging.py::TestUnifiedLoggingSystemStage2"],
            3: ["tests/unit/test_unified_logging.py::TestUnifiedLoggingSystemStage3"],
            4: ["tests/performance/test_unified_logging_performance.py"],
            5: ["tests/integration/test_unified_logging_integration.py"]
        }
        
        if stage not in stage_tests:
            print(f"❌ Invalid stage: {stage}. Valid stages: 0-5")
            return {"status": "failed", "reason": "Invalid stage"}
        
        return self.run_test_category(f"Stage {stage}", stage_tests[stage])


def main():
    """Main entry point for test suite."""
    parser = argparse.ArgumentParser(description="Unified Logging System Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Skip performance tests for faster execution")
    parser.add_argument("--stage", "-s", type=int, choices=range(0, 6),
                       help="Run tests for specific stage (0-5)")
    
    args = parser.parse_args()
    
    # Create test suite
    suite = UnifiedLoggingTestSuite(verbose=args.verbose, quick=args.quick)
    
    try:
        if args.stage is not None:
            # Run specific stage
            result = suite.run_specific_stage(args.stage)
            exit_code = 0 if result["status"] == "passed" else 1
        else:
            # Run all tests
            results = suite.run_all_tests()
            
            # Determine exit code
            failed_count = sum(1 for r in results.values() 
                             if r["status"] in ["failed", "crashed"])
            exit_code = 0 if failed_count == 0 else 1
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 