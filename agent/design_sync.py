"""Design sync — VPS-based versioned storage for FreeCAD → Blender workflow.

Handles:
- Rsync push/pull to VPS
- Versioned file naming: REGION_PART_SIDE_STATUS_vNNN_YYYYMMDD.stl
- Manifest tracking (manifest.json) with full audit trail
- Archive rotation for old drafts (gzip compression)
- 5GB storage limit enforcement
"""
import datetime
import gzip
import json
import shutil
import subprocess
from pathlib import Path

from agent.config import load_config

# Remote VPS paths — configure these for your server
# See docs/DESIGN_SYNC_GUIDE.md for setup instructions
VPS_HOST = "user@your-vps-ip"
VPS_BASE = "/home/user/3dprintvoice-designs"
VPS_ACTIVE = f"{VPS_BASE}/active"
VPS_ARCHIVE = f"{VPS_BASE}/archive"
VPS_MANIFEST = f"{VPS_BASE}/manifest.json"

# Local cache
LOCAL_SYNC_DIR = Path.home() / "3dprintvoice-designs"
LOCAL_ACTIVE = LOCAL_SYNC_DIR / "active"
LOCAL_ARCHIVE = LOCAL_SYNC_DIR / "archive"
LOCAL_MANIFEST = LOCAL_SYNC_DIR / "manifest.json"

SIZE_LIMIT_MB = 5120  # 5GB
SIZE_WARN_MB = 4096   # 4GB warning

VALID_STATUSES = {"DRAFT", "REVIEW", "FINAL", "PRINTED"}
VALID_REGIONS = {"HEAD", "TORSO", "ARM", "LEG", "HAND", "FOOT", "JOINT",
                 "PANEL", "ACCESSORY", "FRAME", "CONNECTOR"}


def _run_ssh(cmd: str, timeout: int = 30) -> tuple[bool, str]:
    """Run a command on VPS via SSH."""
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", VPS_HOST, cmd],
            capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def _rsync_pull() -> tuple[bool, str]:
    """Pull active designs from VPS to local cache."""
    LOCAL_ACTIVE.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            ["rsync", "-az", "--delete",
             f"{VPS_HOST}:{VPS_ACTIVE}/", str(LOCAL_ACTIVE) + "/"],
            capture_output=True, text=True, timeout=120)
        # Pull manifest and merge with local (preserve any local-only entries)
        vps_manifest_tmp = LOCAL_SYNC_DIR / "manifest_vps.json"
        subprocess.run(
            ["rsync", "-az",
             f"{VPS_HOST}:{VPS_MANIFEST}", str(vps_manifest_tmp)],
            capture_output=True, text=True, timeout=30)
        # Merge: VPS is primary, but keep any local entries missing from VPS
        if vps_manifest_tmp.exists():
            try:
                local_m = load_manifest()
                with open(vps_manifest_tmp) as f:
                    vps_m = json.load(f)
                merged = {**local_m, **vps_m}
                # Merge parts: keep the one with more versions
                merged["parts"] = {}
                all_keys = set(local_m.get("parts", {}).keys()) | set(vps_m.get("parts", {}).keys())
                for k in all_keys:
                    local_part = local_m.get("parts", {}).get(k, {"versions": []})
                    vps_part = vps_m.get("parts", {}).get(k, {"versions": []})
                    if len(local_part.get("versions", [])) >= len(vps_part.get("versions", [])):
                        merged["parts"][k] = local_part
                    else:
                        merged["parts"][k] = vps_part
                with open(LOCAL_MANIFEST, "w") as f:
                    json.dump(merged, f, indent=2)
                vps_manifest_tmp.unlink()
            except Exception:
                # Fallback: just use VPS version
                if vps_manifest_tmp.exists():
                    import shutil as _sh
                    _sh.move(str(vps_manifest_tmp), str(LOCAL_MANIFEST))
        return result.returncode == 0, result.stderr.strip() or "OK"
    except Exception as e:
        return False, str(e)


def _rsync_push_file(local_path: Path) -> tuple[bool, str]:
    """Push a single file to VPS active directory."""
    try:
        result = subprocess.run(
            ["rsync", "-az", str(local_path),
             f"{VPS_HOST}:{VPS_ACTIVE}/"],
            capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stderr.strip() or "OK"
    except Exception as e:
        return False, str(e)


def _push_manifest() -> tuple[bool, str]:
    """Push manifest.json to VPS."""
    try:
        result = subprocess.run(
            ["rsync", "-az", str(LOCAL_MANIFEST),
             f"{VPS_HOST}:{VPS_MANIFEST}"],
            capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stderr.strip() or "OK"
    except Exception as e:
        return False, str(e)


def _get_vps_size_mb() -> float:
    """Get total size of designs folder on VPS in MB."""
    ok, output = _run_ssh(f"du -sm {VPS_BASE} 2>/dev/null | cut -f1")
    if ok and output.isdigit():
        return float(output)
    return 0.0


def load_manifest() -> dict:
    """Load manifest from local cache."""
    if LOCAL_MANIFEST.exists():
        try:
            with open(LOCAL_MANIFEST) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "project": "articulated-figure-01",
        "author": "Roland Preisach",
        "created": datetime.datetime.now().isoformat(),
        "parts": {},
    }


def save_manifest(manifest: dict) -> None:
    """Save manifest locally and push to VPS."""
    LOCAL_SYNC_DIR.mkdir(parents=True, exist_ok=True)
    manifest["last_updated"] = datetime.datetime.now().isoformat()
    with open(LOCAL_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    _push_manifest()


def _part_key(region: str, part: str, side: str) -> str:
    """Generate consistent part key."""
    return f"{region}_{part}_{side}".upper()


def _version_filename(region: str, part: str, side: str,
                      status: str, version: int) -> str:
    """Generate versioned filename."""
    date = datetime.date.today().strftime("%Y%m%d")
    return f"{region}_{part}_{side}_{status}_v{version:03d}_{date}.stl".upper()


def get_next_version(manifest: dict, part_key: str) -> int:
    """Get next version number for a part."""
    if part_key in manifest["parts"]:
        versions = manifest["parts"][part_key].get("versions", [])
        if versions:
            return max(v["version"] for v in versions) + 1
    return 1


def register_version(manifest: dict, part_key: str, version: int,
                     status: str, source: str, filename: str,
                     notes: str = "") -> dict:
    """Add a version entry to the manifest."""
    if part_key not in manifest["parts"]:
        manifest["parts"][part_key] = {"versions": [], "current_version": 0,
                                        "current_status": "DRAFT"}
    entry = {
        "version": version,
        "status": status,
        "date": datetime.datetime.now().isoformat(),
        "source": source,
        "file": filename,
        "notes": notes,
    }
    manifest["parts"][part_key]["versions"].append(entry)
    manifest["parts"][part_key]["current_version"] = version
    manifest["parts"][part_key]["current_status"] = status
    return manifest


def save_iteration(stl_path: Path, region: str, part: str, side: str,
                   status: str = "DRAFT", source: str = "blender",
                   notes: str = "") -> tuple[bool, str]:
    """Save a design iteration: version, rename, push to VPS, update manifest."""
    if status not in VALID_STATUSES:
        return False, f"Invalid status: {status}. Use: {VALID_STATUSES}"

    # Check VPS size
    size = _get_vps_size_mb()
    if size > SIZE_LIMIT_MB:
        return False, f"VPS storage full ({size:.0f}MB / {SIZE_LIMIT_MB}MB). Archive old drafts first."

    manifest = load_manifest()
    key = _part_key(region, part, side)
    version = get_next_version(manifest, key)
    filename = _version_filename(region, part, side, status, version)

    # Copy to local active with versioned name
    LOCAL_ACTIVE.mkdir(parents=True, exist_ok=True)
    dest = LOCAL_ACTIVE / filename
    shutil.copy2(str(stl_path), str(dest))

    # Push to VPS
    ok, msg = _rsync_push_file(dest)
    if not ok:
        return False, f"Push failed: {msg}"

    # Update manifest
    manifest = register_version(manifest, key, version, status, source,
                                filename, notes)
    save_manifest(manifest)

    warning = ""
    if size > SIZE_WARN_MB:
        warning = f" (storage: {size:.0f}MB / {SIZE_LIMIT_MB}MB — consider archiving)"

    return True, f"{filename} v{version:03d} pushed to VPS{warning}"


def mark_final(region: str, part: str, side: str,
               notes: str = "Approved for printing") -> tuple[bool, str]:
    """Mark current version of a part as FINAL."""
    manifest = load_manifest()
    key = _part_key(region, part, side)
    if key not in manifest["parts"]:
        return False, f"Part {key} not found in manifest"

    current = manifest["parts"][key]
    old_version = current["current_version"]
    old_file = current["versions"][-1]["file"] if current["versions"] else None

    if not old_file:
        return False, f"No versions found for {key}"

    # Create FINAL version (rename copy)
    new_version = old_version + 1
    new_filename = _version_filename(region, part, side, "FINAL", new_version)

    src = LOCAL_ACTIVE / old_file
    if not src.exists():
        # Try pulling latest first
        _rsync_pull()
        src = LOCAL_ACTIVE / old_file
        if not src.exists():
            return False, f"Source file {old_file} not found"

    dest = LOCAL_ACTIVE / new_filename
    shutil.copy2(str(src), str(dest))

    ok, msg = _rsync_push_file(dest)
    if not ok:
        return False, f"Push failed: {msg}"

    manifest = register_version(manifest, key, new_version, "FINAL",
                                "blender", new_filename, notes)
    save_manifest(manifest)
    return True, f"{key} marked FINAL as {new_filename}"


def reopen_for_changes(region: str, part: str, side: str,
                       notes: str = "Reopened for iteration") -> tuple[bool, str]:
    """Reopen a FINAL part back to DRAFT with a new version."""
    manifest = load_manifest()
    key = _part_key(region, part, side)
    if key not in manifest["parts"]:
        return False, f"Part {key} not found"

    current = manifest["parts"][key]
    old_file = current["versions"][-1]["file"] if current["versions"] else None
    if not old_file:
        return False, f"No versions for {key}"

    new_version = get_next_version(manifest, key)
    new_filename = _version_filename(region, part, side, "DRAFT", new_version)

    src = LOCAL_ACTIVE / old_file
    if not src.exists():
        _rsync_pull()
        src = LOCAL_ACTIVE / old_file
    if not src.exists():
        return False, f"Source file {old_file} not found"

    dest = LOCAL_ACTIVE / new_filename
    shutil.copy2(str(src), str(dest))
    ok, msg = _rsync_push_file(dest)
    if not ok:
        return False, f"Push failed: {msg}"

    manifest = register_version(manifest, key, new_version, "DRAFT",
                                "blender", new_filename, notes)
    save_manifest(manifest)
    return True, f"{key} reopened as DRAFT {new_filename}"


def archive_old_drafts() -> tuple[bool, str]:
    """Compress old DRAFT versions (keep only latest DRAFT + all FINAL)."""
    manifest = load_manifest()
    archived = 0
    for key, part_data in manifest["parts"].items():
        versions = part_data.get("versions", [])
        # Find all drafts except the latest
        drafts = [v for v in versions if v["status"] == "DRAFT"]
        if len(drafts) <= 1:
            continue
        for draft in drafts[:-1]:  # keep latest draft
            src = LOCAL_ACTIVE / draft["file"]
            if src.exists():
                LOCAL_ARCHIVE.mkdir(parents=True, exist_ok=True)
                gz_path = LOCAL_ARCHIVE / (draft["file"] + ".gz")
                with open(src, "rb") as f_in:
                    with gzip.open(str(gz_path), "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                src.unlink()
                archived += 1

    if archived > 0:
        # Save updated manifest (files now moved to archive)
        save_manifest(manifest)
        # Push changes to VPS
        subprocess.run(
            ["rsync", "-az", "--delete",
             str(LOCAL_ACTIVE) + "/", f"{VPS_HOST}:{VPS_ACTIVE}/"],
            capture_output=True, timeout=120)
        subprocess.run(
            ["rsync", "-az",
             str(LOCAL_ARCHIVE) + "/", f"{VPS_HOST}:{VPS_ARCHIVE}/"],
            capture_output=True, timeout=120)
    return True, f"Archived {archived} old draft versions"


def pull_designs() -> tuple[bool, str]:
    """Pull all active designs from VPS to local cache."""
    ok, msg = _rsync_pull()
    if ok:
        files = list(LOCAL_ACTIVE.glob("*.stl")) if LOCAL_ACTIVE.exists() else []
        return True, f"Pulled {len(files)} design files from VPS"
    return False, f"Pull failed: {msg}"


def list_parts() -> dict:
    """List all parts from manifest with current status."""
    manifest = load_manifest()
    return manifest.get("parts", {})


def get_latest_file(region: str, part: str, side: str) -> Path | None:
    """Get the latest version file path for a part."""
    manifest = load_manifest()
    key = _part_key(region, part, side)
    if key not in manifest["parts"]:
        return None
    versions = manifest["parts"][key].get("versions", [])
    if not versions:
        return None
    latest = versions[-1]
    path = LOCAL_ACTIVE / latest["file"]
    return path if path.exists() else None


def init_vps_structure() -> tuple[bool, str]:
    """Initialize the designs folder structure on VPS."""
    cmds = [
        f"mkdir -p {VPS_ACTIVE}",
        f"mkdir -p {VPS_ARCHIVE}",
        f"test -f {VPS_MANIFEST} || echo '{{}}' > {VPS_MANIFEST}",
    ]
    for cmd in cmds:
        ok, msg = _run_ssh(cmd)
        if not ok:
            return False, f"VPS init failed: {msg}"
    return True, "VPS structure initialized"
