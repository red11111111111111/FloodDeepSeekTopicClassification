import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import logging

lora_checkpoint = "/root/autodl-tmp/Deepseek_exp/deepseek-classify-best/checkpoint-13125"
base_model_name = "/root/autodl-tmp/DeepSeek-R1-Distill-Llama-8B"
label_mapping_path = "/root/autodl-tmp/label_mapping.json"


with open(label_mapping_path, "r", encoding="utf-8") as f:
    label_mapping = json.load(f)
id2label = {int(v): k for k, v in label_mapping.items()}
num_labels = len(id2label)

tokenizer = AutoTokenizer.from_pretrained(base_model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    
base_model = AutoModelForSequenceClassification.from_pretrained(
    base_model_name,
    num_labels=num_labels,
    id2label=id2label,
    label2id=label_mapping,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
base_model.config.pad_token_id = tokenizer.pad_token_id

model = PeftModel.from_pretrained(base_model, lora_checkpoint)
model = model.eval()




app = FastAPI(title="Deepseek Text Classifier", version="1.0")

class ClassifyRequest(BaseModel):
    text: str

@app.post("/classify")
def classify(request: ClassifyRequest):
    try:
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="文本不能为空")
            
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(model.device)

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            pred_id = torch.argmax(logits, dim=-1).item()
            pred_label = id2label.get(pred_id)

        if pred_label is None:
            logging.warning(f"预测 ID {pred_id} 不在 id2label 中")
            raise HTTPException(status_code=500, detail="模型返回未知类别")

        return {"category": pred_label}

    except Exception as e:
        logging.error(f"分类出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分类失败: {str(e)}")
