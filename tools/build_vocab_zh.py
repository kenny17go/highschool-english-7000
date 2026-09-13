#!/usr/bin/env python3
"""
Build local Traditional-Chinese vocabulary bank for 高中英文 7000 V1.4.3.1.

Sources:
- CEEC 108-edition word/level list mirror (selection + level + POS)
- Legacy Taiwan high-school list (Level-7 supplement selection + fallback)
- ECDICT (English -> Chinese dictionary fallback)
- OpenCC s2twp conversion for Traditional Chinese / Taiwan wording

Output:
  data/vocabulary-zh.json
"""

from __future__ import annotations
import csv
import io
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from opencc import OpenCC
except ImportError:
    OpenCC = None

CURRENT_URL = "https://raw.githubusercontent.com/EngTW/English-for-Programmers/main/lists/Taiwan-high-school-6K-108-edition/Data/Taiwan-high-school-english-reference-vocabulary-list-108-edition.json"

LEGACY_URLS = [
    "https://raw.githubusercontent.com/mahavivo/english-wordlists/master/%E5%8F%B0%E7%81%A3%E9%AB%98%E4%B8%AD%E8%8B%B1%E6%96%87%E5%8F%83%E8%80%83%E8%A9%9E%E5%BD%99%E8%A1%A8.txt",
    "https://github.com/mahavivo/english-wordlists/raw/refs/heads/master/%E5%8F%B0%E7%81%A3%E9%AB%98%E4%B8%AD%E8%8B%B1%E6%96%87%E5%8F%83%E8%80%83%E8%A9%9E%E5%BD%99%E8%A1%A8.txt",
]

ECDICT_URL = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"
OUT = Path("data/vocabulary-zh.json")


def fetch_bytes(url: str, timeout: int = 180) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 hs7000-v1.4.3.1-builder"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_first(urls, timeout: int = 180) -> bytes:
    last_error = None
    for url in urls:
        try:
            print("Trying legacy vocabulary source:", url, flush=True)
            return fetch_bytes(url, timeout=timeout)
        except Exception as exc:
            last_error = exc
            print("Legacy source failed:", type(exc).__name__, exc, flush=True)
    raise RuntimeError(f"All legacy vocabulary sources failed: {last_error}")


def normalize_word(w):
    return str(w or "").lower().lstrip("*").strip()


def parse_legacy(text: str):
    result = {}
    pos_re = re.compile(
        r"^((?:adj\.|adv\.|n\.|v\.|prep\.|conj\.|pron\.|art\.|num\.|aux\.|int\.)[^\u4e00-\u9fff]*)",
        re.I,
    )
    for raw in text.splitlines():
        line = raw.strip()
        if not line or re.fullmatch(r"[A-Z]", line) or "大學學測" in line:
            continue
        m = re.match(
            r"^\*?([A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*)?)\s+(.+)$",
            line,
        )
        if not m:
            continue
        word = normalize_word(m.group(1))
        rest = m.group(2).strip()
        pm = pos_re.match(rest)
        pos = []
        meaning = rest
        if pm:
            pos = [x for x in re.split(r"[/;, ]+", pm.group(1)) if "." in x]
            meaning = rest[len(pm.group(0)):].strip()
        result[word] = {"meaning": meaning or "", "pos": pos}
    return result


def clean_translation(text: str) -> str:
    text = (text or "").replace("\\n", "；").replace("\n", "；").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[；;]{2,}", "；", text)
    return text.strip("；; ")


def main():
    print("Downloading CEEC 108-edition vocabulary list...", flush=True)
    current = json.loads(fetch_bytes(CURRENT_URL).decode("utf-8"))

    print("Downloading legacy Level-7 selection/fallback...", flush=True)
    legacy = parse_legacy(fetch_first(LEGACY_URLS).decode("utf-8", errors="ignore"))

    current_words = []
    current_set = set()
    for x in current:
        w = normalize_word(x.get("Word"))
        if not w:
            continue
        current_set.add(w)
        current_words.append({
            "word": w,
            "pos": x.get("PartsOfSpeech") or [],
            "level": int(x.get("Level") or 1),
        })

    extras = []
    for w, info in legacy.items():
        if w not in current_set and len(extras) < 1000:
            extras.append({
                "word": w,
                "pos": info.get("pos") or [],
                "level": 7,
            })

    selected = current_words + extras
    wanted = {x["word"] for x in selected}
    print("Selected words:", len(selected), flush=True)

    meanings = {}
    sources = {}
    for w in wanted:
        info = legacy.get(w)
        if info and clean_translation(info.get("meaning", "")):
            meanings[w] = clean_translation(info["meaning"])
            sources[w] = "legacy-tw"

    missing = wanted - meanings.keys()
    print("Need ECDICT fallback:", len(missing), flush=True)

    cc = OpenCC("s2twp") if OpenCC else None

    print("Downloading ECDICT fallback dictionary...", flush=True)
    raw = fetch_bytes(ECDICT_URL, timeout=300).decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(raw))
    for row in reader:
        w = normalize_word(row.get("word"))
        if w not in missing:
            continue
        trans = clean_translation(row.get("translation", ""))
        if not trans:
            continue
        if cc:
            trans = cc.convert(trans)
        meanings[w] = trans
        sources[w] = "ecdict-s2twp"
        missing.discard(w)
        if not missing:
            break

    for w in list(missing):
        info = legacy.get(w)
        if info and info.get("meaning"):
            meanings[w] = clean_translation(info["meaning"])
            sources[w] = "legacy-fallback"
            missing.discard(w)

    words = []
    for x in selected:
        w = x["word"]
        meaning = meanings.get(w, "").strip() or "—"
        words.append({
            "word": w,
            "pos": x["pos"],
            "level": x["level"],
            "meaning": meaning,
            "source": sources.get(w, "missing"),
        })

    missing_words = [x["word"] for x in words if x["meaning"] == "—"]
    summary = {
        "words": len(words),
        "current108": len(current_words),
        "level7Supplement": len(extras),
        "withMeaning": len(words) - len(missing_words),
        "missingMeaning": len(missing_words),
        "coverage": round((len(words) - len(missing_words)) / len(words), 6) if words else 0,
    }

    payload = {
        "version": "1.4.3.1",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "language": "zh-Hant-TW",
        "summary": summary,
        "attribution": {
            "currentList": "CEEC 108-edition vocabulary list mirror by EngTW/English-for-Programmers",
            "legacySelection": "mahavivo/english-wordlists Taiwan high-school list",
            "dictionaryFallback": "skywind3000/ECDICT",
            "conversion": "OpenCC s2twp",
        },
        "words": words,
        "missingWords": missing_words,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print("Wrote", OUT, OUT.stat().st_size, "bytes", flush=True)
    print("Summary:", summary, flush=True)

    if missing_words:
        print("Missing:", ", ".join(missing_words[:80]), flush=True)


if __name__ == "__main__":
    main()
