from importlib.resources import files
from importlib.resources.abc import Traversable

from .data import Dataset as Dataset, create_test_models as create_test_models

_package_root = files(__package__)


def load_resource(path: str) -> Traversable:
    """Return a Path-like traversable to a file in this package."""
    return _package_root.joinpath(path)
