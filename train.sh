#!/bin/bash

# conda activate docparse         # 激活环境

CFG_PATH="/root/autodl-tmp/DocParse-Challenge/trainer/config/qwen2.5vl-7b-lora.yaml"     # 配置文件路径
OUTPUT_PATH="/root/autodl-tmp/DocParse-Challenge/fine_tuned_Qwen2.5-VL-7B-Instruct"      # 模型输出路径

LOG_PATH="./logs/train.log"
touch "$LOG_PATH"

MAX_PIXELS=1003520 MIN_PIXELS=200704 \
python train.py \
  --config "${CFG_PATH}" \
  --output_path "${OUTPUT_PATH}" \
  > "${LOG_PATH}" 2>&1 &

tail -f "${LOG_PATH}"