"""
E2E Distribution Rehearsal -- Step 5 Launch Hardening
Validates distribution readiness: build artifacts, license enforcement,
network binding, backup endpoints, and public portal.

Usage: python -m tools.admin_scripts.e2e_distribution_rehearsal [--base-url URL]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import requests

_BASE_URL = "http://localhost:8001"
PASS = 0
FAIL = 0
WARN = 0

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _set_base_url(url: str):
    global _BASE_URL
    _BASE_URL = url


def _log(ok: bool, label: str, detail: str = ""):
    global PASS, FAIL
    tag = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    suffix = f" -- {detail}" if detail else ""
    print(f"  [{tag}] {label}{suffix}")


def _warn(label: str, detail: str = ""):
    global WARN
    WARN += 1
    suffix = f" -- {detail}" if detail else ""
    print(f"  [WARN] {label}{suffix}")


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# == Phase 1: Build Artifacts ================================================

def phase_1_artifacts():
    print("\n=== Phase 1: Build Artifacts ===")

    # 1. PyInstaller backend exe
    exe_path = PROJECT_ROOT / "dist" / "fitmanager" / "fitmanager.exe"
    _log(exe_path.exists(), "Backend exe exists", f"path={exe_path}")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        _log(size_mb > 5, "Backend exe size reasonable", f"{size_mb:.1f} MB")
        # Total bundle (exe + _internal)
        bundle_dir = PROJECT_ROOT / "dist" / "fitmanager"
        total_mb = sum(f.stat().st_size for f in bundle_dir.rglob("*") if f.is_file()) / (1024 * 1024)
        _log(total_mb > 50, "Backend bundle total size", f"{total_mb:.0f} MB")

    # 2. PyInstaller internal data
    internal = PROJECT_ROOT / "dist" / "fitmanager" / "_internal"
    _log(internal.exists(), "PyInstaller _internal dir exists")
    if internal.exists():
        seed_json = internal / "data" / "exercises" / "seed_exercises.json"
        _log(seed_json.exists(), "Seed exercises JSON in bundle", f"path={seed_json}")
        alembic_dir = internal / "alembic"
        _log(alembic_dir.exists(), "Alembic migrations in bundle")

    # 3. Installer
    installer = PROJECT_ROOT / "dist" / "FitManager_Setup.exe"
    _log(installer.exists(), "Inno Setup installer exists")
    if installer.exists():
        size_mb = installer.stat().st_size / (1024 * 1024)
        _log(size_mb > 40, "Installer size reasonable", f"{size_mb:.1f} MB")

    # 4. Launcher
    launcher = PROJECT_ROOT / "installer" / "launcher.bat"
    _log(launcher.exists(), "Launcher batch script exists")
    if launcher.exists():
        content = launcher.read_text(encoding="utf-8")
        _log("LICENSE_ENFORCEMENT_ENABLED=true" in content,
             "Launcher sets LICENSE_ENFORCEMENT_ENABLED=true")
        _log("--host" not in content or "0.0.0.0" in content,
             "Launcher binds to 0.0.0.0 or uses default")

    # 5. Inno Setup script
    iss = PROJECT_ROOT / "installer" / "fitmanager.iss"
    _log(iss.exists(), "Inno Setup script exists")

    # 6. Node runtime
    node_dir = PROJECT_ROOT / "installer" / "node"
    node_exe = node_dir / "node.exe" if node_dir.exists() else None
    if node_exe and node_exe.exists():
        _log(True, "Node.exe runtime present")
    else:
        _warn("Node.exe runtime missing (expected in installer/node/)")

    # 7. Frontend standalone
    standalone_server = PROJECT_ROOT / "frontend" / ".next" / "standalone" / "server.js"
    if standalone_server.exists():
        _log(True, "Next.js standalone server.js present")
    else:
        _warn("Next.js standalone not built (frontend/.next/standalone/server.js)")

    # 8. Entry point
    entry = PROJECT_ROOT / "tools" / "build" / "entry_point.py"
    _log(entry.exists(), "PyInstaller entry_point.py exists")

    # 9. fitmanager.spec
    spec = PROJECT_ROOT / "tools" / "build" / "fitmanager.spec"
    _log(spec.exists(), "PyInstaller spec file exists")


# == Phase 2: License System =================================================

def phase_2_license():
    print("\n=== Phase 2: License System ===")

    # 1. License file exists
    license_key = PROJECT_ROOT / "data" / "license.key"
    _log(license_key.exists(), "License key file exists", f"path={license_key}")

    # 2. Public key exists
    pub_key = PROJECT_ROOT / "data" / "license_public.pem"
    _log(pub_key.exists(), "License public key exists", f"path={pub_key}")

    # 3. Verify license via CLI
    try:
        result = subprocess.run(
            [sys.executable, "-m", "tools.admin_scripts.generate_license",
             "verify", str(license_key)],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        _log(result.returncode == 0, "License CLI verify passes",
             f"rc={result.returncode}")
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                print(f"    {line}")
    except Exception as e:
        _log(False, "License CLI verify", f"error={e}")

    # 4. Health endpoint reports license status
    try:
        r = requests.get(f"{_BASE_URL}/health", timeout=5)
        health = r.json()
        status = health.get("license_status", "unknown")
        _log(status == "valid", "Health reports license valid", f"license_status={status}")
    except Exception as e:
        _log(False, "Health endpoint", f"error={e}")

    # 5. License service check (direct import)
    try:
        from api.services.license import check_license
        check = check_license()
        _log(check.is_valid, "License service check_license()",
             f"status={check.status}, expires={check.expires_at}")
        if check.claims:
            _log(len(check.claims.client_id) > 0, "License has client_id",
                 f"client={check.claims.client_id}")
            _log(check.claims.tier in ("basic", "pro", "enterprise"),
                 "License tier valid", f"tier={check.claims.tier}")
    except Exception as e:
        _log(False, "License service import", f"error={e}")


# == Phase 3: License Enforcement =============================================

def phase_3_enforcement():
    print("\n=== Phase 3: License Enforcement (middleware gate) ===")

    # Check if LICENSE_ENFORCEMENT_ENABLED is set on running server
    # We test by checking /health (always allowed) vs protected endpoints without auth
    try:
        r = requests.get(f"{_BASE_URL}/health", timeout=5)
        _log(r.status_code == 200, "Health endpoint accessible (exempt from license)")
    except Exception as e:
        _log(False, "Health endpoint", f"error={e}")
        return

    # Launcher.bat sets LICENSE_ENFORCEMENT_ENABLED=true -- verify it's in the script
    launcher = PROJECT_ROOT / "installer" / "launcher.bat"
    if launcher.exists():
        content = launcher.read_text(encoding="utf-8")
        _log("LICENSE_ENFORCEMENT_ENABLED=true" in content,
             "Launcher enforces license in production")
    else:
        _log(False, "Launcher not found for enforcement check")

    # Verify the env file has essential config
    env_file = PROJECT_ROOT / "data" / ".env"
    if env_file.exists():
        env_content = env_file.read_text(encoding="utf-8")
        _log("JWT_SECRET=" in env_content, ".env has JWT_SECRET configured")
        _log("PUBLIC_PORTAL_ENABLED=" in env_content, ".env has PUBLIC_PORTAL_ENABLED")
        _log("PUBLIC_BASE_URL=" in env_content, ".env has PUBLIC_BASE_URL")
    else:
        _log(False, ".env file exists")


# == Phase 4: Network Binding ================================================

def phase_4_network():
    print("\n=== Phase 4: Network Binding ===")

    # 1. Backend responds on configured URL
    try:
        r = requests.get(f"{_BASE_URL}/health", timeout=5)
        _log(r.status_code == 200, "Backend responds on configured URL",
             f"url={_BASE_URL}")
    except Exception as e:
        _log(False, "Backend reachable", f"error={e}")
        return

    # 2. Check CORS headers
    try:
        r = requests.options(f"{_BASE_URL}/api/clients",
                             headers={"Origin": "http://localhost:3001",
                                      "Access-Control-Request-Method": "GET"},
                             timeout=5)
        cors_ok = "access-control-allow-origin" in r.headers
        _log(cors_ok, "CORS headers present for localhost",
             f"headers={dict(r.headers)}" if not cors_ok else "")
    except Exception as e:
        _warn("CORS check", f"error={e}")

    # 3. API docs accessible (dev only)
    try:
        r = requests.get(f"{_BASE_URL}/docs", timeout=5)
        _log(r.status_code == 200, "API docs (/docs) accessible")
    except Exception:
        _warn("API docs not accessible")

    # 4. Static media serving
    try:
        r = requests.get(f"{_BASE_URL}/media/exercises/", timeout=5)
        # 404 or 200 both OK -- just not connection error
        _log(r.status_code in (200, 404, 403, 405),
             "Static media endpoint reachable", f"status={r.status_code}")
    except Exception as e:
        _log(False, "Static media serving", f"error={e}")


# == Phase 5: Backup Endpoints ===============================================

def phase_5_backup(token: str):
    print("\n=== Phase 5: Backup Endpoints ===")
    h = _auth_headers(token)

    # 1. Create backup
    r = requests.post(f"{_BASE_URL}/api/backup/create", headers=h, timeout=30)
    _log(r.status_code == 200, "Create backup", f"status={r.status_code}")
    if r.status_code != 200:
        return
    filename = r.json().get("filename", "")
    _log(len(filename) > 0, "Backup filename returned", f"file={filename}")

    # 2. List backups
    r = requests.get(f"{_BASE_URL}/api/backup/list", headers=h, timeout=10)
    _log(r.status_code == 200, "List backups", f"status={r.status_code}")

    # 3. Verify
    r = requests.post(f"{_BASE_URL}/api/backup/verify/{filename}", headers=h, timeout=10)
    _log(r.status_code == 200, "Verify backup", f"status={r.status_code}")
    if r.status_code == 200:
        v = r.json()
        _log(v.get("integrity_ok") is True, "Integrity OK")
        _log(v.get("checksum_match") is True, "Checksum match")

    # 4. Download
    r = requests.get(f"{_BASE_URL}/api/backup/download/{filename}", headers=h, timeout=30)
    _log(r.status_code == 200, "Download backup", f"size={len(r.content)} bytes")

    # 5. Export JSON
    r = requests.get(f"{_BASE_URL}/api/backup/export", headers=h, timeout=30)
    _log(r.status_code == 200, "JSON export", f"status={r.status_code}")
    if r.status_code == 200:
        export = r.json()
        _log(export.get("version") == "2.0", "Export version 2.0",
             f"version={export.get('version')}")
        data = export.get("data", {})
        _log("clienti" in data, "Export has clienti")
        _log("contratti" in data, "Export has contratti")


# == Phase 6: Public Portal ==================================================

def phase_6_portal(token: str):
    print("\n=== Phase 6: Public Portal ===")
    h = _auth_headers(token)

    # Check if portal is enabled via health
    try:
        r = requests.get(f"{_BASE_URL}/health", timeout=5)
        health = r.json()
        _log(r.status_code == 200, "Health endpoint accessible")
    except Exception as e:
        _log(False, "Health endpoint", f"error={e}")
        return

    # Create a test client for portal token
    r = requests.post(f"{_BASE_URL}/api/clients", json={
        "nome": "Portal", "cognome": "Test",
    }, headers=h)
    if r.status_code != 201:
        _warn("Could not create test client for portal test", f"status={r.status_code}")
        return
    client_id = r.json()["id"]

    # Try to generate share token
    r = requests.post(f"{_BASE_URL}/api/clients/{client_id}/share-anamnesi", headers=h)
    if r.status_code == 404:
        _warn("Public portal disabled (404) -- set PUBLIC_PORTAL_ENABLED=true")
        return
    _log(r.status_code in (200, 201), "Generate share token", f"status={r.status_code}")
    if r.status_code not in (200, 201):
        _log(False, "Generate share token", f"status={r.status_code}: {r.text[:100]}")
        return

    token_data = r.json()
    share_token = token_data.get("token", "")
    _log(len(share_token) > 10, "Share token generated", f"token={share_token[:8]}...")

    share_url = token_data.get("url", "")
    _log(len(share_url) > 0, "Share URL generated", f"url={share_url[:50]}...")
    if share_url:
        _log("https://" in share_url or "localhost" in share_url,
             "Share URL has valid scheme")

    # Validate token (public endpoint, query param)
    r = requests.get(f"{_BASE_URL}/api/public/anamnesi/validate",
                     params={"token": share_token}, timeout=5)
    _log(r.status_code == 200, "Validate share token (public endpoint)",
         f"status={r.status_code}")
    if r.status_code == 200:
        val = r.json()
        _log("client_name" in val, "Validation returns client info",
             f"client={val.get('client_name', '?')}")

    # Check invalid token handling
    fake_token = "00000000-0000-0000-0000-000000000000"
    r = requests.get(f"{_BASE_URL}/api/public/anamnesi/validate",
                     params={"token": fake_token}, timeout=5)
    _log(r.status_code in (404, 410, 422), "Invalid token rejected",
         f"status={r.status_code}")


# == Phase 7: Configuration Checklist =========================================

def phase_7_config():
    print("\n=== Phase 7: Configuration Checklist ===")

    # 1. data/ directory structure
    data_dir = PROJECT_ROOT / "data"
    _log(data_dir.exists(), "data/ directory exists")
    _log((data_dir / "crm.db").exists(), "Production DB (crm.db) exists")
    _log((data_dir / "crm_dev.db").exists(), "Development DB (crm_dev.db) exists")
    _log((data_dir / "catalog.db").exists(), "Catalog DB (catalog.db) exists")

    # 2. Media directory
    media_dir = data_dir / "media" / "exercises"
    _log(media_dir.exists(), "Exercise media directory exists")
    if media_dir.exists():
        photo_count = sum(1 for _ in media_dir.rglob("*.jpg"))
        photo_count += sum(1 for _ in media_dir.rglob("*.png"))
        photo_count += sum(1 for _ in media_dir.rglob("*.webp"))
        _log(photo_count > 100, "Exercise photos present",
             f"count={photo_count}")

    # 3. Backups directory
    backups_dir = data_dir / "backups"
    if backups_dir.exists():
        backup_count = sum(1 for _ in backups_dir.glob("*.sqlite"))
        _log(True, "Backups directory exists", f"backups={backup_count}")
    else:
        _warn("Backups directory does not exist yet")

    # 4. .env sanity
    env_file = data_dir / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        _log("JWT_SECRET=" in content and len(content.split("JWT_SECRET=")[1].split("\n")[0]) > 20,
             "JWT_SECRET is long enough (>20 chars)")
    else:
        _log(False, ".env file exists")

    # 5. Seed data JSON
    exercises_dir = data_dir / "exercises"
    _log((exercises_dir / "seed_exercises.json").exists(), "seed_exercises.json present")
    _log((exercises_dir / "seed_exercise_relations.json").exists(),
         "seed_exercise_relations.json present")
    _log((exercises_dir / "seed_exercise_media.json").exists(),
         "seed_exercise_media.json present")


# == Setup ====================================================================

def setup_trainer() -> str:
    """Register a test trainer and return JWT token."""
    import time
    email = f"dist-rehearsal-{int(time.time())}@test.com"
    r = requests.post(f"{_BASE_URL}/api/auth/register", json={
        "email": email,
        "nome": "Dist",
        "cognome": "Rehearsal",
        "password": "TestPass123!",
    })
    if r.status_code != 201:
        print(f"  [FAIL] Register trainer -- {r.status_code}: {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    print(f"  [PASS] Trainer registered: {email}")
    return token


# == Main =====================================================================

def main():
    parser = argparse.ArgumentParser(description="E2E Distribution Rehearsal")
    parser.add_argument("--base-url", default=_BASE_URL)
    args = parser.parse_args()

    _set_base_url(args.base_url)

    print(f"\n{'='*60}")
    print(f"  E2E Distribution Rehearsal -- Step 5 Launch Hardening")
    print(f"  Target: {_BASE_URL}")
    print(f"{'='*60}")

    # Health check
    try:
        r = requests.get(f"{_BASE_URL}/health", timeout=5)
        if r.status_code != 200:
            print(f"\n  [FAIL] Backend not healthy: {r.status_code}")
            sys.exit(1)
        print(f"\n  [PASS] Backend healthy: {r.json()}")
    except requests.ConnectionError:
        print(f"\n  [FAIL] Cannot connect to {_BASE_URL}")
        sys.exit(1)

    # Run phases
    phase_1_artifacts()
    phase_2_license()
    phase_3_enforcement()
    phase_4_network()

    token = setup_trainer()
    phase_5_backup(token)
    phase_6_portal(token)
    phase_7_config()

    print(f"\n{'='*60}")
    print(f"  Results: {PASS} PASS, {FAIL} FAIL, {WARN} WARN")
    print(f"{'='*60}")

    if WARN > 0:
        print(f"\n  Warnings are non-blocking but should be reviewed.")

    # Manual checklist
    print(f"\n  === Manual Checklist (not automatable) ===")
    print(f"  [ ] Install FitManager_Setup.exe on clean Windows machine")
    print(f"  [ ] Verify launcher.bat starts backend + frontend")
    print(f"  [ ] Access from LAN device (tablet/phone on same WiFi)")
    print(f"  [ ] Access via Tailscale VPN from external network")
    print(f"  [ ] Generate anamnesi link and open on smartphone")
    print(f"  [ ] Complete anamnesi form and verify data saved")
    print(f"  [ ] Test with LICENSE_ENFORCEMENT_ENABLED=true + no license.key")
    print(f"  [ ] Verify /licenza page shows and blocks access")

    print()
    sys.exit(1 if FAIL > 0 else 0)


if __name__ == "__main__":
    main()
