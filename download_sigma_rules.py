#!/usr/bin/env python3
"""
Script to download Sigma rules from the SigmaHQ GitHub repository
"""

import requests
import base64
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

class SigmaRuleDownloader:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com/repos/SigmaHQ/sigma"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Sigma2XSIAM-Converter'
        }
        if token:
            self.headers['Authorization'] = f'token {token}'
        
        self.downloaded_files = []
        self.failed_downloads = []

    def get_directory_contents(self, path: str) -> List[Dict]:
        """Get contents of a directory from GitHub API"""
        url = f"{self.base_url}/contents/{path}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error accessing {path}: {e}")
            return []

    def download_file(self, file_path: str, local_dir: str) -> Optional[str]:
        """Download a single file from GitHub"""
        url = f"{self.base_url}/contents/{file_path}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data['encoding'] == 'base64':
                content = base64.b64decode(data['content']).decode('utf-8')
                
                # Create local path
                local_path = os.path.join(local_dir, os.path.basename(file_path))
                Path(local_dir).mkdir(parents=True, exist_ok=True)
                
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Downloaded: {os.path.basename(file_path)}")
                return local_path
            
        except Exception as e:
            print(f"❌ Failed to download {file_path}: {e}")
            self.failed_downloads.append({'path': file_path, 'error': str(e)})
            return None

    def download_directory(self, remote_path: str, local_dir: str, recursive: bool = True) -> List[str]:
        """Download all .yml files from a directory"""
        print(f"📁 Scanning directory: {remote_path}")
        contents = self.get_directory_contents(remote_path)
        
        downloaded_files = []
        
        for item in contents:
            if item['type'] == 'file' and item['name'].endswith(('.yml', '.yaml')):
                local_path = self.download_file(item['path'], local_dir)
                if local_path:
                    downloaded_files.append(local_path)
                    self.downloaded_files.append({
                        'name': item['name'],
                        'remote_path': item['path'],
                        'local_path': local_path,
                        'size': item['size']
                    })
                
                # Rate limiting - GitHub API allows 5000 requests/hour with token
                time.sleep(0.1)
                
            elif item['type'] == 'dir' and recursive:
                # Recursively download subdirectories
                subdir_local = os.path.join(local_dir, item['name'])
                subdir_files = self.download_directory(item['path'], subdir_local, recursive)
                downloaded_files.extend(subdir_files)
        
        return downloaded_files

    def download_sample_rules(self, max_files: int = 50) -> List[str]:
        """Download a sample of rules for testing"""
        print(f"🔍 Downloading sample of {max_files} rules for testing...")
        
        # Key directories to sample from
        sample_dirs = [
            'rules/windows/process_creation',
            'rules/windows/registry',
            'rules/linux/process_creation',
            'rules/network',
            'rules/web'
        ]
        
        downloaded_files = []
        files_per_dir = max_files // len(sample_dirs)
        
        for directory in sample_dirs:
            print(f"📂 Sampling from {directory}")
            contents = self.get_directory_contents(directory)
            
            file_count = 0
            for item in contents:
                if (item['type'] == 'file' and 
                    item['name'].endswith(('.yml', '.yaml')) and 
                    file_count < files_per_dir):
                    
                    local_path = self.download_file(item['path'], 'downloaded_rules/sample')
                    if local_path:
                        downloaded_files.append(local_path)
                        file_count += 1
                        
                    time.sleep(0.1)
            
            if len(downloaded_files) >= max_files:
                break
        
        return downloaded_files

    def save_download_report(self, output_file: str = 'test_results/download_report.json'):
        """Save download statistics"""
        report = {
            'total_downloaded': len(self.downloaded_files),
            'total_failed': len(self.failed_downloads),
            'downloaded_files': self.downloaded_files,
            'failed_downloads': self.failed_downloads
        }
        
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Download report saved to {output_file}")
        return report

if __name__ == "__main__":
    # Initialize downloader
    downloader = SigmaRuleDownloader()
    
    # Download sample rules for testing
    sample_files = downloader.download_sample_rules(50)
    
    # Save report
    report = downloader.save_download_report()
    
    print(f"\n📈 Download Summary:")
    print(f"   ✅ Successfully downloaded: {len(sample_files)} files")
    print(f"   ❌ Failed downloads: {len(downloader.failed_downloads)}")
    print(f"   📁 Files saved to: downloaded_rules/sample/")