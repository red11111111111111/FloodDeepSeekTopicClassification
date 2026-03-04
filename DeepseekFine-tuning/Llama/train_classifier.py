from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model
from datasets import Dataset
import pandas as pd
import torch
import json
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

with open("/root/autodl-tmp/label_mapping.json", "r", encoding="utf-8") as f:
    label_mapping = json.load(f)
id2label = {int(v): k for k, v in label_mapping.items()}
num_labels = len(id2label)
print("加载标签映射:", id2label)


train_df = pd.read_csv("/root/autodl-tmp/data/train_data_numeric.csv")
test_df = pd.read_csv("/root/autodl-tmp/data/test_data_numeric.csv")


train_dataset = Dataset.from_pandas(train_df[['text', 'label']])
test_dataset = Dataset.from_pandas(test_df[['text', 'label']])



model_path = "/root/autodl-tmp/Meta-Llama-3-8B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_path)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token


def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors=None
    )


print(" 正在 tokenize 数据...")
train_dataset = train_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
test_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])


model = AutoModelForSequenceClassification.from_pretrained(
    model_path,
    num_labels=num_labels,
    id2label=id2label,
    label2id=label_mapping,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
model.gradient_checkpointing_enable() 
model.config.pad_token_id = tokenizer.pad_token_id

lora_config = LoraConfig(
    r=16,  
    lora_alpha=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="SEQ_CLS"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()


training_args = TrainingArguments(
    output_dir="./llama3-classify-best",
    num_train_epochs=5,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-5,
    eval_strategy="no", 
    save_strategy="epoch",
    logging_steps=10,
    load_best_model_at_end=False, 
    metric_for_best_model=None,


    bf16=True,
    fp16=False,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},


    dataloader_pin_memory=False,
    dataloader_num_workers=2,

    save_total_limit=2,
    warmup_ratio=0.1,
    weight_decay=0.01,
    report_to="none",
)


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=-1)
    precision, recall, f1, support = precision_recall_fscore_support(labels, predictions, average=None,
                                                                     labels=range(num_labels))
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "support": support
    }



trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics,
)

print("开始训练...")
trainer.train()


print("在测试集上评估...")
test_results = trainer.evaluate(test_dataset, metric_key_prefix="test")
predictions = np.argmax(test_results["predictions"], axis=-1)
labels = test_results["label_ids"]
precision, recall, f1, support = precision_recall_fscore_support(
    labels, predictions, average=None, labels=range(num_labels)
)

accuracy = np.mean(predictions == labels)
macro_precision = np.mean(precision)
macro_recall = np.mean(recall)
macro_f1 = np.mean(f1)
weighted_precision = np.average(precision, weights=support)
weighted_recall = np.average(recall, weights=support)
weighted_f1 = np.average(f1, weights=support)

output_lines = []
output_lines.append("              precision    recall  f1-score   support\n")
for i in range(num_labels):
    line = f"          {id2label[i]:<8} {precision[i]:.2f}      {recall[i]:.2f}      {f1[i]:.2f}       {support[i]}"
    print(line)
    output_lines.append(line + "\n")

output_lines.append(f"    accuracy                           {accuracy:.2f}      {len(labels)}\n")
output_lines.append(
    f"   macro avg       {macro_precision:.2f}      {macro_recall:.2f}      {macro_f1:.2f}      {len(labels)}\n")
output_lines.append(
    f"weighted avg       {weighted_precision:.2f}      {weighted_recall:.2f}      {weighted_f1:.2f}      {len(labels)}\n")

with open("classification_report.txt", "w", encoding="utf-8") as f:
    f.write("Classification Report\n")
    f.write("=" * 60 + "\n")
    f.writelines(output_lines)

print("分类报告已保存至 classification_report.txt")
trainer.save_model("./llama3-classify-final")
tokenizer.save_pretrained("./llama3-classify-final")
print(" 模型已保存到 ./llama3-classify-final")
