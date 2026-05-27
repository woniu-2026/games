"""Integration tests for epub_builder"""

import sys, os, json, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from epub_builder import build_epub, _build_opf, _build_toc, _mime_for


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


def test_mime_for():
    assert _mime_for("test.jpg") == "image/jpeg"
    assert _mime_for("test.png") == "image/png"
    assert _mime_for("style.css") == "text/css"
    assert _mime_for("test.xhtml") == "application/xhtml+xml"


def test_build_opf_has_rendition_meta():
    opf = _build_opf(SAMPLE_META, SAMPLE_PAGES, "images/cover.jpg")
    assert 'rendition:layout">pre-paginated' in opf
    assert 'rendition:orientation">auto' in opf
    assert "dc:title" in opf
    assert "测试绘本" in opf
    assert "cover-xhtml" in opf


def test_build_toc_has_entries():
    toc = _build_toc("测试", "封面", [("page_001.xhtml", "第1页")])
    assert "cover.xhtml" in toc
    assert "page_001.xhtml" in toc
    assert "第1页" in toc


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

    assert names[0] == "mimetype"
    assert "META-INF/container.xml" in names
    assert "OEBPS/content.opf" in names
    assert "OEBPS/xhtml/cover.xhtml" in names
    assert "OEBPS/xhtml/page_001.xhtml" in names
    assert "OEBPS/xhtml/page_002.xhtml" in names
    assert "OEBPS/xhtml/toc.xhtml" in names
    assert "OEBPS/css/style.css" in names
    assert "OEBPS/images/bg_001.jpg" in names
    assert "OEBPS/images/fg_001.png" in names
    assert "OEBPS/images/bg_002.jpg" in names

    with zipfile.ZipFile(result, "r") as zf:
        info = zf.getinfo("mimetype")
        assert info.compress_type == zipfile.ZIP_STORED


if __name__ == "__main__":
    import tempfile
    test_mime_for()
    test_build_opf_has_rendition_meta()
    test_build_toc_has_entries()
    with tempfile.TemporaryDirectory() as td:
        test_build_epub_integration(Path(td))
    print("All epub_builder tests passed!")
