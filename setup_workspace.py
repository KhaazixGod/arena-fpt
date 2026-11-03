"""Put the arena's sibling folders in place on a new machine (Windows or Linux), or refresh the copies kept in this repo.

The arena code looks for CL-0 and the G0 tools NEXT TO this folder (../cl0, ../dir1), and the plans at ../KE_HOACH_*.md.  Git holds them in deps/:
    python setup_workspace.py              # new machine: deps/cl0 -> ../cl0, deps/dir1 -> ../dir1, deps/KE_HOACH_*.md -> ../  (never overwrites)
    python setup_workspace.py --collect    # machine with the originals: ../cl0, ../dir1, ../KE_HOACH_*.md -> deps/ (run before each commit)
Both print the CL-0 freeze hash of each side (cl0.system.code_sha256 algorithm), which must match.
"""
import argparse
import filecmp
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
DEPS = os.path.join(HERE, "deps")
DIRS = ("cl0", "dir1")
SKIP = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc")


def cl0_hash(cl0_root: str) -> str:
    """Same as cl0.system.code_sha256() for the package at <cl0_root>/cl0, without importing it.  Paths use the OS separator, as the original does."""
    root = os.path.join(cl0_root, "cl0")
    h = hashlib.sha256()
    for dp, dn, fn in sorted(os.walk(root)):
        dn[:] = sorted(d for d in dn if d not in ("__pycache__", "sim", "tests"))
        for f in sorted(fn):
            if f.endswith(".py"):
                with open(os.path.join(dp, f), "rb") as fh:
                    h.update(os.path.relpath(os.path.join(dp, f), root).encode() + b"\0" + fh.read() + b"\0")
    return h.hexdigest()


def plans(folder: str):
    return sorted(f for f in os.listdir(folder) if f.startswith("KE_HOACH_") and f.endswith(".md")) if os.path.isdir(folder) else []


def collect() -> None:
    os.makedirs(DEPS, exist_ok=True)
    for d in DIRS:
        src, dst = os.path.join(PARENT, d), os.path.join(DEPS, d)
        if not os.path.isdir(src):
            sys.exit(f"missing {src}")
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=SKIP)
        print(f"copied {src} -> {dst}")
    for f in plans(PARENT):
        shutil.copy2(os.path.join(PARENT, f), os.path.join(DEPS, f))
        print(f"copied {f} -> deps/")


def install() -> None:
    for d in DIRS:
        src, dst = os.path.join(DEPS, d), os.path.join(PARENT, d)
        if os.path.exists(dst):
            print(f"kept existing {dst} (not overwritten)")
            continue
        shutil.copytree(src, dst, ignore=SKIP)
        print(f"copied {src} -> {dst}")
    for f in plans(DEPS):
        dst = os.path.join(PARENT, f)
        if os.path.exists(dst) and not filecmp.cmp(dst, os.path.join(DEPS, f), shallow=False):
            print(f"kept existing {dst} (differs from deps/{f})")
        elif not os.path.exists(dst):
            shutil.copy2(os.path.join(DEPS, f), dst)
            print(f"copied deps/{f} -> {dst}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--collect", action="store_true", help="copy the originals next to this folder INTO deps/")
    a = ap.parse_args()
    collect() if a.collect else install()
    for name, root in (("deps/cl0", os.path.join(DEPS, "cl0")), ("../cl0", os.path.join(PARENT, "cl0"))):
        if os.path.isdir(os.path.join(root, "cl0")):
            print(f"CL-0 code sha256 {name}: {cl0_hash(root)}")


if __name__ == "__main__":
    main()
