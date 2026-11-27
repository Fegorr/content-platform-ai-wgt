import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.db.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.utils.dependencies import get_auth_service, get_user_repository

ROOT = Path(__file__).resolve().parent.parent

IMPORT_CHECK = """
from unittest import mock
import src.db.database as database
with mock.patch.object(database, "get_client") as get_client:
    import src.utils.dependencies
    import src.routers.auth
    import src.main
    assert not get_client.called, "get_client was called at import"
"""


def test_get_user_repository_uses_users_collection():
    """get_user_repository returns a UserRepository built on the users collection."""
    collection = Mock()
    collection.find_one.return_value = None
    with patch("src.utils.dependencies.get_users_collection", return_value=collection) as getter:
        repository = get_user_repository()
    getter.assert_called_once_with()
    assert isinstance(repository, UserRepository)
    repository.get_by_id("known-id")
    collection.find_one.assert_called_once_with({"id": "known-id"})


def test_get_auth_service_uses_given_repository():
    """get_auth_service returns an AuthService that uses the repository it was given."""
    repository = Mock()
    repository.get_by_id.return_value = None
    service = get_auth_service(repository)
    assert isinstance(service, AuthService)
    service.get_user_by_id("some-id")
    repository.get_by_id.assert_called_once_with("some-id")


def test_import_app_modules_without_connecting():
    """Importing the wiring, auth router and main modules never calls get_client or needs MONGODB_URI."""
    env = {k: v for k, v in os.environ.items() if k != "MONGODB_URI"}
    env["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, "-c", IMPORT_CHECK],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
