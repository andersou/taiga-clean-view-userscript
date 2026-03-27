#!/usr/bin/env python3
"""
Generate extension/content.js from taiga-clean-view.userscript.js, update
extension/manifest.json from the userscript header, and write a signed CRX3
to dist/ (optional --zip for Chrome Web Store).
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
USERSCRIPT = REPO_ROOT / "taiga-clean-view.userscript.js"
EXT_DIR = REPO_ROOT / "extension"
MANIFEST = EXT_DIR / "manifest.json"
CONTENT_OUT = EXT_DIR / "content.js"
DIST_DIR = REPO_ROOT / "dist"
SIGNING_KEY = EXT_DIR / "dev-signing-key.pem"

HEADER_RE = re.compile(
    r"// ==UserScript==\s*\n(.*?)\n// ==/UserScript==\s*\n",
    re.DOTALL,
)


def parse_userscript_metadata(text: str) -> dict:
    m = HEADER_RE.search(text)
    if not m:
        raise ValueError("Missing // ==UserScript== ... // ==/UserScript== block")
    block = m.group(1)
    meta: dict = {"matches": []}
    for raw in block.splitlines():
        line = raw.strip()
        if not line.startswith("// @"):
            continue
        rest = line[3:].lstrip()  # drop "//"
        key, _, value = rest.partition(" ")
        key = key.lstrip("@").lower()
        value = value.strip()
        if key == "match":
            meta["matches"].append(value)
        elif key in ("name", "version", "description", "author"):
            meta[key] = value
    need = ("name", "version", "description")
    for k in need:
        if k not in meta or not meta[k]:
            raise ValueError(f"Userscript header missing @{k}")
    return meta


def strip_userscript_header(text: str) -> str:
    return HEADER_RE.sub("", text, count=1).lstrip("\n")


def expand_match_patterns(patterns: list[str]) -> list[str]:
    """Add bare .../taskboard entry when .../taskboard/* is present. Deduplicate."""
    out: list[str] = []
    seen: set[str] = set()
    for p in patterns:
        p = p.strip()
        if not p or p in seen:
            continue
        seen.add(p)
        out.append(p)
        if p.endswith("/*"):
            bare = p[:-2]
            if bare and bare not in seen:
                seen.add(bare)
                out.append(bare)
    return out


def patch_userscript_body(body: str) -> str:
    """Convert Tampermonkey IIFE body to Chrome extension content script."""
    # Extension-specific storage + debug state
    body = body.replace(
        "let missingHeaderLogCount = 0;\n\n  function isDebugEnabled()",
        "let missingHeaderLogCount = 0;\n  let debugEnabled = false;\n"
        "  let cachedActive = false;\n\n  function isDebugEnabled()",
        1,
    )

    body = re.sub(
        r"function isDebugEnabled\(\) \{\s*"
        r"try \{\s*return localStorage\.getItem\(DEBUG_KEY\) === '1';\s*"
        r"\} catch \(_\) \{\s*return false;\s*\}\s*"
        r"\}",
        "function isDebugEnabled() {\n    return debugEnabled;\n  }",
        body,
        count=1,
    )

    body = re.sub(
        r"\bif \(!isDebugEnabled\(\)\) return;",
        "if (!debugEnabled) return;",
        body,
    )

    body = re.sub(
        r"  function loadState\(\) \{\s*"
        r"try \{\s*return localStorage\.getItem\(STORAGE_KEY\) === '1';\s*"
        r"\} catch \{\s*return false;\s*\}\s*"
        r"\}\s*\n\n"
        r"  function saveState\(active\) \{\s*"
        r"try \{\s*localStorage\.setItem\(STORAGE_KEY, active \? '1' : '0'\);\s*"
        r"\} catch \(_\) \{ \s*\}\s*"
        r"\}\s*\n\n",
        "  async function loadPrefs() {\n"
        "    const r = await chrome.storage.local.get([STORAGE_KEY, DEBUG_KEY]);\n"
        "    cachedActive = r[STORAGE_KEY] === '1';\n"
        "    debugEnabled = r[DEBUG_KEY] === '1';\n"
        "  }\n\n"
        "  async function persistState(active) {\n"
        "    cachedActive = active;\n"
        "    try {\n"
        "      await chrome.storage.local.set({ [STORAGE_KEY]: active ? '1' : '0' });\n"
        "    } catch (_) {\n"
        "      /* ignore */\n"
        "    }\n"
        "  }\n\n",
        body,
        count=1,
    )

    body = body.replace(
        "const active = loadState();",
        "const active = cachedActive;",
        1,
    )
    body = body.replace(
        "saveState(next);",
        "void persistState(next);",
        1,
    )

    storage_listener = (
        "\n"
        "  chrome.storage.onChanged.addListener((changes, area) => {\n"
        "    if (area !== 'local') return;\n"
        "    if (changes[STORAGE_KEY]) {\n"
        "      const v = changes[STORAGE_KEY].newValue;\n"
        "      cachedActive = v === '1';\n"
        "      applyRootState(cachedActive);\n"
        "    }\n"
        "    if (changes[DEBUG_KEY]) {\n"
        "      debugEnabled = changes[DEBUG_KEY].newValue === '1';\n"
        "    }\n"
        "  });\n"
    )
    body = body.replace(
        "  function isTaskboardRoute() {\n"
        "    return /\\/taskboard(\\/|$)/.test(location.pathname);\n"
        "  }\n\n"
        "  function init() {",
        "  function isTaskboardRoute() {\n"
        "    return /\\/taskboard(\\/|$)/.test(location.pathname);\n"
        "  }"
        + storage_listener
        + "\n"
        "  async function init() {",
        1,
    )

    old_init = (
        "  async function init() {\n"
        "    document.documentElement.setAttribute('data-taiga-clean-view-script', '1');\n"
        "    window.__taigaCleanViewLoadedAt = new Date().toISOString();\n"
        "    warn('Userscript init', {\n"
        "      href: location.href,\n"
        "      path: location.pathname,\n"
        "      readyState: document.readyState,\n"
        "      debug: isDebugEnabled(),\n"
        "    });\n\n"
        "    log('Init started', {\n"
        "      href: location.href,\n"
        "      readyState: document.readyState,\n"
        "      debug: isDebugEnabled(),\n"
        "    });\n\n"
        "    if (!isTaskboardRoute()) {\n"
        "      warn('URL does not look like taskboard route', location.pathname);\n"
        "    }\n\n"
        "    try {\n"
        "      injectStyles();\n"
        "      applyRootState(loadState());\n"
        "    } catch (err) {\n"
        "      error('Failed during initial setup', err);\n"
        "    }\n"
    )
    new_init = (
        "  async function init() {\n"
        "    await loadPrefs();\n\n"
        "    document.documentElement.setAttribute('data-taiga-clean-view-extension', '1');\n"
        "    window.__taigaCleanViewExtensionAt = new Date().toISOString();\n\n"
        "    log('Extension content script init', {\n"
        "      href: location.href,\n"
        "      path: location.pathname,\n"
        "      readyState: document.readyState,\n"
        "      debug: debugEnabled,\n"
        "    });\n\n"
        "    if (!isTaskboardRoute()) {\n"
        "      warn('URL does not look like taskboard route', location.pathname);\n"
        "    }\n\n"
        "    try {\n"
        "      injectStyles();\n"
        "      applyRootState(cachedActive);\n"
        "    } catch (err) {\n"
        "      error('Failed during initial setup', err);\n"
        "    }\n"
    )
    if old_init not in body:
        raise ValueError(
            "Could not patch init(): userscript layout changed unexpectedly "
            "(expected sync init with loadState / userscript markers)."
        )
    body = body.replace(old_init, new_init, 1)

    old_boot = (
        "  if (document.readyState === 'loading') {\n"
        "    document.addEventListener('DOMContentLoaded', init);\n"
        "  } else {\n"
        "    init();\n"
        "  }\n"
        "  warn('Userscript file evaluated');\n"
        "})();"
    )
    new_boot = (
        "  function start() {\n"
        "    if (document.readyState === 'loading') {\n"
        "      document.addEventListener('DOMContentLoaded', () => void init());\n"
        "    } else {\n"
        "      void init();\n"
        "    }\n"
        "  }\n\n"
        "  start();\n"
        "})();"
    )
    if old_boot not in body:
        raise ValueError(
            "Could not patch boot block: userscript layout changed unexpectedly."
        )
    body = body.replace(old_boot, new_boot, 1)

    if "localStorage" in body:
        raise ValueError(
            "Patch left localStorage references in content script; check userscript / patches."
        )
    if "loadState(" in body or "saveState(" in body:
        raise ValueError("Patch left loadState/saveState calls; check userscript / patches.")

    return body


def build_content_js(userscript_src: str) -> str:
    body_only = strip_userscript_header(userscript_src).strip()
    if not body_only.startswith("(function ()"):
        raise ValueError("Expected userscript body to start with (function () …")

    patched = patch_userscript_body(body_only)
    header = (
        "// Generated by scripts/build_extension.py from taiga-clean-view.userscript.js\n"
        "// Do not edit by hand; run: python3 scripts/build_extension.py\n\n"
    )
    return header + patched


def write_manifest(meta: dict, matches: list[str]) -> None:
    data = {
        "manifest_version": 3,
        "name": meta["name"],
        "version": meta["version"],
        "description": meta["description"],
        "content_scripts": [
            {
                "matches": matches,
                "js": ["content.js"],
                "run_at": "document_idle",
                "all_frames": False,
            }
        ],
        "permissions": ["storage"],
    }
    if meta.get("author"):
        data["author"] = meta["author"]

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def extension_zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(MANIFEST, arcname="manifest.json")
        zf.write(CONTENT_OUT, arcname="content.js")
    return buf.getvalue()


def write_zip_artifact(version: str, zip_bytes: bytes) -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_DIR / f"taiga-clean-view-extension-{version}.zip"
    zip_path.write_bytes(zip_bytes)
    return zip_path


def write_crx_artifact(version: str, zip_bytes: bytes, key_path: Path) -> Path:
    try:
        from crx3_pack import pack_crx3 as _pack
    except ImportError as e:
        raise RuntimeError(
            "CRX packing needs scripts/crx3_pack.py on PYTHONPATH and "
            "dependencies from scripts/requirements.txt (pip install cryptography)."
        ) from e
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    crx_path = DIST_DIR / f"taiga-clean-view-extension-{version}.crx"
    try:
        crx_path.write_bytes(_pack(zip_bytes, key_path))
    except ImportError as e:
        raise RuntimeError(
            "Install cryptography: pip install -r scripts/requirements.txt"
        ) from e
    return crx_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate extension from userscript; output CRX3 (+ optional ZIP for Web Store)."
    )
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Also write dist/*.zip (Chrome Web Store upload format)",
    )
    parser.add_argument(
        "--key",
        type=Path,
        default=SIGNING_KEY,
        help=f"PEM path for RSA private key (created if missing); default: {SIGNING_KEY}",
    )
    args = parser.parse_args()

    if not USERSCRIPT.is_file():
        print(f"Missing userscript: {USERSCRIPT}", file=sys.stderr)
        return 1

    src = USERSCRIPT.read_text(encoding="utf-8")
    meta = parse_userscript_metadata(src)
    matches = expand_match_patterns(meta.get("matches") or [])
    if not matches:
        raise ValueError("No @match entries in userscript header")

    content = build_content_js(src)
    EXT_DIR.mkdir(parents=True, exist_ok=True)
    CONTENT_OUT.write_text(content, encoding="utf-8")
    write_manifest(meta, matches)

    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    zip_bytes = extension_zip_bytes()
    crx_path = write_crx_artifact(meta["version"], zip_bytes, args.key)
    print(f"Wrote {CONTENT_OUT.relative_to(REPO_ROOT)}")
    print(f"Wrote {MANIFEST.relative_to(REPO_ROOT)}")
    print(f"Wrote {crx_path.relative_to(REPO_ROOT)}")
    if args.zip:
        zpath = write_zip_artifact(meta["version"], zip_bytes)
        print(f"Wrote {zpath.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1)
