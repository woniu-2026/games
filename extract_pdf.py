"""PDF 绘本 → 图片提取 + ePUB 生成（一键脚本）"""

import fitz
import json
import sys
from pathlib import Path

BOOK_JSON = str(Path(__file__).parent / "book-builder" / "sample_book.json")
BUILD_SCRIPT = str(Path(__file__).parent / "book-builder" / "build_epub.py")


def extract_pdf_pages(pdf_path: str, output_dir: str, scale: float = 2.0):
    """将 PDF 每页导出为 JPG 图片。

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        scale: 缩放比例 (2.0 = 2x，质量更高)
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    print(f"PDF 页数: {doc.page_count}")

    page_files = []
    for i in range(doc.page_count):
        page = doc[i]
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        filename = f"page_{i+1:02d}.jpg"
        filepath = out / filename
        pix.save(str(filepath))
        page_files.append(filename)
        print(f"  第{i+1}页 → {filename} ({pix.width}x{pix.height})")

    doc.close()
    return page_files


def build_book_json(page_files: list[str], title: str, output_path: str):
    """根据页面列表生成 book.json，每页只有背景图（占位）。"""
    pages = []
    for i, fname in enumerate(page_files):
        page = {
            "id": i + 1,
            "bg": f"images/{fname}",
            "text": ""  # 留空，后续可手工补充文字
        }
        pages.append(page)

    book = {
        "metadata": {
            "title": title,
            "creator": "",
            "language": "zh",
            "identifier": f"urn:uuid:{__import__('uuid').uuid4()}",
            "cover": f"images/{page_files[0]}"
        },
        "pages": pages
    }

    out = Path(output_path)
    out.write_text(json.dumps(book, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON 描述已生成: {out}")


def main():
    if len(sys.argv) < 2:
        pdf = input("请输入 PDF 路径 (或拖入文件): ").strip().strip('"').strip("'")
    else:
        pdf = sys.argv[1]

    pdf_path = Path(pdf)
    if not pdf_path.exists():
        print(f"错误: 文件不存在 — {pdf_path}")
        sys.exit(1)

    title = pdf_path.stem  # 文件名作为书名
    output_base = pdf_path.parent / pdf_path.stem
    images_dir = output_base / "images"

    print(f"\n正在导出: {pdf_path.name}")
    print(f"  输出目录: {output_base}")

    # 1. 提取页面
    page_files = extract_pdf_pages(str(pdf_path), str(images_dir))

    # 2. 复制封面（第一页是封面）
    cover_src = images_dir / page_files[0]
    cover_dst = images_dir / "cover.jpg"
    if cover_src.suffix != ".jpg":
        # 如果第一页不是jpg，用PIL转换
        from PIL import Image
        img = Image.open(cover_src)
        img.save(cover_dst)
    else:
        import shutil
        shutil.copy2(cover_src, cover_dst)
    print(f"  封面: {cover_dst}")

    # 3. 生成 book.json
    book_json = output_base / "book.json"
    build_book_json(page_files, title, str(book_json))

    # 4. 构建 ePUB
    epub_path = output_base / f"{pdf_path.stem}.epub"
    print(f"\n正在生成 ePUB...")
    import subprocess
    result = subprocess.run(
        ["python", BUILD_SCRIPT, str(book_json),
         "-o", str(epub_path), "--images", str(images_dir)],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        sys.exit(1)

    # 5. 验证
    import zipfile
    with zipfile.ZipFile(epub_path) as zf:
        names = zf.namelist()
    print(f"ePUB 生成成功!")
    print(f"  文件: {epub_path} ({epub_path.stat().st_size / 1024:.1f} KB)")
    print(f"  包含 {len(names)} 个文件")
    print(f"\n提示：")
    print(f"  - 用 Apple Books 打开 {epub_path} 即可观看")
    print(f"  - 编辑 {book_json} 可以补充每页文字和前景/中景图层")
    print(f"  - 用 rembg 做分层: pip install rembg && rembg -i {images_dir} -o {images_dir}/fg")


if __name__ == "__main__":
    main()
