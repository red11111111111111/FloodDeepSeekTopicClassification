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


# 1. 加载映射文件

with open("/root/autodl-tmp/label_mapping.json", "r", encoding="utf-8") as f:
    label_mapping = json.load(f)
id2label = {int(v): k for k, v in label_mapping.items()}
label2id = {k: v for k, v in label_mapping.items()}
num_labels = len(id2label)
print(" 加载标签映射:", id2label)


# 2. 加载数据（数值化版本）

train_df = pd.read_csv("/root/autodl-tmp/data/train_data_numeric.csv")
val_df = pd.read_csv("/root/autodl-tmp/data/val_data_numeric.csv")


train_dataset = Dataset.from_pandas(train_df[["text", "label"]])
val_dataset = Dataset.from_pandas(val_df[["text", "label"]])


# 3. 加载 Tokenizer

model_path = "/root/autodl-tmp/Qwen/Qwen3-8B"
tokenizer = AutoTokenizer.from_pretrained(model_path)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token


def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=512,
        padding=False,
        return_tensors=None,
    )

print(" 正在 tokenize 数据...")
train_dataset = train_dataset.map(tokenize_function, batched=True)
val_dataset = val_dataset.map(tokenize_function, batched=True)

# 4. 加载模型 + LoRA（使用 SequenceClassification）

model = AutoModelForSequenceClassification.from_pretrained(
    model_path,
    num_labels=num_labels,
    id2label=id2label,
    label2id=label2id,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

model.config.pad_token_id = tokenizer.pad_token_id

# LoRA 配置
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


# 5. 训练参数

training_args = TrainingArguments(
    output_dir="./qwen3-classify-best",
    num_train_epochs=5,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-5,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_steps=10,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    bf16=True,
    fp16=False,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    dataloader_pin_memory=False,
    dataloader_num_workers=0,
    save_total_limit=2,
    warmup_ratio=0.1,
    weight_decay=0.01,
    report_to="all",
    disable_tqdm=False,
    eval_accumulation_steps=4,
)


# 6. 评估指标

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = predictions[0] if isinstance(predictions, tuple) else predictions
    pred_ids = predictions.argmax(axis=-1)
    accuracy = (pred_ids == labels).mean()
    return {"accuracy": accuracy}


# 7. 开始训练

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    tokenizer=tokenizer,  # 自动处理 padding
)

print("🚀 开始训练...")
trainer.train()


# 8. 保存完整模型

#  合并 LoRA 权重
model = model.merge_and_unload()

# 保存
model.save_pretrained("./qwen3-classify-final")
tokenizer.save_pretrained("./qwen3-classify-final")

print(" 完整分类模型已保存到 ./qwen3-classify-final")
print(" 该模型可直接用于：")
print("   - 快速推理（只需 tokenizer + model(text)）")
print("   - vLLM / Transformers 部署")