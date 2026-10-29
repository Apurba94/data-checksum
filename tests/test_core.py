import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from data_checksum.cli import main
from data_checksum.core import build_manifest, hash_file, read_manifest, verify, write_manifest


def write(root, rel, data):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(data)
    return p


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        write(self.root, "raw/a.csv", b"abc")
        write(self.root, "raw/b.csv", b"hello")
        write(self.root, ".git/config", b"x")
        write(self.root, "__pycache__/m.pyc", b"x")

    def tearDown(self):
        self.tmp.cleanup()

    def test_hash_known_value(self):
        self.assertEqual(hash_file(os.path.join(self.root, "raw", "a.csv")),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_build_excludes_and_sha256sum_format(self):
        m = build_manifest(self.root)
        self.assertEqual(sorted(m), ["raw/a.csv", "raw/b.csv"])
        path = write_manifest(m, self.root)
        with open(path, encoding="utf-8") as fh:
            first = fh.readline()
        self.assertTrue(first.startswith("ba7816bf") and first.rstrip().endswith("  raw/a.csv"))
        self.assertEqual(read_manifest(path)["raw/b.csv"], m["raw/b.csv"]["hash"])
        self.assertEqual(read_manifest(os.path.join(self.root, "MANIFEST.json")), read_manifest(path))

    def test_verify_detects_changes(self):
        write_manifest(build_manifest(self.root), self.root)
        exp = read_manifest(os.path.join(self.root, "MANIFEST.sha256"))
        write(self.root, "raw/a.csv", b"abd")
        os.remove(os.path.join(self.root, "raw", "b.csv"))
        write(self.root, "raw/c.csv", b"new")
        res = verify(self.root, exp)
        self.assertEqual((res["changed"], res["missing"], res["new"]), (["raw/a.csv"], ["raw/b.csv"], ["raw/c.csv"]))

    def test_incremental_reuse(self):
        m = build_manifest(self.root)
        m["raw/a.csv"]["hash"] = "stale-but-reused"
        m2 = build_manifest(self.root, previous=m)
        self.assertEqual(m2["raw/a.csv"]["hash"], "stale-but-reused")

    def test_cli(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["create", self.root]), 0)
            self.assertEqual(main(["verify", self.root]), 0)
            write(self.root, "raw/b.csv", b"tampered")
            self.assertEqual(main(["verify", self.root]), 1)


if __name__ == "__main__":
    unittest.main()
