"""Command-line interface for data-checksum."""
import argparse
import json
import os
import sys

from .core import DEFAULT_EXCLUDE, build_manifest, read_manifest, verify, write_manifest


def main(argv=None):
    ap = argparse.ArgumentParser(prog="data-checksum", description="Create and verify dataset checksum manifests.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="write MANIFEST.sha256 and MANIFEST.json in the dataset folder")
    c.add_argument("root")
    c.add_argument("--exclude", action="append", default=[], help="extra glob patterns to skip")
    c.add_argument("--update", action="store_true", help="reuse hashes of unchanged files from MANIFEST.json")
    v = sub.add_parser("verify", help="check files against a manifest")
    v.add_argument("root")
    v.add_argument("-m", "--manifest", help="manifest file (default: <root>/MANIFEST.sha256)")
    v.add_argument("--exclude", action="append", default=[])
    v.add_argument("--ignore-new", action="store_true")
    args = ap.parse_args(argv)
    exclude = DEFAULT_EXCLUDE + tuple(args.exclude)
    if args.cmd == "create":
        prev = None
        side = os.path.join(args.root, "MANIFEST.json")
        if args.update and os.path.exists(side):
            with open(side, encoding="utf-8") as fh:
                prev = json.load(fh)["files"]
        m = build_manifest(args.root, exclude, previous=prev)
        path = write_manifest(m, args.root)
        total = sum(x["size"] for x in m.values())
        print("%d files (%.1f MB) -> %s" % (len(m), total / 1e6, path))
        return 0
    mpath = args.manifest or os.path.join(args.root, "MANIFEST.sha256")
    res = verify(args.root, read_manifest(mpath), exclude)
    for key in ("changed", "missing") + (() if args.ignore_new else ("new",)):
        for rel in res[key]:
            print("%-8s %s" % (key.upper(), rel))
    print("%d ok, %d changed, %d missing, %d new" % (len(res["ok"]), len(res["changed"]), len(res["missing"]),
                                                   len(res["new"])), file=sys.stderr)
    bad = res["changed"] or res["missing"] or (res["new"] and not args.ignore_new)
    return 1 if bad else 0
