#!/usr/bin/env python3
"""
Download a comprehensive set of Sigma rules for thorough testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download_sigma_rules import SigmaRuleDownloader

def download_comprehensive_test_set():
    """Download a comprehensive set of rules from various categories"""
    downloader = SigmaRuleDownloader()
    
    # Define comprehensive test directories
    test_directories = [
        'rules/windows/process_creation',
        'rules/windows/registry/add',
        'rules/windows/registry/delete', 
        'rules/windows/registry/set',
        'rules/windows/file_event',
        'rules/windows/network_connection',
        'rules/linux/process_creation',
        'rules/linux/file_create',
        'rules/linux/auditd',
        'rules/network/cisco',
        'rules/network/dns',
        'rules/web/webserver',
        'rules/application/antivirus',
        'rules/cloud/aws',
        'rules-emerging-threats/2024'
    ]
    
    total_downloaded = 0
    
    for directory in test_directories:
        print(f"\n📁 Processing directory: {directory}")
        try:
            # Download up to 20 files from each directory for comprehensive testing
            files = downloader.download_directory(directory, f'downloaded_rules/comprehensive/{directory.split("/")[-1]}', recursive=False)
            downloaded_count = len(files)
            total_downloaded += downloaded_count
            print(f"   ✅ Downloaded {downloaded_count} files from {directory}")
            
            # Stop early if we have a lot of files to avoid API limits
            if total_downloaded > 150:
                print(f"   🛑 Stopping at {total_downloaded} files to avoid API limits")
                break
                
        except Exception as e:
            print(f"   ❌ Error processing {directory}: {e}")
            continue
    
    # Save comprehensive report
    report = downloader.save_download_report('test_results/comprehensive_download_report.json')
    
    print(f"\n📊 COMPREHENSIVE DOWNLOAD SUMMARY:")
    print(f"   ✅ Total files downloaded: {total_downloaded}")
    print(f"   ❌ Failed downloads: {len(downloader.failed_downloads)}")
    print(f"   📁 Files organized in: downloaded_rules/comprehensive/")
    
    return total_downloaded

if __name__ == "__main__":
    download_comprehensive_test_set()