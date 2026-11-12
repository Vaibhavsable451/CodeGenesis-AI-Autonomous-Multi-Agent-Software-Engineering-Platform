import io
import zipfile

import pytest

from core import code_intel, ingestion


def test_valid_github_url():
    assert ingestion.validate_github_url("https://github.com/psf/requests") == ("psf", "requests")


@pytest.mark.parametrize("bad", ["http://github.com/a/b", "https://evil.com/a/b", "https://github.com/a"])
def test_invalid_github_url(bad):
    with pytest.raises(ValueError):
        ingestion.validate_github_url(bad)


def test_zip_slip_blocked():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("../evil.txt", "x")
    with pytest.raises(ValueError):
        ingestion.extract_zip(buf.getvalue())


def test_zip_ingest_and_tree():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/main.py", "def f(x):\n    if x:\n        return eval(x)\n")
        z.writestr("node_modules/skip.js", "1")
    rid = ingestion.extract_zip(buf.getvalue())
    files = ingestion.build_file_tree(rid)
    assert [f["path"] for f in files] == ["app/main.py"]
    assert files[0]["language"] == "python"


def test_code_intel():
    src = "import os\n\ndef f(x):\n    if x:\n        return eval(x)\n    return 1\n"
    info = code_intel.analyze_python(src, "a.py")
    assert info["functions"][0]["complexity"] == 2
    assert any(f["title"] == "Use of eval()" for f in code_intel.security_scan(src, "a.py"))
