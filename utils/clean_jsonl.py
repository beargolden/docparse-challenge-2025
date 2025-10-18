#!/usr/bin/env python3
import json
import re
import sys


def format_html_table(html: str) -> str:
    """
    在 <table>...</table> 内部：
    1. 删除 <thead>、<tbody>、<tfoot>；
    2. 将 <th> 替换为 <td>；
    3. 在相邻标签之间添加换行符；
    4. 对空或“伪空”单元格（仅空格/&nbsp;）不添加换行；
    5. 保持其他 HTML 不变。
    """

    def process_table(match):
        table_html = match.group(0)
        table_html = re.sub(r"</?(thead|tbody|tfoot)>", "", table_html, flags=re.IGNORECASE)
        table_html = re.sub(r"<\s*th(\s|>)", r"<td\1", table_html, flags=re.IGNORECASE)
        table_html = re.sub(r"</\s*th\s*>", "</td>", table_html, flags=re.IGNORECASE)
        table_html = re.sub(r"><", ">\n<", table_html)
        table_html = re.sub(r"<td([^>]*)>(?:\s|&nbsp;)*</td>", r"<td\1></td>", table_html, flags=re.IGNORECASE)
        table_html = re.sub(r"\n+", "\n", table_html)
        return table_html.strip()

    return re.sub(r"<table.*?</table>", process_table, html, flags=re.DOTALL | re.IGNORECASE)


def clean_markdown_inside_html(html: str) -> str:
    """
    删除 HTML 标签内的 Markdown 标记符：
    - 标题符号 (#, ##, ###...)
    - 列表符号 (-, *, +, 1.)
    - 粗体、斜体 (**text**, *text*, __text__, _text_)
    """

    def remove_md_in_text(text):
        # 删除标题符号
        text = re.sub(r'\s*#{1,6}\s*', '', text)

        # 删除列表标记
        text = re.sub(r'^\s*([-*+]\s+|\d+\.\s+)', '', text)

        # 删除粗体与斜体
        text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)  # **text** / __text__
        text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)  # *text* / _text_

        return text

    # 对每段 HTML 以外的文本执行清理
    segments = re.split(r'(<[^>]+>)', html)
    cleaned_segments = [
        remove_md_in_text(seg) if not seg.startswith('<') else seg
        for seg in segments
    ]
    return ''.join(cleaned_segments)


def normalize_text(text: str) -> str:
    """
    文本规范化处理：
    (1) 删除中文之间、中英文之间的空格；
    (2) 保留英文单词之间的空格；
    (3) 替换全角标点为半角（保留“。”）；
    (4) 删除所有中英文标点符号前后的空格。
    """

    # 删除中文与中文之间的空格
    text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)

    # 删除中文与英文/数字之间的空格
    text = re.sub(r'([\u4e00-\u9fff])\s+([A-Za-z0-9])', r'\1\2', text)
    text = re.sub(r'([A-Za-z0-9])\s+([\u4e00-\u9fff])', r'\1\2', text)

    # 全角标点到半角标点映射（不包括“。”）
    punct_map = {
        '，': ',',
        '；': ';',
        '：': ':',
        '？': '?',
        '！': '!',
        '（': '(',
        '）': ')',
        '【': '[',
        '】': ']',
    }
    for cn_punct, en_punct in punct_map.items():
        text = text.replace(cn_punct, en_punct)

    # 删除所有中英文标点符号前后的空格
    text = re.sub(r'\s*([,.;:!?()\[\]{}，。；：！？（）【】])\s*', r'\1', text)

    return text


def clean_jsonl(input_file, output_file, field="suffix"):
    """
    清理 JSONL 文件中指定字段的 HTML、Markdown 和文本内容。
    """
    with open(input_file, "r", encoding="utf-8") as f_in, \
            open(output_file, "w", encoding="utf-8") as f_out:
        for line in f_in:
            if not line.strip():
                continue
            data = json.loads(line)
            if field in data and isinstance(data[field], str):
                text = data[field].replace("\n", "")

                # 表格格式化
                if "<table" in text and "</table>" in text:
                    text = format_html_table(text)

                # 删除 HTML 内部 Markdown 符号
                text = clean_markdown_inside_html(text)

                # 文本规范化
                text = normalize_text(text)

                data[field] = text

            f_out.write(json.dumps(data, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python clean_jsonl.py 输入文件 输出文件 [字段名]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    field = sys.argv[3] if len(sys.argv) > 3 else "suffix"

    clean_jsonl(input_file, output_file, field)
    print(f"处理完成！已生成 {output_file}")
