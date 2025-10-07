#!/usr/bin/env python3
"""
Comprehensive test script for Sigma2XSIAM converter
Tests all Sigma rules and generates detailed statistics
"""

import sys
import os
import json
import yaml
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sigma.rule import SigmaRule
from sigma.processing.pipeline import ProcessingPipeline
from cortex.backends.cortexxsiam import CortexXSIAMBackend

def find_all_sigma_rules(directory):
    """Find all Sigma rule files"""
    rules = []
    for ext in ['*.yml', '*.yaml']:
        rules.extend(Path(directory).rglob(ext))
    return rules

def load_backend():
    """Initialize the backend with pipeline"""
    with open("pipelines/cortex_xdm.yml", "r", encoding='utf-8') as f:
        pipeline_yaml = f.read()
    
    try:
        pipeline = ProcessingPipeline.from_yaml(pipeline_yaml)
    except AttributeError:
        pipeline_data = yaml.safe_load(pipeline_yaml)
        pipeline = ProcessingPipeline(pipeline_data)
    
    return CortexXSIAMBackend(processing_pipeline=pipeline)

def test_rule(rule_path, backend):
    """Test a single rule conversion"""
    try:
        with open(rule_path, 'r', encoding='utf-8') as f:
            rule_content = f.read()
        
        sigma_rule = SigmaRule.from_yaml(rule_content)
        result = backend.convert_rule(sigma_rule)
        
        if isinstance(result, list):
            query = result[0] if result else ""
        else:
            query = result
        
        return {
            'status': 'success',
            'query': query,
            'rule_path': str(rule_path)
        }
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        return {
            'status': 'failed',
            'error': error_msg,
            'error_type': error_type,
            'rule_path': str(rule_path)
        }

def main():
    print("🔍 Sigma2XSIAM Comprehensive Testing")
    print("=" * 60)
    
    # Find all rules
    print("\n📂 Finding Sigma rules...")
    rules = find_all_sigma_rules("attached_assets/sigma_rules")
    total_rules = len(rules)
    print(f"Found {total_rules} Sigma rule files")
    
    # Initialize backend
    print("\n🔧 Initializing backend...")
    backend = load_backend()
    print("✅ Backend initialized")
    
    # Test all rules
    print(f"\n🧪 Testing {total_rules} rules...")
    results = {
        'success': [],
        'failed': []
    }
    
    error_categories = defaultdict(int)
    
    for i, rule_path in enumerate(rules, 1):
        if i % 100 == 0:
            print(f"Progress: {i}/{total_rules} ({i*100//total_rules}%)")
        
        result = test_rule(rule_path, backend)
        
        if result['status'] == 'success':
            results['success'].append(result)
        else:
            results['failed'].append(result)
            error_categories[result['error_type']] += 1
    
    # Calculate statistics
    success_count = len(results['success'])
    failed_count = len(results['failed'])
    success_rate = (success_count / total_rules * 100) if total_rules > 0 else 0
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"\n✅ Successful Conversions: {success_count}/{total_rules} ({success_rate:.2f}%)")
    print(f"❌ Failed Conversions: {failed_count}/{total_rules} ({100-success_rate:.2f}%)")
    
    if error_categories:
        print(f"\n📋 Error Categories:")
        for error_type, count in sorted(error_categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / failed_count * 100) if failed_count > 0 else 0
            print(f"  • {error_type}: {count} ({percentage:.1f}% of failures)")
    
    # Show sample failures
    if results['failed']:
        print(f"\n🔍 Sample Failed Rules (showing first 5):")
        for i, failure in enumerate(results['failed'][:5], 1):
            rule_name = Path(failure['rule_path']).name
            print(f"\n  {i}. {rule_name}")
            print(f"     Error: {failure['error_type']}")
            print(f"     Message: {failure['error'][:100]}...")
    
    # Save detailed report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_rules': total_rules,
            'success_count': success_count,
            'failed_count': failed_count,
            'success_rate': success_rate,
            'error_categories': dict(error_categories),
            'failed_rules': results['failed'][:50]  # First 50 failures
        }, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    print("\n" + "=" * 60)
    
    return success_rate

if __name__ == "__main__":
    main()
