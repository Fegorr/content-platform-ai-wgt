import os
import subprocess
import sys
from pathlib import Path

from src.db.mongo_utils import strip_mongo_id

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_strip_mongo_id_removes_only_id():
    """strip_mongo_id drops _id and keeps every other key and value."""
    document = {"_id": "abc", "id": "1", "title": "Intro", "duration": 30}

    result = strip_mongo_id(document)

    assert result == {"id": "1", "title": "Intro", "duration": 30}


def test_strip_mongo_id_without_id_returns_new_dict():
    """A document with no _id comes back equal but as a different dict."""
    document = {"id": "1", "title": "Intro"}

    result = strip_mongo_id(document)

    assert result == document
    assert result is not document


def test_strip_mongo_id_does_not_change_input():
    """The dict passed in still has its _id and other keys after the call."""
    document = {"_id": "abc", "id": "1", "title": "Intro"}

    strip_mongo_id(document)

    assert document == {"_id": "abc", "id": "1", "title": "Intro"}


def test_strip_mongo_id_empty_dict():
    """An empty dict gives an empty dict."""
    assert strip_mongo_id({}) == {}


def test_import_mongo_utils_without_pymongo():
    """Importing src.db.mongo_utils does not load pymongo."""
    code = (
        "import sys\n"
        "import src.db.mongo_utils\n"
        "assert 'pymongo' not in sys.modules\n"
    )
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT)}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
