"""Shared atomic-write helpers.

Addresses Gap 29 (fixed ``.tmp`` names can collide under concurrent execution)
and Gap 30 (atomic replace is not the same as crash durability).

Every writer routes through a unique, same-directory temporary file created with
``tempfile.mkstemp`` (PID + random suffix), is flushed and ``fsync``-ed, and then
``os.replace``-d into place. ``os.replace`` is atomic on POSIX when source and
destination are on the same filesystem, so a reader never observes a partial file.

Durability caveat (documented, not over-promised): fsync of the file guarantees
the file's bytes reach disk before the rename returns; we additionally fsync the
containing directory so the rename itself is durable. This protects against
process crash and, on most filesystems, node crash -- but exact GPFS durability
semantics are storage-configuration dependent and are not claimed beyond this.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _fsync_dir(dir_path: Path) -> None:
    """Best-effort fsync of a directory so a rename within it is durable."""
    try:
        fd = os.open(str(dir_path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_bytes(path: str | os.PathLike, data: bytes, *, fsync: bool = True) -> None:
    """Atomically write ``data`` to ``path`` via a unique same-directory temp file."""
    path = Path(path)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(directory), prefix=path.name + ".", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            if fsync:
                os.fsync(f.fileno())
        os.replace(tmp_path, path)
        if fsync:
            _fsync_dir(directory)
    except BaseException:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def atomic_write_text(path: str | os.PathLike, text: str, *, encoding: str = "utf-8",
                      fsync: bool = True) -> None:
    atomic_write_bytes(path, text.encode(encoding), fsync=fsync)


def atomic_write_json(path: str | os.PathLike, obj: Any, *, indent: int | None = None,
                      fsync: bool = True) -> None:
    atomic_write_text(path, json.dumps(obj, indent=indent), fsync=fsync)


def atomic_write_dataframe_csv(path: str | os.PathLike, df, *, fsync: bool = True, **to_csv_kwargs) -> None:
    """Atomically write a pandas DataFrame to CSV. ``index=False`` unless overridden."""
    to_csv_kwargs.setdefault("index", False)
    csv_text = df.to_csv(**to_csv_kwargs)
    atomic_write_text(path, csv_text, fsync=fsync)
