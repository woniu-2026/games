"""ePUB3 package builder — constants and templates for animated picture books"""

import os
import shutil
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
from page_renderer import render_page, render_cover

# ── ePUB3 文件布局常量 ──
META_INF = "META-INF"
OEBPS = "OEBPS"
XHTML_DIR = "xhtml"
CSS_DIR = "css"
IMAGE_DIR = "images"

# ── 容器模板 ──
CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

# ── CSS 模板：包含视差动效 ──
STYLE_CSS = """@charset "UTF-8";

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000;
}

/* 场景容器 */
.scene {
  position: relative;
  width: 100%;
  height: 100vh;
  perspective: 800px;
  overflow: hidden;
  background: #fff;
}

/* 通用图层 */
.layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

/* 背景层：视差效果 */
.layer-bg {
  /* 翻页时产生视差位移 */
}

/* 中景层 */
.layer-mid {
  /* 可选的中间层，静止 */
}

/* 前景层：浮动呼吸动画 */
.layer-fg {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-5px); }
}

/* 文字叠层 */
.text-overlay {
  position: absolute;
  bottom: 8%;
  left: 6%;
  right: 6%;
  padding: 18px 24px;
  background: rgba(0, 0, 0, 0.45);
  border-radius: 12px;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.story-text {
  margin: 0;
  font-size: 1.2em;
  line-height: 1.6;
  color: #fff;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 封面专用 */
.cover-page {
  width: 100%;
  height: 100vh;
  background-size: cover;
  background-position: center;
}

/* 翻页视差：Apple Books 通过 @page 控制 */
@page {
  margin: 0;
  padding: 0;
}
"""

# ── 打包函数 ──


def build_epub(book_meta: dict, pages: list[dict], output_path: str | Path,
               image_source_dir: str | Path = ".") -> Path:
    """构建完整的 .epub 文件。

    Args:
        book_meta: 书籍元数据字典（title, creator, language, identifier, cover）
        pages: 页面列表字典，每个包含 bg/mid/fg/text
        output_path: 输出的 .epub 文件路径
        image_source_dir: 图片文件所在目录

    Returns:
        生成的 .epub 文件 Path
    """
    output_path = Path(output_path)
    image_source = Path(image_source_dir)
    epub_root = output_path.parent / f".epub_staging_{output_path.stem}"

    try:
        _create_structure(epub_root, book_meta, pages, image_source)
        _pack_epub(epub_root, output_path)
    finally:
        if epub_root.exists():
            shutil.rmtree(epub_root)

    return output_path


def _create_structure(epub_root: Path, meta: dict, pages: list[dict],
                      image_source: Path):
    """创建 ePUB 临时目录结构并写入所有文件。"""

    # 创建目录
    dirs = {
        "META-INF": epub_root / META_INF,
        "OEBPS": epub_root / OEBPS,
        "XHTML": epub_root / OEBPS / XHTML_DIR,
        "CSS": epub_root / OEBPS / CSS_DIR,
        "IMAGES": epub_root / OEBPS / IMAGE_DIR,
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # 1. container.xml
    (dirs["META-INF"] / "container.xml").write_text(CONTAINER_XML, encoding="utf-8")

    # 2. style.css
    (dirs["CSS"] / "style.css").write_text(STYLE_CSS, encoding="utf-8")

    # 3. 封面页
    cover_image = meta.get("cover", "")
    if cover_image:
        # XHTML 在 xhtml/ 子目录中，图片路径需加 ../ 前缀
        cover_xhtml = render_cover(f"../{cover_image}", f"../{CSS_DIR}/style.css")
        (dirs["XHTML"] / "cover.xhtml").write_text(cover_xhtml, encoding="utf-8")

    # 4. 每页 xhtml
    toc_entries = []
    for i, page in enumerate(pages):
        page_num = page.get("id", i + 1)
        xhtml_name = f"page_{page_num:03d}.xhtml"
        # 复制 page dict 并给图片路径加 ../ 前缀（从 xhtml/ 指向 images/）
        page_copy = dict(page)
        for key in ("bg", "mid", "fg"):
            if page_copy.get(key):
                page_copy[key] = f"../{page_copy[key]}"
        xhtml_content = render_page(page_copy, f"../{CSS_DIR}/style.css")
        (dirs["XHTML"] / xhtml_name).write_text(xhtml_content, encoding="utf-8")
        toc_entries.append((xhtml_name, f"第{page_num}页"))

    # 5. toc.xhtml
    cover_label = "封面" if cover_image else None
    toc_xhtml = _build_toc(
        meta.get("title", "Book"),
        cover_label,
        toc_entries
    )
    (dirs["XHTML"] / "toc.xhtml").write_text(toc_xhtml, encoding="utf-8")

    # 6. content.opf
    opf = _build_opf(meta, pages, cover_image)
    (epub_root / OEBPS / "content.opf").write_text(opf, encoding="utf-8")

    # 7. 复制图片
    if image_source.exists():
        for f in image_source.iterdir():
            if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                shutil.copy2(f, dirs["IMAGES"] / f.name)


def _build_toc(title: str, cover_label: str | None, entries: list[tuple[str, str]]) -> str:
    """生成 toc.xhtml 导航页面。"""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">',
        "  <head>",
        f'    <title>{escape(title)}</title>',
        "  </head>",
        "  <body>",
        '    <nav epub:type="toc">',
        f'      <h1>{escape(title)}</h1>',
        "      <ol>",
    ]
    if cover_label:
        lines.append(f'        <li><a href="cover.xhtml">{escape(cover_label)}</a></li>')
    for xhtml_name, label in entries:
        lines.append(f'        <li><a href="{xhtml_name}">{escape(label)}</a></li>')
    lines.extend([
        "      </ol>",
        "    </nav>",
        "  </body>",
        "</html>",
    ])
    return "\n".join(lines) + "\n"


def _build_opf(meta: dict, pages: list[dict], cover_image: str) -> str:
    """生成 content.opf 元数据文件。"""
    title = escape(meta.get("title", "Untitled"))
    creator = escape(meta.get("creator", "Unknown"))
    lang = escape(meta.get("language", "en"))
    identifier = escape(meta.get("identifier", f"urn:uuid:{uuid.uuid4()}"))

    # 收集清单
    manifest = []
    spine = []

    # CSS
    manifest.append((f"{CSS_DIR}/style.css", "text/css", "style.css"))

    # 封面页
    if cover_image:
        manifest.append((f"{XHTML_DIR}/cover.xhtml", "application/xhtml+xml", "cover-xhtml"))
        spine.append("cover-xhtml")
        basename = os.path.basename(cover_image)
        img_id = os.path.splitext(basename)[0]
        manifest.append((f"{IMAGE_DIR}/{basename}", _mime_for(cover_image), img_id))

    # 页面
    for i, page in enumerate(pages):
        page_num = page.get("id", i + 1)
        xhtml_name = f"page_{page_num:03d}.xhtml"
        page_id = f"page-{page_num:03d}"
        manifest.append((f"{XHTML_DIR}/{xhtml_name}", "application/xhtml+xml", page_id))
        spine.append(page_id)

        for key in ("bg", "mid", "fg"):
            img_path = page.get(key)
            if img_path:
                img_id = f"img-{page_num:03d}-{key}"
                manifest.append((f"{IMAGE_DIR}/{os.path.basename(img_path)}", _mime_for(img_path), img_id))

    # TOC
    manifest.append((f"{XHTML_DIR}/toc.xhtml", "application/xhtml+xml", "toc"))
    spine.append("toc")

    # 构建 XML
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">',
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">',
        f'    <dc:identifier id="book-id">{identifier}</dc:identifier>',
        f'    <dc:title>{title}</dc:title>',
        f'    <dc:creator>{creator}</dc:creator>',
        f'    <dc:language>{lang}</dc:language>',
        '    <meta property="rendition:layout">pre-paginated</meta>',
        '    <meta property="rendition:orientation">auto</meta>',
        '    <meta property="rendition:spread">none</meta>',
        "  </metadata>",
        "  <manifest>",
    ]
    for href, media_type, item_id in manifest:
        lines.append(f'    <item id="{item_id}" href="{href}" media-type="{media_type}"/>')
    lines.extend([
        "  </manifest>",
        "  <spine>",
    ])
    for item_id in spine:
        lines.append(f'    <itemref idref="{item_id}"/>')
    lines.extend([
        "  </spine>",
        "</package>",
    ])
    return "\n".join(lines) + "\n"


def _mime_for(path: str) -> str:
    """根据文件扩展名返回 MIME 类型。"""
    ext = os.path.splitext(path)[1].lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".css": "text/css",
        ".xhtml": "application/xhtml+xml",
        ".xml": "application/xml",
    }.get(ext, "application/octet-stream")


def _pack_epub(epub_root: Path, output_path: Path):
    """将临时目录打包为 .epub（标准 ZIP 格式）。"""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype 必须是第一个文件，且不压缩
        zf.writestr("mimetype", "application/epub+zip",
                     compress_type=zipfile.ZIP_STORED)

        for f in sorted(epub_root.rglob("*")):
            if f.is_file():
                arcname = str(f.relative_to(epub_root))
                zf.write(f, arcname)
