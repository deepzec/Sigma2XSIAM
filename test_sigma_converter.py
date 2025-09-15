#!/usr/bin/env python3
"""
Comprehensive testing framework for Sigma2XSIAM converter
Tests multiple Sigma rules and reports failures
"""

import os
import sys
import json
import time
import traceback
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add the project directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import required modules
from sigma.rule import SigmaRule
from sigma.processing.pipeline import ProcessingPipeline
from cortex.backends.cortexxsiam import CortexXSIAMBackend

class SigmaConverterTester:
    def __init__(self, pipeline_file: str = "pipelines/cortex_xdm.yml"):
        self.pipeline_file = pipeline_file
        self.backend = None
        self.test_results = []
        self.failed_tests = []
        self.successful_tests = []
        
        # Initialize backend
        self._initialize_backend()

    def _initialize_backend(self):
        """Initialize the Sigma converter backend"""
        try:
            print("🔧 Initializing Sigma2XSIAM backend...")
            
            # Load processing pipeline
            with open(self.pipeline_file, "r", encoding='utf-8') as f:
                pipeline_yaml = f.read()
            
            # Try different methods to load pipeline
            try:
                pipeline = ProcessingPipeline.from_yaml(pipeline_yaml)
            except AttributeError:
                pipeline_data = yaml.safe_load(pipeline_yaml)
                pipeline = ProcessingPipeline(pipeline_data)
            
            # Initialize backend
            self.backend = CortexXSIAMBackend(processing_pipeline=pipeline)
            print("✅ Backend initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize backend: {e}")
            raise

    def test_single_rule(self, rule_file: str) -> Dict:
        """Test conversion of a single Sigma rule"""
        test_result = {
            'file': rule_file,
            'filename': os.path.basename(rule_file),
            'status': 'unknown',
            'error': None,
            'query': None,
            'rule_info': {},
            'execution_time': 0
        }
        
        start_time = time.time()
        
        try:
            # Read and parse rule
            with open(rule_file, 'r', encoding='utf-8') as f:
                rule_content = f.read()
            
            # Parse YAML to get rule info
            try:
                rule_data = yaml.safe_load(rule_content)
                test_result['rule_info'] = {
                    'title': rule_data.get('title', 'Unknown'),
                    'level': rule_data.get('level', 'Unknown'),
                    'logsource': rule_data.get('logsource', {}),
                    'author': rule_data.get('author', 'Unknown')
                }
            except:
                pass
            
            # Convert with Sigma
            sigma_rule = SigmaRule.from_yaml(rule_content)
            conversion_result = self.backend.convert_rule(sigma_rule)
            
            # Handle different return types
            if isinstance(conversion_result, list):
                query = conversion_result[0] if conversion_result else "Empty result"
            else:
                query = conversion_result
            
            test_result['query'] = query
            test_result['status'] = 'success'
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['error'] = str(e)
            test_result['error_type'] = type(e).__name__
            test_result['traceback'] = traceback.format_exc()
        
        test_result['execution_time'] = time.time() - start_time
        return test_result

    def test_directory(self, rules_directory: str) -> List[Dict]:
        """Test all rules in a directory"""
        print(f"🧪 Testing rules in directory: {rules_directory}")
        
        rule_files = []
        for root, dirs, files in os.walk(rules_directory):
            for file in files:
                if file.endswith(('.yml', '.yaml')):
                    rule_files.append(os.path.join(root, file))
        
        print(f"📋 Found {len(rule_files)} rule files to test")
        
        results = []
        for i, rule_file in enumerate(rule_files, 1):
            print(f"🔄 Testing {i}/{len(rule_files)}: {os.path.basename(rule_file)}")
            
            result = self.test_single_rule(rule_file)
            results.append(result)
            
            if result['status'] == 'success':
                self.successful_tests.append(result)
            else:
                self.failed_tests.append(result)
                print(f"   ❌ FAILED: {result['error']}")
            
            # Progress indicator
            if i % 10 == 0:
                success_count = len(self.successful_tests)
                failure_count = len(self.failed_tests)
                print(f"   📊 Progress: {success_count} success, {failure_count} failed")
        
        self.test_results.extend(results)
        return results

    def generate_failure_report(self) -> Dict:
        """Generate detailed failure analysis"""
        if not self.failed_tests:
            return {"message": "No failed tests to report"}
        
        # Categorize failures by error type
        error_categories = {}
        for test in self.failed_tests:
            error_type = test.get('error_type', 'Unknown')
            if error_type not in error_categories:
                error_categories[error_type] = []
            error_categories[error_type].append(test)
        
        # Categorize by log source
        logsource_categories = {}
        for test in self.failed_tests:
            logsource = test['rule_info'].get('logsource', {})
            category = f"{logsource.get('product', 'unknown')}/{logsource.get('category', 'unknown')}"
            if category not in logsource_categories:
                logsource_categories[category] = []
            logsource_categories[category].append(test)
        
        failure_report = {
            'summary': {
                'total_tests': len(self.test_results),
                'successful_tests': len(self.successful_tests),
                'failed_tests': len(self.failed_tests),
                'success_rate': len(self.successful_tests) / len(self.test_results) * 100 if self.test_results else 0
            },
            'error_categories': {
                category: {
                    'count': len(tests),
                    'examples': [
                        {
                            'file': test['filename'],
                            'title': test['rule_info'].get('title', 'Unknown'),
                            'error': test['error']
                        } for test in tests[:5]  # Show first 5 examples
                    ]
                } for category, tests in error_categories.items()
            },
            'logsource_failures': {
                category: len(tests) 
                for category, tests in logsource_categories.items()
            },
            'detailed_failures': self.failed_tests
        }
        
        return failure_report

    def save_results(self, output_dir: str = "test_results"):
        """Save test results to files"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete results
        results_file = os.path.join(output_dir, f"test_results_{timestamp}.json")
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': {
                    'total_tests': len(self.test_results),
                    'successful_tests': len(self.successful_tests),
                    'failed_tests': len(self.failed_tests)
                },
                'results': self.test_results
            }, f, indent=2)
        
        # Save failure report
        failure_report = self.generate_failure_report()
        failure_file = os.path.join(output_dir, f"failure_report_{timestamp}.json")
        with open(failure_file, 'w') as f:
            json.dump(failure_report, f, indent=2)
        
        # Save summary report
        summary_file = os.path.join(output_dir, f"summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Sigma2XSIAM Converter Test Results\n")
            f.write(f"{'='*50}\n")
            f.write(f"Test Date: {datetime.now()}\n")
            f.write(f"Total Rules Tested: {len(self.test_results)}\n")
            f.write(f"Successful Conversions: {len(self.successful_tests)}\n")
            f.write(f"Failed Conversions: {len(self.failed_tests)}\n")
            f.write(f"Success Rate: {len(self.successful_tests)/len(self.test_results)*100:.1f}%\n\n")
            
            if self.failed_tests:
                f.write("FAILED TEST CASES:\n")
                f.write("-" * 30 + "\n")
                for test in self.failed_tests:
                    f.write(f"File: {test['filename']}\n")
                    f.write(f"Title: {test['rule_info'].get('title', 'Unknown')}\n")
                    f.write(f"Error: {test['error']}\n")
                    f.write(f"Error Type: {test.get('error_type', 'Unknown')}\n")
                    f.write("-" * 30 + "\n")
        
        return results_file, failure_file, summary_file

    def print_summary(self):
        """Print test summary to console"""
        total = len(self.test_results)
        success = len(self.successful_tests)
        failed = len(self.failed_tests)
        
        print(f"\n📊 TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Total Rules Tested: {total}")
        print(f"✅ Successful Conversions: {success}")
        print(f"❌ Failed Conversions: {failed}")
        print(f"📈 Success Rate: {success/total*100:.1f}%" if total > 0 else "No tests run")
        
        if self.failed_tests:
            print(f"\n❌ FAILED CASES ({len(self.failed_tests)}):")
            print("-" * 30)
            for test in self.failed_tests[:10]:  # Show first 10 failures
                print(f"• {test['filename']}: {test['error'][:80]}...")

if __name__ == "__main__":
    # Initialize tester
    tester = SigmaConverterTester()
    
    # Test downloaded rules
    rules_directory = "downloaded_rules"
    if os.path.exists(rules_directory):
        tester.test_directory(rules_directory)
        
        # Save results
        results_file, failure_file, summary_file = tester.save_results()
        
        # Print summary
        tester.print_summary()
        
        print(f"\n📁 Results saved to:")
        print(f"   📋 Complete results: {results_file}")
        print(f"   ❌ Failure analysis: {failure_file}")
        print(f"   📄 Summary report: {summary_file}")
        
    else:
        print(f"❌ Rules directory '{rules_directory}' not found!")
        print("Run download_sigma_rules.py first to download test rules.")