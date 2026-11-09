#!/usr/bin/env python3
"""Download product images for GamaQ 'not listed' game consoles from Wikimedia Commons."""

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "img" / "gamaq-not-listed"

# (subdir, filename, commons search/file title)
CONSOLES = [
    # Nintendo
    ("nintendo", "01-color-tv-game.jpg", "Nintendo Color TV-Game 15 (1978) 2.jpg"),
    ("nintendo", "02-famicom-disk-system.jpg", "Famicom Disk System.jpg"),
    ("nintendo", "03-game-and-watch.jpg", "Game & Watch Multi Screen.jpg"),
    ("nintendo", "04-game-boy-pocket.jpg", "Game Boy Pocket.jpg"),
    ("nintendo", "05-game-boy-light.jpg", "Game Boy Light.jpg"),
    ("nintendo", "06-game-boy-micro.jpg", "Game-Boy-Micro.jpg"),
    ("nintendo", "07-switch-variants.jpg", "Nintendo Switch – OLED Model.jpg"),
    # Sony
    ("sony", "01-ps-one.jpg", "PSone.jpg"),
    ("sony", "02-ps3-slim.jpg", "PlayStation 3 Slim.jpg"),
    ("sony", "03-ps4-slim.jpg", "PlayStation 4 Slim console.jpg"),
    ("sony", "04-ps5-slim.jpg", "PlayStation 5 Slim Digital Edition.jpg"),
    ("sony", "05-ps5-pro.jpg", "PlayStation 5 Pro.jpg"),
    ("sony", "06-psp-2000.jpg", "PSP-2000.jpg"),
    ("sony", "07-psp-3000.jpg", "PSP-3000.jpg"),
    ("sony", "08-psp-go.jpg", "PSP Go.jpg"),
    ("sony", "09-ps-vita-slim.jpg", "PlayStation Vita Slim.jpg"),
    # Sega
    ("sega", "01-sg-1000.jpg", "Sega SG-1000.jpg"),
    ("sega", "01b-sg-1000ii.jpg", "Sega SG-1000 II.jpg"),
    ("sega", "02-mark-iii.jpg", "Sega Mark III.jpg"),
    ("sega", "02b-master-system.jpg", "Sega-Master-System-Set.jpg"),
    ("sega", "03-mega-cd.jpg", "Sega-Genesis-CD-Model-1-Bare.jpg"),
    ("sega", "04-32x.jpg", "Sega 32X.jpg"),
    # Microsoft
    ("microsoft", "01-xbox-original.jpg", "Xbox console.jpg"),
    ("microsoft", "02-xbox-one-s.jpg", "Xbox One S All-Digital Edition.jpg"),
    ("microsoft", "03-xbox-one-x.jpg", "Microsoft-Xbox-One-X-Console-Set.jpg"),
    # NEC
    ("nec", "01-pc-engine-shuttle.jpg", "PC Engine Shuttle.jpg"),
    ("nec", "02-pc-engine-sg.jpg", "SuperGrafx-Console-Set.jpg"),
    ("nec", "03-pc-engine-gt.jpg", "NEC-TurboExpress-Upright-FL.jpg"),
    ("nec", "04-pc-engine-duo.jpg", "PC-Engine-Duo-Console-Set.png"),
    ("nec", "05-pc-fx.jpg", "PC-FX-Console-Set.jpg"),
    # SNK
    ("snk", "01-neo-geo-aes.jpg", "Neo-Geo-AES-Console-Set.jpg"),
    ("snk", "02-neo-geo-cd.jpg", "Neo-Geo-CD-TopLoader-wController-FL.jpg"),
    ("snk", "02b-neo-geo-cd-z.jpg", "Neo-Geo-CDZ-wController-FL.png"),
    ("snk", "03-neo-geo-pocket-color.jpg", "Neo-Geo-Pocket-Color-Blue-Left.jpg"),
    ("snk", "04-neo-geo-pocket-color-new.jpg", "Neo-Geo-Pocket-Color-Anthra-Left.png"),
]

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "GamaQImageCollector/1.0 (research; cloud-agent)"


def api_get(params: dict) -> dict:
    params = {**params, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def resolve_commons_file(title: str) -> tuple[str, str] | None:
    if not title.startswith("File:"):
        title = f"File:{title}"

    data = api_get(
        {
            "action": "query",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 800,
        }
    )
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        if "missing" in page:
            return None
        infos = page.get("imageinfo") or []
        if not infos:
            return None
        info = infos[0]
        return info.get("thumburl") or info.get("url"), info.get("mime", "")

    return None


def search_commons_file(query: str) -> tuple[str, str] | None:
    data = api_get(
        {
            "action": "query",
            "list": "search",
            "srsearch": f'filetype:bitmap {query}',
            "srnamespace": 6,
            "srlimit": 5,
        }
    )
    results = data.get("query", {}).get("search", [])
    for item in results:
        title = item["title"]
        resolved = resolve_commons_file(title)
        if resolved:
            return resolved
    return None


def download(url: str, dest: Path, retries: int = 4) -> None:
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                dest.write_bytes(resp.read())
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(4 * (attempt + 1))
    raise last_error  # type: ignore[misc]


def safe_ext(mime: str, fallback: str) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    return mapping.get(mime, fallback)


def main() -> int:
    manifest = []
    failures = []

    for subdir, filename, commons_title in CONSOLES:
        dest_dir = OUT_DIR / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename

        print(f"Fetching: {commons_title} -> {dest.relative_to(ROOT)}")

        if dest.exists() and dest.stat().st_size > 1000:
            print(f"  SKIP (already exists)")
            manifest.append(
                {
                    "subdir": subdir,
                    "filename": dest.name,
                    "commons_title": commons_title,
                    "source_url": "(cached)",
                    "path": str(dest.relative_to(ROOT)),
                }
            )
            continue

        resolved = resolve_commons_file(commons_title)
        if not resolved:
            resolved = search_commons_file(commons_title.replace(".jpg", ""))
        if not resolved:
            failures.append((commons_title, "not found on Commons"))
            print(f"  FAILED: not found")
            continue

        url, mime = resolved
        ext = Path(filename).suffix
        actual_ext = safe_ext(mime, ext)
        if actual_ext != ext:
            dest = dest.with_suffix(actual_ext)

        try:
            download(url, dest)
            size_kb = dest.stat().st_size // 1024
            print(f"  OK ({size_kb} KB)")
            manifest.append(
                {
                    "subdir": subdir,
                    "filename": dest.name,
                    "commons_title": commons_title,
                    "source_url": url,
                    "path": str(dest.relative_to(ROOT)),
                }
            )
        except Exception as exc:  # noqa: BLE001
            failures.append((commons_title, str(exc)))
            print(f"  FAILED: {exc}")

        time.sleep(2.5)

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nDownloaded: {len(manifest)} / {len(CONSOLES)}")
    if failures:
        print("Failures:")
        for title, reason in failures:
            print(f"  - {title}: {reason}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
