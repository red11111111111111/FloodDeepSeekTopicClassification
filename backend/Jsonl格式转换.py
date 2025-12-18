import json

# 输入文件路径（你原来的 JSONL）
input_file = r'E:\Experiment\train\GPT\data\val_data.jsonl'

# 输出文件路径（用于微调的新格式）
output_file = r'E:\Experiment\train\Qwen\data\qwen_finetune_val_data.jsonl'

with open(input_file, 'r', encoding='utf-8') as fin, \
     open(output_file, 'w', encoding='utf-8') as fout:

    for line_num, line in enumerate(fin, 1):
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
            prompt = data["prompt"]
            completion = data["completion"]

            # 构造新格式
            new_data = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": completion}
                ]
            }

            # 写入文件
            fout.write(json.dumps(new_data, ensure_ascii=False) + '\n')

        except Exception as e:
            print(f"第 {line_num} 行解析失败: {e}")
            continue

print(f"✅ 转换完成！已保存至: {output_file}")