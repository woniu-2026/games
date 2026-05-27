"""Integration tests for epub_builder (ebooklib)"""

import sys, os, json, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from epub_builder import build_epub


SAMPLE_META = {
    "title": "测试绘本",
    "creator": "测试作者",
    "language": "zh",
    "identifier": "urn:uuid:test-0000-0000-0000-000000000001",
    "cover": "images/cover.jpg",
}

SAMPLE_PAGES = [
    {"id": 1, "bg": "images/bg_001.jpg", "fg": "images/fg_001.png", "text": "第一页"},
    {"id": 2, "bg": "images/bg_002.jpg", "text": "第二页"},
]


def test_build_epub_integration(tmp_path):
    """端到端测试：生成 ePUB 并验证内部结构。"""
    # 创建临时图片
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    for name in ["cover.jpg", "bg_001.jpg", "fg_001.png", "bg_002.jpg"]:
        (img_dir / name).write_text("fake-image-data")

    output = tmp_path / "output.epub"
    result = build_epub(SAMPLE_META, SAMPLE_PAGES, output, img_dir)

    assert result.exists()
    assert result.suffix == ".epub"

    with zipfile.ZipFile(result, "r") as zf:
        names = zf.namelist()

    # Standard ePUB 3 structure
    assert names[0] == "mimetype"
    assert "META-INF/container.xml" in names
    assert "EPUB/content.opf" in names
    assert "EPUB/xhtml/cover.xhtml" in names
    assert "EPUB/xhtml/page_001.xhtml" in names
    assert "EPUB/xhtml/page_002.xhtml" in names
    assert "EPUB/style.css" in names
    assert "EPUB/images/bg_001.jpg" in names
    assert "EPUB/images/fg_001.png" in names
    assert "EPUB/images/bg_002.jpg" in names

    # mimetype must be uncompressed
    with zipfile.ZipFile(result, "r") as zf:
        info = zf.getinfo("mimetype")
        assert info.compress_type == zipfile.ZIP_STORED

    # Verify OPF contains rendition metadata
    with zipfile.ZipFile(result, "r") as zf:
        opf = zf.read("EPUB/content.opf").decode("utf-8")
    assert 'rendition:layout">pre-paginated' in opf
    assert 'rendition:orientation">auto' in opf
    assert "dc:title" in opf
    assert "测试绘本" in opf

    # Verify TOC links exist in OPF spine
    assert "page_001.xhtml" in opf
    assert "page_002.xhtml" in opf


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        test_build_epub_integration(Path(td))
    print("All epub_builder tests passed!")
