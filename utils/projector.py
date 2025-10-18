from transformers import Qwen2_5_VLForConditionalGeneration

model = Qwen2_5_VLForConditionalGeneration.from_pretrained("base_models/Qwen2.5-VL-7B-Instruct")

for name, module in model.named_modules():
    print(name)
