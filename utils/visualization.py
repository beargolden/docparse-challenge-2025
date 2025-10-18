import difflib
import json
from pathlib import Path

import gradio as gr
from PIL import Image, ImageDraw, ImageFont

# ---------- 配置 ----------
DATASET_ROOT = Path("../datasets/vlm-challenge-B-complete")
IMAGE_FOLDERS = {
    "train": DATASET_ROOT / "image" / "train",
    "eval": DATASET_ROOT / "image" / "eval",
    "test": DATASET_ROOT / "image" / "test",
    "test_B": DATASET_ROOT / "image" / "test_B",
}
LABEL_FILES = {
    "train": DATASET_ROOT / "label" / "train.jsonl",
    "eval": DATASET_ROOT / "label" / "eval.jsonl",
    "test": DATASET_ROOT / "label" / "predict.jsonl",
    "test_B": DATASET_ROOT / "label" / "predict_B.jsonl",
}
CLASS_COLOR = {
    "h2": "red",
    "p": "green",
    "image": "blue",
    "chart": "orange",
    "table": "purple",
    "formula": "cyan",
    "header": "yellow",
    "footer": "magenta",
}


# ---------- 工具 ----------
def load_jsonl(label_file):
    data = []
    with open(label_file, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data


def parse_bbox(elem):
    bbox_str = elem.get("data-bbox") or elem.get("db")
    x1, y1, x2, y2 = map(int, bbox_str.strip().split())
    return x1, y1, x2, y2


def draw_annotations(image_path, suffix):
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("msyh.ttf", 15)
    except:
        font = ImageFont.load_default(15)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(suffix, "html.parser")

    for tag in soup.find_all(["h2", "p", "div"]):
        cls = tag.name
        if cls == "div":
            cls = tag.get("class")[0] if tag.get("class") else "div"
        color = CLASS_COLOR.get(cls, "black")
        x1, y1, x2, y2 = parse_bbox(tag.attrs)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        if tag.get_text(strip=True):
            draw.text((x1, y1 - 20), cls, fill=color, font=font)
    return img


def get_legend():
    html = "<div style='line-height:1.8em'>"
    for cls, color in CLASS_COLOR.items():
        html += f"<div><span style='display:inline-block;width:20px;height:20px;background:{color};margin-right:5px;'></span>{cls}</div>"
    html += "</div>"
    return html


def visualize(dataset_type="train", index=0):
    data = load_jsonl(LABEL_FILES[dataset_type])
    total = len(data)
    if total == 0:
        return None, "<p style='color:red;'>⚠️ 当前数据集为空</p>", get_legend(), f"{dataset_type}（空）"
    if index >= total:
        index = 0
    sample = data[index]
    image_path = IMAGE_FOLDERS[dataset_type] / sample["image"]

    if dataset_type in ["train", "eval"]:
        html_content = sample.get("suffix", "")
        title = "<h3 style='margin:5px 0;color:green;'>标注 HTML</h3>"
    else:
        html_content = sample.get("answer", "")
        title = "<h3 style='margin:5px 0;color:blue;'>预测 HTML</h3>"

    img_with_ann = draw_annotations(image_path, html_content)
    filename_title = f"**{dataset_type}[{index + 1}/{total}] - 文件名：** {sample['image']}"
    html_display = f"{title}<pre style='white-space: pre-wrap; word-break: break-word;'>{html_content}</pre>"
    return img_with_ann, html_display, get_legend(), filename_title


# ---------- 辅助 ----------
def clear_all(dataset_type):
    data = load_jsonl(LABEL_FILES[dataset_type])
    max_index = max(len(data) - 1, 0)
    return None, "", get_legend(), "", gr.update(value=0, maximum=max_index), gr.update(choices=[], value=None)


def change_index(dataset_type, current_index, step):
    data = load_jsonl(LABEL_FILES[dataset_type])
    new_index = max(0, min(len(data) - 1, current_index + step))
    img, html, legend, filename = visualize(dataset_type, new_index)
    return img, html, new_index, legend, filename


# ---------- 初始化 ----------
dataset_options = ["train", "eval", "test", "test_B"]
default_dataset = "train"
default_data = load_jsonl(LABEL_FILES[default_dataset])
default_max_index = max(len(default_data) - 1, 0)
default_img, default_html, default_legend, default_filename = visualize(default_dataset, 0)

# ---------- 界面 ----------
with gr.Blocks() as demo:
    gr.Markdown("## 📘 文档解析标注可视化（支持智能搜索与自动加载）")

    with gr.Row():
        dataset_dropdown = gr.Dropdown(dataset_options, value=default_dataset, label="选择数据集")
        index_slider = gr.Slider(0, default_max_index, step=1, label="样本索引", value=0)
        search_input = gr.Dropdown(
            label="按文件名搜索（可输入或选择匹配结果）",
            choices=[],
            value=None,
            allow_custom_value=True,
            info="输入文件名关键词，例如 page_12 或 1234.jpg"
        )
        search_btn = gr.Button("搜索", scale=0, min_width=100)
        submit_btn = gr.Button("加载", variant="primary", scale=0, min_width=100)
        clear_btn = gr.Button("清空", scale=0, min_width=100)
        prev_btn = gr.Button("上一张", scale=0, min_width=100)
        next_btn = gr.Button("下一张", scale=0, min_width=100)

    with gr.Row():
        with gr.Column(scale=8):
            filename_out = gr.Markdown(default_filename)
            img_out = gr.Image(type="pil", label="图像标注", value=default_img)
        with gr.Column(scale=4):
            html_out = gr.HTML(label="标注HTML", value=default_html)
        with gr.Column(scale=1):
            legend_out = gr.HTML(label="图例", value=default_legend)

    # ---------- 功能 ----------
    submit_btn.click(
        fn=visualize,
        inputs=[dataset_dropdown, index_slider],
        outputs=[img_out, html_out, legend_out, filename_out]
    )

    clear_btn.click(
        fn=clear_all,
        inputs=[dataset_dropdown],
        outputs=[img_out, html_out, legend_out, filename_out, index_slider, search_input]
    )

    prev_btn.click(
        fn=lambda d, i: change_index(d, i, -1),
        inputs=[dataset_dropdown, index_slider],
        outputs=[img_out, html_out, index_slider, legend_out, filename_out]
    )
    next_btn.click(
        fn=lambda d, i: change_index(d, i, 1),
        inputs=[dataset_dropdown, index_slider],
        outputs=[img_out, html_out, index_slider, legend_out, filename_out]
    )


    # ---------- 搜索 ----------
    def search_file(dataset_type, query):
        if not query or not query.strip():
            return None, "", 0, get_legend(), "❌ 请输入文件名关键词", gr.update(choices=[], value=None)
        data = load_jsonl(LABEL_FILES[dataset_type])
        filenames = [s["image"] for s in data]
        scored = []
        for i, fname in enumerate(filenames):
            if query.lower() in fname.lower():
                pos_score = 1 - (fname.lower().find(query.lower()) / max(len(fname), 1))
                sim_score = difflib.SequenceMatcher(None, query.lower(), fname.lower()).ratio()
                score = 0.6 * sim_score + 0.4 * pos_score
                scored.append((score, i))
        if not scored:
            return None, "", 0, get_legend(), f"❌ 未找到包含 '{query}' 的文件", gr.update(choices=[], value=None)
        scored.sort(key=lambda x: x[0], reverse=True)
        matches = [i for _, i in scored[:50]]
        if len(matches) == 1:
            index = matches[0]
            img, html, legend, filename = visualize(dataset_type, index)
            filename = f"🔍 搜索结果：{filename}"
            return img, html, index, legend, filename, gr.update(choices=[], value=None)
        matched_files = [filenames[i] for i in matches]
        filename = f"🔍 找到 {len(matches)} 个匹配结果（已按相关度排序）"
        return None, "", 0, get_legend(), filename, gr.update(choices=matched_files, value=matched_files[0])


    def select_file(dataset_type, filename):
        if not filename:
            return None, "", 0, get_legend(), ""
        data = load_jsonl(LABEL_FILES[dataset_type])
        index = next((i for i, s in enumerate(data) if s["image"] == filename), 0)
        img, html, legend, fname = visualize(dataset_type, index)
        fname = f"🔎 选中：{fname}"
        return img, html, index, legend, fname


    search_btn.click(
        fn=search_file,
        inputs=[dataset_dropdown, search_input],
        outputs=[img_out, html_out, index_slider, legend_out, filename_out, search_input]
    )

    search_input.change(
        fn=select_file,
        inputs=[dataset_dropdown, search_input],
        outputs=[img_out, html_out, index_slider, legend_out, filename_out]
    )


    # ---------- 数据集切换自动加载 ----------
    def on_dataset_change(dataset_type):
        data = load_jsonl(LABEL_FILES[dataset_type])
        if not data:
            return None, "<p style='color:red;'>⚠️ 当前数据集为空</p>", get_legend(), f"{dataset_type}（空）", gr.update(
                maximum=0, value=0)
        img, html, legend, filename = visualize(dataset_type, 0)
        max_index = max(len(data) - 1, 0)
        return img, html, legend, filename, gr.update(maximum=max_index, value=0)


    dataset_dropdown.change(
        fn=on_dataset_change,
        inputs=dataset_dropdown,
        outputs=[img_out, html_out, legend_out, filename_out, index_slider]
    )

if __name__ == "__main__":
    demo.launch(share=True)
