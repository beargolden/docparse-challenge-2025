# docparse-challenge-2025

金山办公2025算法挑战赛——多模态文档解析大赛 [参赛代码] ![visitors](https://visitor-badge.laobi.icu/badge?page_id=beargolden.docparse-challenge-2025)

[![金山办公2025算法挑战赛——多模态文档解析大赛](./assets/docparse-challenge-2025-logo.png "docparse-challenge-2025-logo")](https://datastudio.wps.cn/matchcenter/competition/2/introduction)

## 项目简介

`docparse-challenge-2025`是CVPR@HBUT在金山办公2025算法挑战赛——多模态文档解析大赛中使用的代码。该代码基于竞赛主办方提供的基线代码，采用Qwen2.5‑VL‑7B模型实现了LoRA微调、权重合并与推理评测脚本。

- **训练脚本**：`train.py`（LoRA微调）
- **合并脚本**：`merge_lora.py`
- **推理脚本**：`eval.py`（批量推理生成`jsonl`提交文件）

## 环境依赖

```bash
conda create -n docparse python=3.12 -y
# conda init bash && source /root/.bashrc # 更新bashrc中的环境变量（AutoDL平台需要）
conda activate docparse

# transformers安装
git clone https://github.com/huggingface/transformers.git
cd transformers
# git checkout 9985d06add07a4cc691dc54a7e34f54205c04d40
pip install -e .

# 其他库安装（可以不指定ms-swift、lmdeploy的版本号）
pip install ms-swift==3.4.0 lmdeploy==0.9.1 qwen-vl-utils[decord] peft accelerate beautifulsoup4 bitsandbytes

# flash-attention安装
pip install ninja # Make sure that ninja is installed and that it works correctly （e.g. ninja --version then echo $? should return exit code 0）.
# pip install -U flash-attn --no-build-isolation # 若安装失败，可以参考https：//github.com/Dao-AILab/flash-attention/releases，选择v2.7.4.post1本地安装
pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3+cu12torch2.7cxx11abiTRUE-cp312-cp312-linux_x86_64.whl # 注意：flash-attention安装版本要与已安装的python/cuda/torch的版本匹配

# 安装modelscope下载模型
pip install modelscope
```

## 目录结构

```text
docparse-challenge-2025/
├─ train.sh                # 训练入口
├─ train.py                # LoRA微调主脚本
├─ merge_lora.py           # LoRA与基座模型合并脚本
├─ eval.sh                 # 推理入口（vLLM+批量推理）
├─ eval.py                 # 执行模型推理并生成jsonl
└─ trainer/
 ├─ config/
 │   └─ qwen2.5vl-7b-lora.yaml  # 默认超参&数据路径配置
 └─ dataset/
     └─ preprocess.py           # 数据集构建与预处理
```

## 快速开始

### 1. 编辑配置

**关键字段修改**：

```text
| 字段                       | 说明                                  |
| ------------------------- | ------------------------------------－|
| `model.model_path`        | 基座模型（如Qwen2.5‑VL‑7B‑Instruct）路径 |
| `dataset.train_data_path` | 训练集图像数据路径                      |
| `dataset.train_json_path` | 训练集`jsonl`                         |
| `dataset.valid_data_path` | 验证集集图像数据路径                    |
| `dataset.valid_json_path` | 验证集`jsonl`                         |
| 其余**LoRA/hparams**       | 按需调整                              |
```

### 2. 启动训练

1. **修改路径**

```bash
#!/bin/bash
source activate docparse         # 激活环境

CFG_PATH="path/to/your/qwen2.5vl-7b-lora.yaml"     # 配置文件路径
OUTPUT_PATH="path/to/your/output/dir"              # 模型输出路径

MAX_PIXELS=1003520 MIN_PIXELS=200704 \
python -m torch.distributed.launch --nproc_per_node=4 train.py \
--config "${CFG_PATH}" \
--output_path "${OUTPUT_PATH}" \
> ./log/train.log 2>&1 &
tail -f ./log/train.log
```

2. **启动训练**

```bash
bash train.sh
```

3. **其他参数**

- `--nproc_per_node=4`：默认使用4块GPU，可自行调整。

训练完成后，`OUTPUT_PATH`内将包含**LoRA adapter**权重。

### 3. 合并LoRA权重（可选）

1. **修改变量**：

```python
BASE_MODEL_PATH   = "path/to/your/qwen2.5-vl-7b-instruct"            # 基座模型路径
ADAPTER_PATH      = "path/to/your/output/dir/checkpoint-xxxx"        # 模型checkpoint路径
MERGED_MODEL_PATH = "path/to/your/output/dir/merged_qwen2.5_vl_7b"   # 合并模型输出路径
```

2. **执行脚本**

```bash
python merge_lora.py
```

### 4. 启动推理服务

1. **修改路径**

```bash
source activate path/to/your/conda/env                           # 激活环境

IMAGE_DIR="path/to/your/image/dir"                               # 图片目录
MERGE_MODEL_PATH="path/to/your/output/dir/merged_qwen2.5_vl_7b"  # 合并的模型权重路径
OUTPUT_BASE_DIR="path/to/your/eval_result"                       # jsonl结果保存目录

export CUDA_VISIBLE_DEVICES=0
python eval.py \
--model_path "${MERGE_MODEL_PATH}" \
--output_base_dir "${OUTPUT_BASE_DIR}" \
--image_dir "${IMAGE_DIR}" \
> "${LOG_FILE}" 2>&1
```

2. **启动推理**

```bash
bash eval.sh
```

推理完成后，确认OUTPUT_BASE_DIR中的predict.jsonl行数与测试集图像数量一致，之后提交至比赛平台即可查看分数。

## 竞赛成绩

目前，CVPR@HBUT团队第一次玩转大模型微调，2025-09-15训练得到的最优模型在A榜取得0.8281（位列第7），终极B榜取得0.8372（位列14）[加油]

| 榜单 | 成绩     |
|----|--------|
| A榜 | 0.8281 |
| B榜 | 0.8372 |

## 数据集与模型下载

原始数据集：请访问竞赛官网下载

部分修正后的数据集链接: https://pan.baidu.com/s/1vOodMhkZ6KkniFQqR4W4ng?pwd=avne 提取码: avne

2025-09-15训练得到的最优模型链接: https://pan.baidu.com/s/1cSjZWAj-L0Q0TKZwmU3RfA?pwd=gja5 提取码: gja5