"""CLI tests for build_epub.py"""

import sys, json, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from build_epub import load_book


def test_load_book_valid():
    data = {
        "metadata": {"title": "测试"},
        "pages": [{"id": 1, "bg": "test.jpg", "text": "hello"}]
    }
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, f, ensure_ascii=False)
    f.close()

    meta, pages = load_book(f.name)
    assert meta["title"] == "测试"
    assert len(pages) == 1
    Path(f.name).unlink()


def test_load_book_missing_metadata():
    data = {"pages": []}
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, f)
    f.close()

    try:
        load_book(f.name)
        assert False, "Should have exited"
    except SystemExit:
        pass
    Path(f.name).unlink()


def test_load_book_missing_pages():
    data = {"metadata": {"title": "测试"}}
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, f)
    f.close()

    try:
        load_book(f.name)
        assert False, "Should have exited"
    except SystemExit:
        pass
    Path(f.name).unlink()


if __name__ == "__main__":
    test_load_book_valid()
    test_load_book_missing_metadata()
    test_load_book_missing_pages()
    print("All CLI tests passed!")
