"""Build helpers for libxmtp native library."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.install import install
from wheel.bdist_wheel import bdist_wheel


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


def _project_root() -> Path:
    # bindings/python (or sdist root when building from source distribution)
    return Path(__file__).resolve().parents[2]


def _repo_root(project_root: Path) -> Path:
    candidate = project_root.parent.parent
    if (candidate / "bindings" / "python").exists():
        return candidate
    return project_root


def _lib_name_candidates() -> list[str]:
    if sys.platform == "darwin":
        return ["libxmtpv3.dylib"]
    if sys.platform == "win32":
        return ["xmtpv3.dll", "libxmtpv3.dll"]
    return ["libxmtpv3.so"]


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.check_call(cmd, cwd=str(cwd))


def _ensure_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f'Missing required tool "{name}". Install it and retry.')


def _clone_libxmtp(
    repo_url: str,
    dest: Path,
    ref: str | None,
    announce: Callable[[str], None],
) -> None:
    _ensure_tool("git")
    if ref:
        try:
            _run(
                ["git", "clone", "--depth", "1", "--branch", ref, repo_url, str(dest)],
                cwd=dest.parent,
            )
            return
        except subprocess.CalledProcessError:
            announce(f'Failed to clone with ref "{ref}", retrying with default branch.')
    _run(["git", "clone", "--depth", "1", repo_url, str(dest)], cwd=dest.parent)
    if ref:
        _run(["git", "-C", str(dest), "fetch", "--depth", "1", "origin", ref], cwd=dest.parent)
        _run(["git", "-C", str(dest), "checkout", ref], cwd=dest.parent)


def _select_built_library(target_dir: Path) -> Path:
    for name in _lib_name_candidates():
        candidate = target_dir / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"libxmtp build output not found in {target_dir}")


def _ensure_libxmtp(announce: Callable[[str], None]) -> None:
    if _is_truthy(os.getenv("XMTP_BINDINGS_SKIP_BUILD")):
        announce("Skipping libxmtp build (XMTP_BINDINGS_SKIP_BUILD set).")
        return

    project_root = _project_root()
    repo_root = _repo_root(project_root)
    package_dir = project_root / "src" / "xmtp_bindings"

    if not package_dir.exists():
        raise RuntimeError(f"Package dir not found: {package_dir}")

    if not _is_truthy(os.getenv("XMTP_BINDINGS_FORCE_BUILD")):
        for name in _lib_name_candidates():
            if (package_dir / name).exists():
                announce("libxmtp native library already present; skipping build.")
                return

    libxmtp_path = os.getenv("XMTP_LIBXMTP_PATH")
    deps_dir = repo_root / ".deps"
    libxmtp_dir = (
        Path(libxmtp_path).expanduser().resolve() if libxmtp_path else deps_dir / "libxmtp"
    )

    deps_dir.mkdir(parents=True, exist_ok=True)

    repo_url = os.getenv("XMTP_LIBXMTP_REPO", "https://github.com/xmtp/libxmtp")
    ref = os.getenv("XMTP_LIBXMTP_REF")

    if not libxmtp_dir.exists():
        announce(f"Cloning libxmtp from {repo_url} into {libxmtp_dir}")
        _clone_libxmtp(repo_url, libxmtp_dir, ref, announce)
    elif ref:
        _ensure_tool("git")
        announce(f"Checking out libxmtp ref {ref}")
        _run(
            ["git", "-C", str(libxmtp_dir), "fetch", "--depth", "1", "origin", ref],
            cwd=libxmtp_dir,
        )
        _run(["git", "-C", str(libxmtp_dir), "checkout", ref], cwd=libxmtp_dir)

    _ensure_tool("cargo")
    announce("Building libxmtp (xmtpv3) via cargo...")
    _run(["cargo", "build", "-p", "xmtpv3", "--release"], cwd=libxmtp_dir)

    built = _select_built_library(libxmtp_dir / "target" / "release")
    destination = package_dir / built.name
    shutil.copy2(built, destination)
    announce(f"Copied {built.name} to {destination}")


class BuildPy(build_py):
    """Ensure libxmtp is built before packaging."""

    def run(self) -> None:
        _ensure_libxmtp(self._announce)
        super().run()

    def _announce(self, message: str) -> None:
        self.announce(message, level=2)


class BuildExt(build_ext):
    """Ensure libxmtp is built before extensions (even if none exist)."""

    def run(self) -> None:
        _ensure_libxmtp(self._announce)
        super().run()

    def _announce(self, message: str) -> None:
        self.announce(message, level=2)


class Develop(develop):
    """Ensure libxmtp is built for editable installs."""

    def run(self) -> None:
        _ensure_libxmtp(self._announce)
        super().run()

    def _announce(self, message: str) -> None:
        self.announce(message, level=2)


class Install(install):
    """Install pure-Python packages into platlib for bundled shared libraries."""

    def finalize_options(self) -> None:
        super().finalize_options()
        self.install_lib = self.install_platlib


class BdistWheel(bdist_wheel):
    """Mark the wheel as platform-specific when bundling native libraries."""

    def finalize_options(self) -> None:
        super().finalize_options()
        self.root_is_pure = False

    def run(self) -> None:
        self.root_is_pure = False
        super().run()

    def write_wheelfile(self, *args: object, **kwargs: object) -> None:
        self.root_is_pure = False
        super().write_wheelfile(*args, **kwargs)
