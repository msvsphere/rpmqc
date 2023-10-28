import os.path

__all__ = ['normalize_path']


def normalize_path(path: str) -> str:
    """
    Returns an absolute path with all variables expanded.

    Args:
        path: path to be normalized.

    Returns:
        Normalized path.
    """
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
