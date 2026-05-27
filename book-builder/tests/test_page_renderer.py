"""Tests for page_renderer module"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from page_renderer import render_page, render_cover


def test_render_page_with_all_layers():
    page = {
        "id": 1,
        "bg": "images/bg_001.jpg",
        "mid": "images/mid_001.png",
        "fg": "images/fg_001.png",
        "text": "测试文字"
    }
    result = render_page(page, 1, "../css/style.css")

    assert '<?xml version="1.0" encoding="UTF-8"?>' in result
    assert 'xmlns="http://www.w3.org/1999/xhtml"' in result
    assert 'href="../css/style.css"' in result
    assert "images/bg_001.jpg" in result
    assert "images/mid_001.png" in result
    assert "images/fg_001.png" in result
    assert "测试文字" in result
    assert 'layer-bg' in result
    assert 'layer-mid' in result
    assert 'layer-fg' in result


def test_render_page_minimal():
    page = {"id": 2, "bg": "images/bg_002.jpg", "text": "只有背景"}
    result = render_page(page, 2, "../css/style.css")

    assert "images/bg_002.jpg" in result
    assert "只有背景" in result
    assert 'layer-mid' not in result
    assert 'layer-fg' not in result


def test_render_page_no_text():
    page = {"id": 3, "bg": "images/bg_003.jpg", "fg": "images/fg_003.png"}
    result = render_page(page, 3, "../css/style.css")

    assert "images/bg_003.jpg" in result
    assert 'story-text' not in result


def test_render_cover():
    result = render_cover("images/cover.jpg", "../css/style.css")
    assert "images/cover.jpg" in result
    assert "cover-page" in result


def test_special_chars_escaped():
    page = {"id": 4, "bg": "images/bg.jpg", "text": "a < b & c > d"}
    result = render_page(page, 4, "../css/style.css")
    assert "&lt;" in result
    assert "&amp;" in result
    assert "< b" not in result
    assert "&gt;" in result


if __name__ == "__main__":
    test_render_page_with_all_layers()
    test_render_page_minimal()
    test_render_page_no_text()
    test_render_cover()
    test_special_chars_escaped()
    print("All page_renderer tests passed!")
