# data-checksum

**Prove your data have not changed: create SHA-256 manifests for dataset folders and verify
them later, on another machine, or after a transfer, in the standard `sha256sum` format.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Raw data should be immutable, but files get overwritten by accident, corrupted during copies to
external drives or clusters, or silently "cleaned" by a collaborator. A checksum manifest stored with
the data (and in your repository or data paper) lets anyone confirm they analyse exactly the
published files. Data repositories and archives use the same approach (BagIt, Zenodo MD5s).

## Features

- `MANIFEST.sha256` compatible with `sha256sum -c`, plus `MANIFEST.json` with sizes and timestamps
- Excludes VCS folders, caches and OS clutter by default; extra `--exclude` globs
- `--update`: incremental re-hashing of only changed files (by size and mtime) for large datasets
- `verify` reports changed, missing and new files with exit code 1 (CI/pipeline guard)
- Reads standard `sha256sum` manifests produced by other tools

## Usage

```bash
pip install .
data-checksum create data/raw
data-checksum verify data/raw
data-checksum verify /mnt/cluster/project/raw -m data/raw/MANIFEST.sha256 --ignore-new
sha256sum -c MANIFEST.sha256   # works too (run inside the folder)
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
