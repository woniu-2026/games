"""ePUB3 package builder — uses ebooklib for spec-compliant output"""

import os
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

from ebooklib import epub
from page_renderer import render_page, render_cover

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

.scene {
  position: relative;
  width: 100%;
  height: 100vh;
  perspective: 800px;
  overflow: hidden;
  background: #fff;
}

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

.layer-bg {
  /* 翻页时产生视差位移 */
}

.layer-mid {
  /* 可选的中间层，静止 */
}

.layer-fg {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-5px); }
}

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

.cover-page {
  width: 100%;
  height: 100vh;
  background-size: cover;
  background-position: center;
}

@page {
  margin: 0;
  padding: 0;
  size: 1440px 1080px;
}

@media amzn-mobi {
  @page { margin: 0 !important; }
}

body {
  margin: 0;
  padding: 0;
  widows: 0;
  orphans: 0;
}
"""


def build_epub(book_meta: dict, pages: list[dict], output_path: str | Path,
               image_source_dir: str | Path = ".") -> Path:
    """构建完整的 .epub 文件（使用 ebooklib）。

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

    # 创建 EpubBook
    book = epub.EpubBook()

    # ── 元数据 ──
    book.set_identifier(book_meta.get("identifier", str(uuid.uuid4())))
    book.set_title(book_meta.get("title", "Untitled"))
    book.set_language(book_meta.get("language", "zh"))
    if creator := book_meta.get("creator"):
        book.add_author(creator)

    # ── 渲染模式：pre-paginated（固定版面，单页显示） ──
    book.add_metadata(None, "meta", "pre-paginated", {
        "property": "rendition:layout"
    })
    book.add_metadata(None, "meta", "auto", {
        "property": "rendition:orientation"
    })
    book.add_metadata(None, "meta", "none", {
        "property": "rendition:spread"
    })
    book.add_metadata(None, "meta", "ltr", {
        "property": "rendition:page-progression-direction"
    })

    # ── CSS ──
    css_item = epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=STYLE_CSS.encode("utf-8")
    )
    book.add_item(css_item)

    # ── 封面图片 ──
    cover_image = book_meta.get("cover", "")
    cover_ext = ".jpg"
    if cover_image:
        cover_img_path = image_source / os.path.basename(cover_image)
        if cover_img_path.exists():
            with open(cover_img_path, "rb") as f:
                img_data = f.read()
            cover_ext = cover_img_path.suffix.lower()
            mime = "image/jpeg" if cover_ext in (".jpg", ".jpeg") else "image/png"
            cover_img_item = epub.EpubImage(
                uid="cover-img",
                file_name=f"images/cover-img{cover_ext}",
                media_type=mime,
                content=img_data
            )
            book.add_item(cover_img_item)
            # 标记封面图片（ePUB2 兼容）
            book.add_metadata(None, "meta", "cover-img", {"name": "cover"})

    # ── 处理每页图片并添加为 EpubImage ──
    page_images = {}  # (page_num, key) -> file_name
    for i, page in enumerate(pages):
        page_num = page.get("id", i + 1)
        for key in ("bg", "mid", "fg"):
            img_path = page.get(key)
            if img_path:
                basename = os.path.basename(img_path)
                img_file = image_source / basename
                if img_file.exists():
                    img_id = f"img-{page_num:03d}-{key}"
                    ext = img_file.suffix.lower()
                    mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
                    with open(img_file, "rb") as f:
                        data = f.read()
                    item = epub.EpubImage(
                        uid=img_id,
                        file_name=f"images/{basename}",
                        media_type=mime,
                        content=data
                    )
                    book.add_item(item)
                    page_images[(page_num, key)] = f"images/{basename}"

    # ── 构建每页 XHTML ──
    spine = []
    toc_items = []

    # 封面页
    if cover_image:
        cover = epub.EpubHtml(
            title="封面",
            file_name="cover.xhtml",
            lang=book_meta.get("language", "zh")
        )
        cover.add_meta(name="viewport", content="width=1440, height=1080")
        cover_content = render_cover(f"images/cover-img{cover_ext}", "style.css")
        cover.content = cover_content.encode("utf-8")
        cover.add_item(css_item)
        book.add_item(cover)
        spine.append(cover)
        toc_items.append(epub.Link("cover.xhtml", "封面", "cover-nav"))

    # 内容页
    for i, page in enumerate(pages):
        page_num = page.get("id", i + 1)
        xhtml_name = f"page_{page_num:03d}.xhtml"

        # 图片路径相对于 EPUB/ 根目录
        page_copy = dict(page)
        for key in ("bg", "mid", "fg"):
            if page_copy.get(key):
                filename = os.path.basename(page_copy[key])
                page_copy[key] = f"images/{filename}"

        xhtml_content = render_page(page_copy, "style.css")

        chapter = epub.EpubHtml(
            title=f"第{page_num}页",
            file_name=xhtml_name,
            lang=book_meta.get("language", "zh")
        )
        chapter.add_meta(name="viewport", content="width=1440, height=1080")
        chapter.content = xhtml_content.encode("utf-8")
        chapter.add_item(css_item)
        book.add_item(chapter)
        spine.append(chapter)
        toc_items.append(epub.Link(xhtml_name, f"第{page_num}页", f"page-{page_num:03d}"))

    # ── 设置目录 ──
    book.toc = toc_items

    # ── 设置 spine ──
    book.spine = spine

    # ── 写入 ePUB ──
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book, {})

    return output_path
