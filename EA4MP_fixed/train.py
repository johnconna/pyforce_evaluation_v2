# bert_train_final.py
import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from transformers import EarlyStoppingCallback
from sklearn.model_selection import train_test_split
from datasets import Dataset
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
import json

def load_data(data_path):
    """加载训练数据"""
    data = []
    labels = []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                label, sequence = parts
                data.append(sequence)
                labels.append(int(label))
    
    return data, labels

def compute_metrics(eval_pred):
    """计算评估指标"""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='binary')
    acc = accuracy_score(labels, predictions)
    
    # 添加每个类别的详细指标
    class_report = classification_report(labels, predictions, output_dict=True, target_names=['benign', 'malicious'])
    
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall,
        'malicious_precision': class_report['malicious']['precision'],
        'malicious_recall': class_report['malicious']['recall'],
        'malicious_f1': class_report['malicious']['f1-score'],
        'benign_precision': class_report['benign']['precision'],
        'benign_recall': class_report['benign']['recall'],
        'benign_f1': class_report['benign']['f1-score'],
    }

def main():
    # 配置
    model_name = "bert-base-uncased"
    data_file = "bert_training_data_balanced.txt"  # 使用平衡数据集
    output_dir = "./bert_final_model"
    
    print("Loading training data...")
    sequences, labels = load_data(data_file)
    
    print(f"Total samples: {len(sequences)}")
    label_counts = pd.Series(labels).value_counts()
    print(f"Label distribution: {label_counts.to_dict()}")
    
    # 分割数据（80%训练，20%验证）
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        sequences, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    print(f"Training samples: {len(train_texts)}")
    print(f"Validation samples: {len(val_texts)}")
    
    # 初始化tokenizer
    tokenizer = BertTokenizer.from_pretrained(model_name)
    
    # 标记化函数
    def tokenize_function(examples):
        return tokenizer(examples['text'], padding="max_length", truncation=True, max_length=512)
    
    # 创建数据集
    train_dataset = Dataset.from_dict({"text": train_texts, "labels": train_labels})
    val_dataset = Dataset.from_dict({"text": val_texts, "labels": val_labels})
    
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    
    # 设置PyTorch格式
    train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])
    val_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])
    
    # 加载模型
    num_labels = len(set(labels))
    print(f"Number of classes: {num_labels}")
    
    model = BertForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=num_labels
    )
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=4,  # 增加训练轮数
        per_device_train_batch_size=16,  # 增加batch size
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=50,
        evaluation_strategy="steps",
        eval_steps=100,
        save_steps=200,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        save_total_limit=3,  # 只保存最好的3个模型
        report_to=None,  # 禁用wandb等报告
    )
    
    # 创建训练器
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )
    
    # 开始训练
    print("Starting training...")
    train_result = trainer.train()
    
    # 保存模型
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # 保存训练指标
    metrics = train_result.metrics
    with open(f"{output_dir}/training_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Model saved to: {output_dir}")
    
    # 最终评估
    print("\nFinal evaluation on validation set:")
    eval_results = trainer.evaluate()
    for key, value in eval_results.items():
        print(f"  {key}: {value:.4f}")
    
    # 保存评估结果
    with open(f"{output_dir}/evaluation_results.json", "w") as f:
        json.dump(eval_results, f, indent=2)

if __name__ == "__main__":
    main()
