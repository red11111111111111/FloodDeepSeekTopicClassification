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
num_labels = len(id2label)
print(" 加载标签映射:", id2label)


# 2. 加载数据

train_df = pd.read_csv("/root/autodl-tmp/data/train_data_numeric.csv")
val_df = pd.read_csv("/root/autodl-tmp/data/val_data_numeric.csv")  # 保留用于 save_best_model


# 3. 转为 Hugging Face Dataset

train_dataset = Dataset.from_pandas(train_df[['text', 'label']])
val_dataset = Dataset.from_pandas(val_df[['text', 'label']])  # 用于选择最佳模型


# 4. 加载 Tokenizer

model_path = "/root/autodl-tmp/DeepSeek-R1-Distill-Llama-8B"  # 或你的本地路径
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

# 设置 pad_token：DeepSeek
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.unk_token


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
val_dataset = val_dataset.map(tokenize_function, batched=True)

# 设置 PyTorch 格式
train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
val_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])


# 5. 加载模型 + LoRA

model = AutoModelForSequenceClassification.from_pretrained(
    model_path,
    num_labels=num_labels,
    id2label=id2label,
    label2id=label_mapping,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)
model.gradient_checkpointing_enable()
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


# 6. 训练参数（不评估，但用 val 选最佳模型）

training_args = TrainingArguments(
    output_dir="./deepseek-classify-best",
    num_train_epochs=5,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=8,
    learning_rate=2e-5,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_steps=10,
    load_best_model_at_end=True,
    metric_for_best_model="loss",

    # 显存优化
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



# 8. 开始训练（使用 val 选模型，但不打印指标）

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,  #  传入 val，用于计算 loss 选模型
    # compute_metrics 不传
)

print(" 开始训练...")
trainer.train()



trainer.save_model("./deepseek-classify-final")
tokenizer.save_pretrained("./deepseek-classify-final")
print(" 模型已保存到 ./deepseek-classify-final")