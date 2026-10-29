"""Manifests in the standard `sha256sum` format plus a JSON sidecar with sizes and timestamps."""
import fnmatch
import hashlib
import json
import os
import time

DEFAULT_EXCLUDE = (".git/*", "*/.git/*", "__pycache__/*", "*/__pycache__/*", "*.pyc", ".DS_Store", "Thumbs.db",
                   "MANIFEST.sha256", "MANIFEST.json")


def hash_file(path, algo="sha256", chunk=1 << 20):
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def iter_files(root, exclude=DEFAULT_EXCLUDE):
    for dp, dns, fns in os.walk(root):
        dns.sort()
        for fn in sorted(fns):
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if any(fnmatch.fnmatch(rel, pat) for pat in exclude):
                continue
            yield rel, full


def build_manifest(root, exclude=DEFAULT_EXCLUDE, algo="sha256", previous=None):
    """Return {relpath: {"hash", "size", "mtime"}}. With `previous`, files whose size and mtime are
    unchanged reuse the stored hash (fast incremental updates of large datasets)."""
    out = {}
    for rel, full in iter_files(root, exclude):
        st = os.stat(full)
        prev = (previous or {}).get(rel)
        if prev and prev.get("size") == st.st_size and prev.get("mtime") == int(st.st_mtime):
            out[rel] = prev
            continue
        out[rel] = {"hash": hash_file(full, algo), "size": st.st_size, "mtime": int(st.st_mtime)}
    return out


def write_manifest(manifest, root, name="MANIFEST", algo="sha256"):
    txt = os.path.join(root, name + "." + algo)
    with open(txt, "w", encoding="utf-8", newline="\n") as fh:
        for rel in sorted(manifest):
            fh.write("%s  %s\n" % (manifest[rel]["hash"], rel))
    with open(os.path.join(root, name + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"algorithm": algo, "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": manifest}, fh, indent=1)
    return txt


def read_manifest(path):
    """Read a sha256sum-style file (or our JSON) into {relpath: hash}."""
    if path.endswith(".json"):
        with open(path, encoding="utf-8") as fh:
            return {k: v["hash"] for k, v in json.load(fh)["files"].items()}
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            h, _, rel = line.partition("  ")
            if not rel:
                h, _, rel = line.partition(" *")   # binary-mode marker
            out[rel.strip()] = h.strip().lower()
    return out


def verify(root, expected, exclude=DEFAULT_EXCLUDE, algo="sha256"):
    """Compare files under root with expected {relpath: hash}. Returns dict of lists: ok, changed, missing, new."""
    res = {"ok": [], "changed": [], "missing": [], "new": []}
    present = dict(iter_files(root, exclude))
    for rel, h in sorted(expected.items()):
        full = present.get(rel)
        if full is None:
            res["missing"].append(rel)
        elif hash_file(full, algo) == h:
            res["ok"].append(rel)
        else:
            res["changed"].append(rel)
    res["new"] = sorted(set(present) - set(expected))
    return res
