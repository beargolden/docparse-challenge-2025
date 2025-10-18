#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将原始 jsonl (image + prefix + suffix) 转换为 LLaMA Factory 多模态格式。
特点：
1. 保留 prefix 作为 human 指令的一部分；
2. suffix 原样输出到 gpt 回复；
3. 自动根据输入文件名选择 image 路径前缀：
   - train.jsonl → vlm-challenge-update/image/train
   - eval.jsonl 或 val.jsonl → vlm-challenge-update/image/eval
   - 其他情况 → vlm-challenge-update/image/other
4. 结构完全符合 LLaMA Factory 多模态训练数据格式。
"""

import json
import sys
from pathlib import Path
from tqdm import tqdm


def infer_image_root(input_path: Path) -> str:
    """根据文件名自动推断 image 根目录路径"""
    name = input_path.stem.lower()
    if "train" in name:
        subset = "train"
    elif "eval" in name or "val" in name:
        subset = "eval"
    else:
        subset = "other"
    return f"/root/autodl-tmp/LLaMA-Factory/data/vlm-challenge-update/image/{subset}"


def convert_file(input_path, output_path, image_root=None):
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        print(f"❌ 输入文件不存在：{input_path}")
        sys.exit(1)

    # 自动推断 image 路径前缀
    if image_root is None:
        image_root = infer_image_root(input_path)
        print(f"📁 自动检测 image 根目录：{image_root}")

    image_root = image_root.rstrip("/")

    total = sum(1 for _ in open(input_path, "r", encoding="utf-8"))
    success, fail = 0, 0

    with open(input_path, "r", encoding="utf-8") as fin, \
            open(output_path, "w", encoding="utf-8") as fout:

        for line_no, line in enumerate(tqdm(fin, total=total, desc="Converting"), start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except Exception as e:
                print(f"⚠️ 跳过第 {line_no} 行：无法解析 JSON ({e})")
                fail += 1
                continue

            image = obj.get("image", "")
            prefix = obj.get("prefix", "")
            suffix = obj.get("suffix", "")

            # 拼接 image 路径前缀
            if image:
                image = f"{image_root}/{image.lstrip('/')}"

            if not prefix:
                print(f"⚠️ 第 {line_no} 行缺少 prefix 字段，已使用空字符串")
            if not suffix:
                print(f"⚠️ 第 {line_no} 行缺少 suffix 字段，已使用空字符串")

            sample = {
                "id": f"sample-{success + 1:04d}",
                "image": image,
                "conversations": [
                    {
                        "from": "human",
                        "value": f"<image>请解析该文档图像，输出符合要求的{prefix}结构。"
                    },
                    {
                        "from": "gpt",
                        "value": suffix
                    }
                ]
            }

            fout.write(json.dumps(sample, ensure_ascii=False) + "\n")
            success += 1

    print(f"\n✅ 转换完成：成功 {success} 条，跳过 {fail} 条")
    print(f"📄 输出文件：{output_path.resolve()}")


def main():
    if len(sys.argv) < 3:
        print("用法：python convert_to_llama_factory.py <input.jsonl> <output.jsonl> [image_root]")
        print("说明：若未指定 image_root，将自动根据输入文件名推断 train / eval / other")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    image_root = sys.argv[3] if len(sys.argv) >= 4 else None

    convert_file(input_path, output_path, image_root)


if __name__ == "__main__":
    main()
