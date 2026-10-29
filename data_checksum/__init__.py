"""Create and verify SHA-256 manifests for research datasets."""
from .core import hash_file, build_manifest, write_manifest, read_manifest, verify

__version__ = "0.1.0"
__all__ = ["hash_file", "build_manifest", "write_manifest", "read_manifest", "verify"]
