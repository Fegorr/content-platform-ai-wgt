import importlib

import pytest

PACKAGES = [
    "src",
    "src.models",
    "src.schemas",
    "src.db",
    "src.services",
    "src.auth",
    "src.routers",
    "src.utils",
]


@pytest.mark.parametrize("package", PACKAGES)
def test_package_can_be_imported(package):
    """Each src package can be imported."""
    assert importlib.import_module(package) is not None
