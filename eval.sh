#!/bin/bash

# conda activate docparse         # 激活环境

IMAGE_DIR="/root/autodl-tmp/DocParse-Challenge/datasets/vlm-challenge-B-complete/image/test_B"    # 图片目录
OUTPUT_BASE_DIR="/root/autodl-tmp/DocParse-Challenge/datasets/vlm-challenge-B-complete/image/test_result"    # jsonl结果保存目录
MERGE_MODEL_PATH="/root/autodl-tmp/DocParse-Challenge/fine_tuned_Qwen2.5-VL-7B-Instruct/checkpoint-2000/merged_Qwen2.5-VL-7B-Instruct"  # 合并的模型权重路径

LOG_FILE="./logs/eval.log"
touch "$LOG_FILE"

# 运行推理脚本
export CUDA_VISIBLE_DEVICES=0
python eval.py \
  --model_path "${MERGE_MODEL_PATH}" \
  --output_base_dir "${OUTPUT_BASE_DIR}" \
  --image_dir "${IMAGE_DIR}" \
  > "${LOG_FILE}" 2>&1

echo "Finished"