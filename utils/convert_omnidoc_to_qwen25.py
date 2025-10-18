import json
import re

# 输入输出文件路径
src_file = "../datasets/OmniDocBench/OmniDocBench.json"
tgt_file = "../datasets/OmniDocBench/train.jsonl"

# 类别 → HTML 标签映射
CATEGORY_TO_HTML = {
    "title": "h2",  # 标题
    "text_block": "p",  # 段落级别纯文本
    "figure": "div.image",  # 图片类
    "figure_caption": "h2",  # 图片说明、标题
    "figure_footnote": "div.footer",  # 图片注释
    "table": "div.table",  # 表格主体
    "table_caption": "h2",  # 表格说明和标题
    "table_footnote": "div.footer",  # 表格的注释
    "equation_isolated": "div.formula",  # 行间公式
    "equation_caption": "p",  # 公式序号
    "header": "div.header",  # 页眉
    "footer": "div.footer",  # 页脚
    "page_number": "div.footer",  # 页码
    "page_footnote": "div.footer",  # 页面注释
    "code_txt": "p",  # 代码块
    "reference": "p",  # 参考文献类
}

# 若 order 为 None 或非法值，映射到这个很大的哨兵值（排到最后）
ORDER_SENTINEL = 10 ** 9


def poly_to_bbox(poly):
    """将 poly 转换为 (x1,y1,x2,y2) bbox，返回 int"""
    xs = poly[0::2]
    ys = poly[1::2]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def order_key(det):
    """返回用于排序的 key：把 None / 非整数字段映射为 ORDER_SENTINEL"""
    o = det.get("order", None)
    if o is None:
        return ORDER_SENTINEL
    try:
        # 有时 order 可能是字符串数字，尝试转换
        return int(o)
    except Exception:
        return ORDER_SENTINEL


def convert_block(det):
    """把单个 layout_dets 转换为 HTML（返回字符串或 None）"""
    cat = det.get("category_type", "")
    text = det.get("text", "")
    latex = det.get("latex", "")
    html = det.get("html", "")
    poly = det.get("poly", [])
    if not poly:
        return None

    x1, y1, x2, y2 = poly_to_bbox(poly)
    bbox = f'{x1} {y1} {x2} {y2}'

    # 递归处理 merge_list（按 order 排序）
    if "merge_list" in det and det["merge_list"]:
        parts = []
        for sub in sorted(det["merge_list"], key=order_key):
            sub_html = convert_block(sub)
            if sub_html:
                parts.append(sub_html)
        return "".join(parts) if parts else None

    # 按映射规则输出 HTML
    if cat in ["title", "figure_caption", "table_caption"]:
        return f'<h2 data-bbox="{bbox}">{text}</h2>'
    elif cat in ["text_block", "equation_caption", "code_txt", "reference"]:
        return f'<p data-bbox="{bbox}">{text}</p>'
    elif cat == "header":
        return f'<div class="header" data-bbox="{bbox}">{text}</div>'
    elif cat in ["footer", "page_number", "page_footnote", "figure_footnote", "table_footnote"]:
        return f'<div class="footer" data-bbox="{bbox}">{text}</div>'
    elif cat == "figure":
        return f'<div class="image" data-bbox="{bbox}"></div>'
    elif cat == "table":
        return f'<div class="table" data-bbox="{bbox}">{html}</div>'
    elif cat == "equation_isolated":
        return f'<div class="formula" data-bbox="{bbox}">{latex}</div>'
    else:
        return None


def convert_and_save(src_file, tgt_file):
    with open(src_file, "r", encoding="utf-8") as f_src, \
            open(tgt_file, "w", encoding="utf-8") as f_tgt:
        src_data = json.load(f_src)

        for page in src_data:
            image_path = page.get("page_info", {}).get("image_path", "")
            if not image_path:
                # 若没有 image_path，可以选择跳过或写空；这里跳过
                continue

            # 按 order 排序 layout_dets（None/Null 会被视为 ORDER_SENTINEL，排到最后）
            sorted_dets = sorted(page.get("layout_dets", []), key=order_key)

            html_blocks = []
            for det in sorted_dets:
                html = convert_block(det)
                if html:
                    html_blocks.append(html)

            if not html_blocks:
                continue

            # 单行 <body>（确保内部无换行）
            html_body = "<body>" + "".join(html_blocks) + "</body>"

            item = {
                "image": image_path,
                "prefix": "QwenVL HTML",
                "suffix": html_body
            }

            # 逐条写入（即时落盘）
            f_tgt.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ 转换完成（按阅读顺序并处理 None order），结果逐条写入: {tgt_file}")


if __name__ == "__main__":
    convert_and_save(src_file, tgt_file)
