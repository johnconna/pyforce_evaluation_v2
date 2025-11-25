# download_direct_tsinghua.py
import os
import csv
import requests
import time
import json
import tarfile
import zipfile
from urllib.parse import urljoin
from pathlib import Path

def read_package_list(csv_file):
    """从CSV文件读取包名列表"""
    packages = []
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    package_name = row[0].strip()
                    packages.append(package_name)
        return packages
    except FileNotFoundError:
        print(f"CSV file not found: {csv_file}")
        return []
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []

def get_package_info_from_mirror(package_name, mirror_base="https://pypi.tuna.tsinghua.edu.cn/pypi"):
    """从清华镜像获取包信息"""
    try:
        url = f"{mirror_base}/{package_name}/json"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ✗ Failed to get info for {package_name}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  ✗ Error getting info for {package_name}: {e}")
        return None

def find_source_distribution(package_info):
    """查找源码分发文件（优先.tar.gz）"""
    if not package_info:
        return None
    
    releases = package_info.get('releases', {})
    
    # 获取最新版本
    latest_version = package_info.get('info', {}).get('version')
    if not latest_version or latest_version not in releases:
        # 如果没有最新版本，尝试获取第一个可用版本
        available_versions = [v for v in releases.keys() if releases[v]]
        if not available_versions:
            return None
        latest_version = available_versions[0]
    
    # 查找源码分发文件
    release_files = releases[latest_version]
    source_files = [f for f in release_files if f.get('packagetype') == 'sdist']
    
    if not source_files:
        return None
    
    # 优先选择.tar.gz，然后是.zip
    tar_gz_files = [f for f in source_files if f.get('filename', '').endswith('.tar.gz')]
    if tar_gz_files:
        return tar_gz_files[0]
    
    zip_files = [f for f in source_files if f.get('filename', '').endswith('.zip')]
    if zip_files:
        return zip_files[0]
    
    return source_files[0] if source_files else None

def download_package_file(file_info, download_dir, mirror_base="https://pypi.tuna.tsinghua.edu.cn/simple"):
    """下载包文件"""
    if not file_info:
        return False
    
    filename = file_info.get('filename')
    url = file_info.get('url')
    
    # 如果URL是官方PyPI，替换为清华镜像
    if url and 'pypi.org' in url:
        # 构建镜像URL
        url = f"{mirror_base}/{filename}"
    
    if not url:
        return False
    
    try:
        filepath = os.path.join(download_dir, filename)
        
        # 如果文件已存在，跳过下载
        if os.path.exists(filepath):
            print(f"  ○ File already exists: {filename}")
            return True
        
        print(f"  ↓ Downloading: {filename}")
        response = requests.get(url, stream=True, timeout=60)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"  ✓ Downloaded: {filename}")
            return True
        else:
            print(f"  ✗ Download failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Download error: {e}")
        return False

def extract_packages(download_dir, extract_dir):
    """解压下载的包"""
    if not os.path.exists(download_dir):
        print(f"Download directory not found: {download_dir}")
        return []
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    
    extracted_packages = []
    
    print(f"\nExtracting packages from {download_dir}...")
    
    for filename in os.listdir(download_dir):
        filepath = os.path.join(download_dir, filename)
        
        if filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            # tar.gz 文件
            try:
                if '.tar.gz' in filename:
                    package_name = filename.split('.tar.gz')[0]
                else:
                    package_name = filename.split('.tgz')[0]
                    
                extract_path = os.path.join(extract_dir, package_name)
                
                if not os.path.exists(extract_path):
                    with tarfile.open(filepath, 'r:gz') as tar:
                        tar.extractall(extract_dir)
                    print(f"  ✓ Extracted: {filename} -> {package_name}")
                    extracted_packages.append(package_name)
                else:
                    print(f"  ○ Already exists: {package_name}")
                    extracted_packages.append(package_name)
                    
            except Exception as e:
                print(f"  ✗ Failed to extract {filename}: {e}")
                
        elif filename.endswith('.zip'):
            # zip 文件
            try:
                package_name = filename.split('.zip')[0]
                extract_path = os.path.join(extract_dir, package_name)
                
                if not os.path.exists(extract_path):
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    print(f"  ✓ Extracted: {filename} -> {package_name}")
                    extracted_packages.append(package_name)
                else:
                    print(f"  ○ Already exists: {package_name}")
                    extracted_packages.append(package_name)
                    
            except Exception as e:
                print(f"  ✗ Failed to extract {filename}: {e}")
        elif filename.endswith('.whl'):
            # wheel 文件，跳过不解压
            print(f"  - Skipped wheel file: {filename}")
        else:
            print(f"  ? Skipped (unsupported format): {filename}")
    
    return extracted_packages

def download_packages_direct(package_list, download_dir, mirror_base="https://pypi.tuna.tsinghua.edu.cn/pypi"):
    """直接下载包（不使用pip）"""
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    successful_downloads = []
    failed_downloads = []
    
    print(f"Starting direct download of {len(package_list)} packages...")
    print(f"Using mirror: {mirror_base}")
    
    for i, package in enumerate(package_list, 1):
        print(f"[{i}/{len(package_list)}] Processing: {package}")
        
        try:
            # 获取包信息
            package_info = get_package_info_from_mirror(package, mirror_base)
            if not package_info:
                failed_downloads.append(package)
                continue
            
            # 查找源码分发文件
            file_info = find_source_distribution(package_info)
            if not file_info:
                print(f"  ✗ No source distribution found for: {package}")
                failed_downloads.append(package)
                continue
            
            # 下载文件
            if download_package_file(file_info, download_dir):
                successful_downloads.append(package)
            else:
                failed_downloads.append(package)
                
        except Exception as e:
            print(f"  ✗ Error processing {package}: {e}")
            failed_downloads.append(package)
        
        # 添加延迟避免被限制
        time.sleep(1)
    
    return successful_downloads, failed_downloads

def retry_failed_downloads(failed_packages, download_dir, max_retries=2):
    """重试失败的下载"""
    if not failed_packages:
        print("No failed packages to retry.")
        return [], []
    
    print(f"\nRetrying {len(failed_packages)} failed downloads...")
    
    all_retry_successful = []
    all_retry_failed = failed_packages.copy()
    
    for retry in range(max_retries):
        print(f"Retry attempt {retry + 1}/{max_retries}")
        
        retry_successful = []
        still_failed = []
        
        for package in all_retry_failed:
            print(f"  Retrying: {package}")
            
            try:
                package_info = get_package_info_from_mirror(package)
                if not package_info:
                    still_failed.append(package)
                    continue
                
                file_info = find_source_distribution(package_info)
                if not file_info:
                    still_failed.append(package)
                    continue
                
                if download_package_file(file_info, download_dir):
                    retry_successful.append(package)
                else:
                    still_failed.append(package)
                    
            except Exception as e:
                print(f"  ✗ Retry failed for {package}: {e}")
                still_failed.append(package)
            
            time.sleep(1)
        
        all_retry_successful.extend(retry_successful)
        all_retry_failed = still_failed
        
        if not all_retry_failed or retry == max_retries - 1:
            break
        
        print(f"Waiting 10 seconds before next retry...")
        time.sleep(10)
    
    return all_retry_successful, all_retry_failed

def main():
    """主函数"""
    csv_file = "famous.csv"
    download_dir = "/home/john/pyforce/benign_downloads_direct"
    extract_dir = "/home/john/pyforce/benign_packages"
    mirror_base = "https://pypi.tuna.tsinghua.edu.cn/pypi"
    
    # 读取包列表
    packages = read_package_list(csv_file)
    if not packages:
        print("No packages found in CSV file.")
        return
    
    print(f"Found {len(packages)} packages in CSV file:")
    for pkg in packages[:10]:
        print(f"  - {pkg}")
    if len(packages) > 10:
        print(f"  ... and {len(packages) - 10} more")
    
    # 第一次下载尝试
    successful, failed = download_packages_direct(packages, download_dir, mirror_base)
    
    # 重试失败的下载
    if failed:
        retry_successful, retry_failed = retry_failed_downloads(failed, download_dir)
        successful.extend(retry_successful)
        failed = retry_failed
    
    print(f"\nDownload Summary:")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Success rate: {len(successful)/len(packages)*100:.1f}%")
    
    if failed:
        print(f"\nFailed packages ({len(failed)}):")
        for pkg in failed[:20]:  # 只显示前20个失败的包
            print(f"  - {pkg}")
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")
        
        # 保存失败列表
        with open("failed_packages_direct.txt", "w") as f:
            for pkg in failed:
                f.write(f"{pkg}\n")
        print(f"Failed packages list saved to: failed_packages_direct.txt")
    
    # 解压包
    extracted = extract_packages(download_dir, extract_dir)
    
    print(f"\nExtraction Summary:")
    print(f"  Extracted: {len(extracted)} packages")
    print(f"  Location: {extract_dir}")
    
    # 保存结果
    results = {
        "method": "direct_requests",
        "mirror_used": mirror_base,
        "total_packages": len(packages),
        "successful_downloads": successful,
        "failed_downloads": failed,
        "extracted_packages": extracted,
        "download_directory": download_dir,
        "extract_directory": extract_dir,
        "completion_time": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open("download_results_direct.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: download_results_direct.json")

if __name__ == "__main__":
    main()