# 通过ModelScope 的 snapshot_download函数下载模型

from modelscope import snapshot_download

# 下载Qwen2.5-VL-3B-Instruct模型
# model_dir = snapshot_download(model_id="Qwen/Qwen2.5-VL-3B-Instruct", local_dir="base_models/Qwen2.5-VL-3B-Instruct")

# 下载Qwen2.5-VL-7B-Instruct模型
model_dir = snapshot_download(model_id="Qwen/Qwen2.5-VL-7B-Instruct", local_dir="base_models/Qwen2.5-VL-7B-Instruct")

# 下载...模型
# model_dir = snapshot_download(model_id="...", local_dir="base_models/...")

print(f"模型已下载到: {model_dir}")