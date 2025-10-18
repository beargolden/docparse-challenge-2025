import json

# 待处理数据集名称
train_or_eval = "eval"  # train or eval

# 输入输出路径
src_path = "../dataset/vlm-challenge-B-complete/label/" + train_or_eval + "_dotsocr_generated.jsonl"
out_path = "../dataset/vlm-challenge-B-complete/label/" + train_or_eval + "_dotsocr.jsonl"


def convert_item(item):
    """将单个 OCR item 转换为 HTML"""
    bbox = item.get("bbox", [])
    x1, y1, x2, y2 = bbox if len(bbox) == 4 else ("", "", "", "")
    text = item.get("text", "").strip()
    category = item.get("category", "")

    if category in ["Title", "Section-header", "Caption"]:
        return f'<h2 data-bbox="{x1} {y1} {x2} {y2}">{text}</h2>'
    elif category in ["Text", "List-item"]:
        return f'<p data-bbox="{x1} {y1} {x2} {y2}">{text}</p>'
    elif category == "Footnote":
        return f'<div class="footer" data-bbox="{x1} {y1} {x2} {y2}">{text}</div>'
    elif category == "Formula":
        return f'<div class="formula" data-bbox="{x1} {y1} {x2} {y2}">{text}</div>'
    elif category == "Table":
        return f'<div class="table" data-bbox="{x1} {y1} {x2} {y2}">{text}</div>'
    elif category == "Picture":
        return f'<div class="image" data-bbox="{x1} {y1} {x2} {y2}"></div>'
    elif category == "Page-header":
        return f'<div class="header" data-bbox="{x1} {y1} {x2} {y2}">{text}</div>'
    elif category == "Page-footer":
        return f'<div class="footer" data-bbox="{x1} {y1} {x2} {y2}">{text}</div>'
    else:
        # 未知类型 fallback
        return f'<p data-bbox="{x1} {y1} {x2} {y2}">{text}</p>'


def process_file(src_path, out_path):
    with open(src_path, "r", encoding="utf-8") as fin, \
            open(out_path, "w", encoding="utf-8") as fout:

        for line in fin:
            obj = json.loads(line)
            image = obj["file"]
            try:
                response = json.loads(obj["response"])
            except Exception:
                response = []

            html_parts = [convert_item(item) for item in response]
            html_body = "<body>" + "".join(html_parts) + "</body>"

            new_obj = {
                "image": image,
                "prefix": "QwenVL HTML",
                "suffix": html_body
            }

            # new_obj = {
            #     "image": image,
            #     "prompt": "QwenVL HTML",
            #     "answer": html_body,
            #     "latency": obj["latency"]
            # }

            fout.write(json.dumps(new_obj, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    process_file(src_path, out_path)
    print(f"✅ 转换完成，输出文件: {out_path}")
