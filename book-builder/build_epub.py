#!/usr/bin/env python3
"""ePUB3 视差动效绘本生成器 — CLI 入口

用法:
  python build_epub.py sample_book.json -o output.epub
  python build_epub.py sample_book.json -o output.epub --images ./my_images
"""

import argparse
import json
import sys
from pathlib import Path

# 确保能从同级导入模块
sys.path.insert(0, str(Path(__file__).parent))

from epub_builder import build_epub


def load_book(json_path: str | Path) -> tuple[dict, list[dict]]:
    """加载并验证书籍 JSON 文件。

    Returns:
        (metadata dict, pages list)
    """
    path = Path(json_path)
    if not path.exists():
        print(f"错误: 文件不存在 — {path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 — {e}", file=sys.stderr)
        sys.exit(1)

    if "metadata" not in data:
        print("错误: JSON 缺少 'metadata' 字段", file=sys.stderr)
        sys.exit(1)
    if "pages" not in data or not isinstance(data["pages"], list):
        print("错误: JSON 缺少 'pages' 数组", file=sys.stderr)
        sys.exit(1)

    return data["metadata"], data["pages"]


def main():
    parser = argparse.ArgumentParser(
        description="ePUB3 视差动效绘本生成器 — 将分层图片 + 文本打包为动画电子书"
    )
    parser.add_argument("book_json", type=str,
                        help="书籍描述 JSON 文件路径")
    parser.add_argument("-o", "--output", type=str, default="output.epub",
                        help="输出 .epub 文件路径 (default: output.epub)")
    parser.add_argument("--images", type=str, default=".",
                        help="图片文件所在目录 (default: 当前目录)")

    args = parser.parse_args()

    metadata, pages = load_book(args.book_json)
    output = Path(args.output)

    print(f"📖 开始生成: {metadata.get('title', 'Untitled')}")
    print(f"  页数: {len(pages)}")
    print(f"  输出: {output}")

    result = build_epub(metadata, pages, output, args.images)

    size = result.stat().st_size
    print(f"✅ 生成成功! ({size / 1024:.1f} KB)")
    print(f"  文件: {result.resolve()}")


if __name__ == "__main__":
    main()
