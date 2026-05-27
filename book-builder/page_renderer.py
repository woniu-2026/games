"""Per-page XHTML generation from page data"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.sax.saxutils import escape

XHTML_NS = "http://www.w3.org/1999/xhtml"

def render_page(page: dict, page_num: int, css_path: str) -> str:
    """生成单个跨页的 XHTML 内容。

    Args:
        page: 页面数据字典，包含 bg/mid/fg/image路径 和 text
        page_num: 页码（用于生成 id）
        css_path: 相对于 OEBPS/xhtml/ 到 style.css 的路径

    Returns:
        格式化的 XHTML 字符串
    """
    has_bg = bool(page.get("bg"))
    has_mid = bool(page.get("mid"))
    has_fg = bool(page.get("fg"))
    text = page.get("text", "")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<html xmlns="{XHTML_NS}">',
        "  <head>",
        f'    <meta charset="utf-8"/>',
        f'    <link rel="stylesheet" href="{css_path}"/>',
        "  </head>",
        "  <body>",
        '    <div class="scene">',
    ]

    # 背景层
    if has_bg:
        bg_url = escape(page["bg"])
        lines.append(f'      <div class="layer layer-bg" style="background-image: url({bg_url})"></div>')

    # 中景层
    if has_mid:
        mid_url = escape(page["mid"])
        lines.append(f'      <div class="layer layer-mid" style="background-image: url({mid_url})"></div>')

    # 前景层
    if has_fg:
        fg_url = escape(page["fg"])
        lines.append(f'      <div class="layer layer-fg" style="background-image: url({fg_url})"></div>')

    # 文字
    if text:
        lines.append('      <div class="text-overlay">')
        lines.append(f'        <p class="story-text">{escape(text)}</p>')
        lines.append("      </div>")

    lines.extend([
        "    </div>",
        "  </body>",
        "</html>",
    ])

    return "\n".join(lines) + "\n"


def render_cover(cover_image: str, css_path: str) -> str:
    """生成封面页 XHTML。"""
    img_url = escape(cover_image)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="{XHTML_NS}">
  <head>
    <meta charset="utf-8"/>
    <link rel="stylesheet" href="{css_path}"/>
  </head>
  <body>
    <div class="cover-page" style="background-image: url({img_url})"></div>
  </body>
</html>
"""
