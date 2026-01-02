"""Version handling"""
import os

__version_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../version.txt")


def _get_version():
    """Get version from 'version.txt'"""
    if not os.path.exists(__version_file):
        return None
    try:
        with open(__version_file, "r", encoding="utf-8") as f:
            result = f.read()
    except OSError:
        result = None
    return result


version = _get_version()
