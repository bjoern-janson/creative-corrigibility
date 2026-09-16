from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


FREEZE_ID = "CC-V0-EPOCH-001"
APPARATUS_PARENT_COMMIT = "39e9919b23576bd0903960bb79aafdedc119eef5"
MANIFEST_PATH = Path("custody/FREEZE_V0.json")
PUBLIC_KEY_PATH = Path("custody/FREEZE_V0.pub.pem")
SIGNATURE_PATH = Path("custody/FREEZE_V0.sig.b64")

# This set is the judging apparatus plus the custody machinery that locks it.
# Prospective mechanism code must live outside this set.
FROZEN_PATHS = (
    ".github/workflows/ci.yml",
    "docs/preregistration/CREATIVE_CORRIGIBILITY_V0.md",
    "src/creative_corrigibility/__init__.py",
    "src/creative_corrigibility/model.py",
    "src/creative_corrigibility/engine.py",
    "src/creative_corrigibility/measurement.py",
    "src/creative_corrigibility/calibration.py",
    "src/creative_corrigibility/custody.py",
    "tests/test_architecture.py",
    "tests/test_calibration_signatures.py",
    "tests/test_exhaustive_finite_validation.py",
    "tests/test_measurement_contract.py",
    "tests/test_semantic_isolation.py",
    "tests/test_custody_freeze.py",
)


class FreezeVerificationError(RuntimeError):
    pass


@dataclass(frozen=True)
class FreezeReport:
    ok: bool
    status: str
    freeze_id: str
    parent_commit: str
    cube_coverage: str
    ci_tests: int
    correction_horizon: int


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_bytes(root: Path, relative_path: str, overrides: Mapping[str, bytes] | None) -> bytes:
    if overrides and relative_path in overrides:
        return overrides[relative_path]
    path = root / relative_path
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise FreezeVerificationError(f"frozen file missing: {relative_path}") from exc


def emit_frozen_hashes(root: Path) -> dict[str, str]:
    return {path: _sha256((root / path).read_bytes()) for path in FROZEN_PATHS}


def load_manifest(root: Path) -> dict:
    try:
        raw = (root / MANIFEST_PATH).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FreezeVerificationError(f"freeze manifest missing: {MANIFEST_PATH}") from exc
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FreezeVerificationError("freeze manifest is not valid JSON") from exc
    if not isinstance(manifest, dict):
        raise FreezeVerificationError("freeze manifest must be a JSON object")
    return manifest


def verify_manifest_signature(root: Path, manifest_bytes: bytes | None = None) -> bool:
    if manifest_bytes is None:
        try:
            manifest_bytes = (root / MANIFEST_PATH).read_bytes()
        except FileNotFoundError as exc:
            raise FreezeVerificationError(f"freeze manifest missing: {MANIFEST_PATH}") from exc

    try:
        signature_b64 = (root / SIGNATURE_PATH).read_text(encoding="ascii").strip()
        signature = base64.b64decode(signature_b64, validate=True)
        public_key = (root / PUBLIC_KEY_PATH).read_bytes()
    except FileNotFoundError as exc:
        raise FreezeVerificationError("freeze signature material is incomplete") from exc
    except (ValueError, UnicodeError) as exc:
        raise FreezeVerificationError("freeze signature is not valid base64") from exc

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest_file = tmp_path / "manifest.json"
        signature_file = tmp_path / "signature.der"
        public_key_file = tmp_path / "public.pem"
        manifest_file.write_bytes(manifest_bytes)
        signature_file.write_bytes(signature)
        public_key_file.write_bytes(public_key)
        result = subprocess.run(
            [
                "openssl",
                "dgst",
                "-sha256",
                "-verify",
                str(public_key_file),
                "-signature",
                str(signature_file),
                str(manifest_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        raise FreezeVerificationError("freeze manifest signature verification failed")
    return True


def verify_freeze(
    root: Path,
    content_overrides: Mapping[str, bytes] | None = None,
) -> FreezeReport:
    root = root.resolve()
    verify_manifest_signature(root)
    manifest = load_manifest(root)

    if manifest.get("schema") != "creative-corrigibility/freeze-manifest/v0":
        raise FreezeVerificationError("unexpected freeze manifest schema")
    if manifest.get("status") != "FROZEN_APPARATUS":
        raise FreezeVerificationError("manifest status is not FROZEN_APPARATUS")
    if manifest.get("freeze_id") != FREEZE_ID:
        raise FreezeVerificationError("freeze id mismatch")
    if manifest.get("apparatus_parent_commit") != APPARATUS_PARENT_COMMIT:
        raise FreezeVerificationError("calibrated apparatus parent mismatch")

    frozen_files = manifest.get("frozen_files")
    if not isinstance(frozen_files, dict):
        raise FreezeVerificationError("frozen_files must be an object")
    if tuple(sorted(frozen_files)) != tuple(sorted(FROZEN_PATHS)):
        raise FreezeVerificationError("frozen file set does not match the declared custody set")

    for relative_path in FROZEN_PATHS:
        expected = frozen_files.get(relative_path)
        if not isinstance(expected, str) or len(expected) != 64:
            raise FreezeVerificationError(f"invalid sha256 entry for {relative_path}")
        actual = _sha256(_repo_bytes(root, relative_path, content_overrides))
        if actual != expected:
            raise FreezeVerificationError(
                f"APPARATUS_INVALIDATED: sha256 mismatch for {relative_path}: {actual} != {expected}"
            )

    calibration = manifest.get("calibration_result", {})
    if calibration.get("status") != "PASS":
        raise FreezeVerificationError("calibration result is not PASS")
    if calibration.get("commit") != APPARATUS_PARENT_COMMIT:
        raise FreezeVerificationError("calibration commit mismatch")

    return FreezeReport(
        ok=True,
        status="FROZEN_APPARATUS",
        freeze_id=manifest["freeze_id"],
        parent_commit=manifest["apparatus_parent_commit"],
        cube_coverage=manifest["cube_coverage"],
        ci_tests=int(calibration["tests"]),
        correction_horizon=int(manifest["correction_horizon"]),
    )


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Creative Corrigibility v0 custody verifier")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--emit-hashes", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    root = _default_root()

    if args.emit_hashes:
        print(json.dumps(emit_frozen_hashes(root), sort_keys=True, indent=2))
        return 0

    try:
        report = verify_freeze(root)
    except FreezeVerificationError as exc:
        print(f"APPARATUS_INVALIDATED: {exc}")
        return 1
    print(
        json.dumps(
            {
                "status": report.status,
                "freeze_id": report.freeze_id,
                "apparatus_parent_commit": report.parent_commit,
                "cube_coverage": report.cube_coverage,
                "calibration_tests": report.ci_tests,
                "correction_horizon": report.correction_horizon,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
