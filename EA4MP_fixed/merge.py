# merge_final_datasets.py
import os
import json
import random
from datetime import datetime

def load_json_data(filepath):
    """加载JSON数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def merge_sequence_data():
    """合并恶意和良性序列数据"""
    print("Loading sequence data...")
    
    # 加载恶意包数据
    malicious_data = load_json_data("all_malware_sequences.json")
    if not malicious_data:
        return False
    
    # 加载良性包数据  
    benign_data = load_json_data("all_benign_sequences.json")
    if not benign_data:
        return False
    
    print(f"Malicious packages: {malicious_data['metadata']['total_packages']}")
    print(f"Benign packages: {benign_data['metadata']['total_packages']}")
    
    # 合并包数据
    combined_packages = []
    
    # 添加恶意包（标签1）
    malicious_success = 0
    for package in malicious_data['packages']:
        if package['status'] == 'success' and package['sequence']:
            package['label'] = 1
            combined_packages.append(package)
            malicious_success += 1
    
    # 添加良性包（标签0）
    benign_success = 0
    for package in benign_data['packages']:
        if package['status'] == 'success' and package['sequence']:
            package['label'] = 0
            combined_packages.append(package)
            benign_success += 1
    
    # 创建合并的元数据
    combined_metadata = {
        'total_original_packages': malicious_data['metadata']['total_packages'] + benign_data['metadata']['total_packages'],
        'total_successful_packages': len(combined_packages),
        'malicious_original': malicious_data['metadata']['total_packages'],
        'malicious_successful': malicious_success,
        'malicious_success_rate': malicious_success / malicious_data['metadata']['total_packages'] * 100,
        'benign_original': benign_data['metadata']['total_packages'],
        'benign_successful': benign_success,
        'benign_success_rate': benign_success / benign_data['metadata']['total_packages'] * 100,
        'merged_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'description': 'Combined malicious and benign PyPI packages for malware detection'
    }
    
    # 保存合并的序列数据
    combined_data = {
        'metadata': combined_metadata,
        'packages': combined_packages
    }
    
    with open('combined_sequences.json', 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nCombined sequence data saved to: combined_sequences.json")
    print(f"Total successful packages: {len(combined_packages)}")
    print(f"  - Malicious: {malicious_success}")
    print(f"  - Benign: {benign_success}")
    
    return combined_packages

def merge_bert_training_data():
    """合并BERT训练数据"""
    print("\nMerging BERT training data...")
    
    # 读取恶意训练数据
    malicious_lines = []
    if os.path.exists("bert_training_data.txt"):
        with open("bert_training_data.txt", 'r', encoding='utf-8') as f:
            malicious_lines = f.readlines()
    
    # 读取良性训练数据
    benign_lines = []
    if os.path.exists("bert_training_data_benign.txt"):
        with open("bert_training_data_benign.txt", 'r', encoding='utf-8') as f:
            benign_lines = f.readlines()
    
    # 合并所有数据
    all_lines = malicious_lines + benign_lines
    
    # 保存合并的数据
    with open("bert_training_data_combined.txt", 'w', encoding='utf-8') as f:
        f.writelines(all_lines)
    
    malicious_count = len(malicious_lines)
    benign_count = len(benign_lines)
    
    print(f"Combined BERT training data saved to: bert_training_data_combined.txt")
    print(f"Total samples: {len(all_lines)}")
    print(f"  - Malicious (1): {malicious_count}")
    print(f"  - Benign (0): {benign_count}")
    
    return all_lines, malicious_count, benign_count

def create_balanced_dataset(all_lines, malicious_count, benign_count):
    """创建平衡的数据集"""
    print("\nCreating balanced dataset...")
    
    # 分离恶意和良性样本
    malicious_samples = [line for line in all_lines if line.startswith('1\t')]
    benign_samples = [line for line in all_lines if line.startswith('0\t')]
    
    print(f"Available malicious samples: {len(malicious_samples)}")
    print(f"Available benign samples: {len(benign_samples)}")
    
    # 使用较小的数量作为平衡基准
    min_count = min(len(malicious_samples), len(benign_samples))
    
    # 随机选择样本
    balanced_malicious = random.sample(malicious_samples, min_count)
    balanced_benign = random.sample(benign_samples, min_count)
    
    # 合并并打乱顺序
    balanced_lines = balanced_malicious + balanced_benign
    random.shuffle(balanced_lines)
    
    # 保存平衡数据集
    with open("bert_training_data_balanced.txt", 'w', encoding='utf-8') as f:
        f.writelines(balanced_lines)
    
    print(f"Balanced dataset saved to: bert_training_data_balanced.txt")
    print(f"Balanced samples: {len(balanced_lines)}")
    print(f"  - Malicious: {len(balanced_malicious)}")
    print(f"  - Benign: {len(balanced_benign)}")
    
    return balanced_lines

def create_dataset_stats():
    """创建数据集统计信息"""
    print("\nCreating dataset statistics...")
    
    stats = {}
    
    # 序列数据统计
    if os.path.exists("combined_sequences.json"):
        with open("combined_sequences.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            stats['sequences'] = data['metadata']
    
    # BERT训练数据统计
    bert_files = {
        'combined': 'bert_training_data_combined.txt',
        'balanced': 'bert_training_data_balanced.txt'
    }
    
    for name, filename in bert_files.items():
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                malicious = sum(1 for line in lines if line.startswith('1\t'))
                benign = sum(1 for line in lines if line.startswith('0\t'))
                
                stats[name] = {
                    'total_samples': len(lines),
                    'malicious_samples': malicious,
                    'benign_samples': benign,
                    'balance_ratio': min(malicious, benign) / max(malicious, benign) * 100 if max(malicious, benign) > 0 else 0
                }
    
    # 保存统计信息
    with open("dataset_statistics.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"Dataset statistics saved to: dataset_statistics.json")
    
    # 打印统计摘要
    print("\n" + "="*50)
    print("DATASET SUMMARY")
    print("="*50)
    
    if 'sequences' in stats:
        seq = stats['sequences']
        print(f"Sequences:")
        print(f"  Total packages: {seq['total_successful_packages']}")
        print(f"  Malicious: {seq['malicious_successful']} ({seq['malicious_success_rate']:.1f}% success rate)")
        print(f"  Benign: {seq['benign_successful']} ({seq['benign_success_rate']:.1f}% success rate)")
    
    for name in ['combined', 'balanced']:
        if name in stats:
            bert = stats[name]
            print(f"\n{name.upper()} BERT Data:")
            print(f"  Total samples: {bert['total_samples']}")
            print(f"  Malicious: {bert['malicious_samples']}")
            print(f"  Benign: {bert['benign_samples']}")
            print(f"  Balance: {bert['balance_ratio']:.1f}%")

def main():
    """主函数"""
    print("Starting final dataset merge...")
    print("="*60)
    
    # 1. 合并序列数据
    combined_packages = merge_sequence_data()
    if not combined_packages:
        print("Failed to merge sequence data")
        return
    
    # 2. 合并BERT训练数据
    all_lines, malicious_count, benign_count = merge_bert_training_data()
    
    # 3. 创建平衡数据集
    if all_lines:
        create_balanced_dataset(all_lines, malicious_count, benign_count)
    
    # 4. 创建统计信息
    create_dataset_stats()
    
    print("\n" + "="*60)
    print("DATASET MERGE COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nNext steps:")
    print("1. Use 'bert_training_data_balanced.txt' for training BERT model")
    print("2. Use 'combined_sequences.json' for analysis and debugging")
    print("3. Check 'dataset_statistics.json' for detailed statistics")

if __name__ == "__main__":
    main()
