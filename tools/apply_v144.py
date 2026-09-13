#!/usr/bin/env python3
"""
Highschool English 7000 - V1.4.4 upgrade

This script upgrades the CURRENT repository in-place:
- fixes the missing LOCAL_VOCAB_URL declaration
- loads local vocabulary-details.json
- upgrades detailFor() to use WordNet-derived synonyms / antonyms / word family
- renames "字根字首" to the safer "字首・字尾・字族"
- bumps PWA cache + settings version
- builds data/vocabulary-details.json from the already-generated vocabulary-zh.json

It does NOT change STORAGE_KEY, so study progress is preserved.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from nltk.corpus import wordnet as wn

APP = Path("app.js")
INDEX = Path("index.html")
SW = Path("sw.js")
VOCAB = Path("data/vocabulary-zh.json")
DETAILS = Path("data/vocabulary-details.json")

PREFIXES = [
    ("under", "不足／在下"),
    ("inter", "在…之間"),
    ("trans", "跨越／轉移"),
    ("super", "在上／超越"),
    ("anti", "反對／對抗"),
    ("over", "過度／在上"),
    ("post", "在後／之後"),
    ("pre", "在前／預先"),
    ("sub", "在下／次級"),
    ("non", "非／不"),
    ("dis", "不／分離／相反"),
    ("mis", "錯誤／不當"),
    ("un", "不／相反"),
    ("re", "再／回"),
]

SUFFIXES = [
    ("ization", "名詞字尾：過程／結果"),
    ("isation", "名詞字尾：過程／結果"),
    ("ational", "形容詞字尾：與…有關"),
    ("fulness", "名詞字尾：性質／狀態"),
    ("lessness", "名詞字尾：缺乏…的狀態"),
    ("ability", "名詞字尾：能力／性質"),
    ("ibility", "名詞字尾：能力／性質"),
    ("ation", "名詞字尾：行為／過程／結果"),
    ("ition", "名詞字尾：行為／結果"),
    ("tion", "名詞字尾：行為／結果"),
    ("sion", "名詞字尾：行為／結果"),
    ("ment", "名詞字尾：狀態／結果"),
    ("ness", "名詞字尾：性質／狀態"),
    ("ence", "名詞字尾：狀態／性質"),
    ("ance", "名詞字尾：狀態／性質"),
    ("ity", "名詞字尾：性質／狀態"),
    ("ship", "名詞字尾：身分／關係／狀態"),
    ("ism", "名詞字尾：主義／現象"),
    ("ist", "名詞字尾：人／專業者"),
    ("able", "形容詞字尾：能…的"),
    ("ible", "形容詞字尾：能…的"),
    ("less", "形容詞字尾：沒有…的"),
    ("ful", "形容詞字尾：充滿…的"),
    ("ous", "形容詞字尾：具有…性質"),
    ("ive", "形容詞字尾：具有…性質"),
    ("al", "形容詞字尾：與…有關"),
    ("ic", "形容詞字尾：與…有關"),
    ("ize", "動詞字尾：使成為／使…化"),
    ("ise", "動詞字尾：使成為／使…化"),
    ("ify", "動詞字尾：使…化"),
    ("ly", "副詞字尾"),
    ("er", "名詞字尾：人／物；亦可能為比較級"),
    ("or", "名詞字尾：人／物"),
]

# Keep some known manually curated data when it is better than automatic data.
MANUAL = {
    "absence": {
        "syn": ["lack", "nonattendance"],
        "ant": ["presence"],
        "family": ["absent"],
    },
    "ability": {
        "syn": ["capacity", "skill", "talent"],
        "ant": ["inability"],
        "family": ["able", "inability"],
    },
    "accept": {
        "syn": ["receive", "admit", "approve"],
        "ant": ["reject", "refuse"],
        "family": ["acceptable", "acceptance"],
    },
    "achieve": {
        "syn": ["accomplish", "attain", "reach"],
        "ant": ["fail"],
        "family": ["achievement"],
    },
}

def norm(s: str) -> str:
    return str(s or "").lower().replace("_", " ").strip()

def is_good_term(s: str, base: str) -> bool:
    if not s or s == base:
        return False
    if len(s) > 28:
        return False
    if any(ch.isdigit() for ch in s):
        return False
    # Keep short phrases but avoid dictionary-style clutter.
    if len(s.split()) > 3:
        return False
    return all(ch.isalpha() or ch in " -'" for ch in s)

def wordnet_details(word: str):
    syn = []
    ant = []
    family = []

    seen_syn, seen_ant, seen_family = set(), set(), set()
    synsets = wn.synsets(word)

    for synset in synsets[:10]:
        for lemma in synset.lemmas():
            name = norm(lemma.name())
            if is_good_term(name, word) and name not in seen_syn:
                seen_syn.add(name)
                syn.append(name)

            for antonym in lemma.antonyms():
                name = norm(antonym.name())
                if is_good_term(name, word) and name not in seen_ant:
                    seen_ant.add(name)
                    ant.append(name)

            for related in lemma.derivationally_related_forms():
                name = norm(related.name())
                if is_good_term(name, word) and name not in seen_family:
                    seen_family.add(name)
                    family.append(name)

    return syn[:6], ant[:5], family[:8]

def morphology_hint(word: str, family: list[str]) -> str:
    parts = []

    for p, meaning in PREFIXES:
        if word.startswith(p) and len(word) >= len(p) + 4:
            parts.append(f"字首 {p}-（{meaning}）")
            break

    for s, meaning in SUFFIXES:
        if word.endswith(s) and len(word) >= len(s) + 3:
            parts.append(f"字尾 -{s}（{meaning}）")
            break

    if family:
        parts.append("字族：" + "、".join(family[:6]))

    if not parts:
        return "未辨識出可靠字首／字尾；建議搭配例句與字族記憶"
    return "｜".join(parts)

def build_details():
    if not VOCAB.exists():
        raise SystemExit(
            "data/vocabulary-zh.json 不存在。請先成功執行 Build vocabulary meanings。"
        )

    data = json.loads(VOCAB.read_text(encoding="utf-8"))
    words = data.get("words", [])
    if len(words) < 6000:
        raise SystemExit(
            f"vocabulary-zh.json 只有 {len(words)} 字，應先完成本地中文字庫建置。"
        )

    vocab_set = {norm(x.get("word")) for x in words}
    out = {}

    for i, item in enumerate(words, 1):
        word = norm(item.get("word"))
        if not word:
            continue

        auto_syn, auto_ant, auto_family = wordnet_details(word)
        manual = MANUAL.get(word, {})

        syn = manual.get("syn") or auto_syn
        ant = manual.get("ant") or auto_ant
        family = manual.get("family") or auto_family

        # Prefer family words that actually belong to this learning bank.
        in_bank_family = [x for x in family if x in vocab_set]
        if in_bank_family:
            family = in_bank_family + [x for x in family if x not in vocab_set]
        family = list(dict.fromkeys(family))[:8]

        out[word] = {
            "syn": list(dict.fromkeys(syn))[:6],
            "ant": list(dict.fromkeys(ant))[:5],
            "family": family,
            "structure": morphology_hint(word, family),
        }

        if i % 1000 == 0:
            print("details", i, "/", len(words), flush=True)

    payload = {
        "version": "1.4.4",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "NLTK WordNet + conservative morphology rules + small manual overrides",
        "note": (
            "Synonyms/antonyms/word-family are learning aids. "
            "Prefix/suffix hints are conservative form-based hints, not claims of full etymology."
        ),
        "summary": {
            "words": len(out),
            "withSynonyms": sum(bool(x["syn"]) for x in out.values()),
            "withAntonyms": sum(bool(x["ant"]) for x in out.values()),
            "withFamily": sum(bool(x["family"]) for x in out.values()),
            "withStructure": sum(
                not x["structure"].startswith("未辨識") for x in out.values()
            ),
        },
        "words": out,
    }

    DETAILS.parent.mkdir(parents=True, exist_ok=True)
    DETAILS.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print("wrote", DETAILS, payload["summary"], flush=True)

def patch_app():
    text = APP.read_text(encoding="utf-8")

    # Fix the exact V1.4.3 bug: loadBank() referenced LOCAL_VOCAB_URL
    # without declaring it.
    if "const LOCAL_VOCAB_URL=" not in text:
        marker = "const LEGACY_URL="
        pos = text.find("\n", text.find(marker))
        if pos < 0:
            raise SystemExit("找不到 LEGACY_URL，無法安全修補 app.js")
        insertion = (
            "\nconst LOCAL_VOCAB_URL='data/vocabulary-zh.json?v=1.4.4';"
            "\nconst DETAILS_URL='data/vocabulary-details.json?v=1.4.4';"
            "\nlet WORD_DETAILS={};"
        )
        text = text[:pos] + insertion + text[pos:]
    else:
        text = re.sub(
            r"const LOCAL_VOCAB_URL=.*?;",
            "const LOCAL_VOCAB_URL='data/vocabulary-zh.json?v=1.4.4';",
            text,
            count=1,
        )
        if "const DETAILS_URL=" not in text:
            marker = re.search(r"const LOCAL_VOCAB_URL=.*?;\n", text)
            if not marker:
                raise SystemExit("找不到 LOCAL_VOCAB_URL 宣告")
            insertion = (
                "const DETAILS_URL='data/vocabulary-details.json?v=1.4.4';\n"
                "let WORD_DETAILS={};\n"
            )
            text = text[:marker.end()] + insertion + text[marker.end():]
        elif "let WORD_DETAILS=" not in text:
            text = text.replace(
                "const DETAILS_URL='data/vocabulary-details.json?v=1.4.4';",
                "const DETAILS_URL='data/vocabulary-details.json?v=1.4.4';\nlet WORD_DETAILS={};",
                1,
            )

    old_detail = (
        "function detailFor(w){const e=ENRICH[w.word]||{};"
        "return {example:genericExample(w),collocations:genericCollocations(w),"
        "root:rootHint(w.word),syn:e.syn||[],ant:e.ant||[],conf:confusables(w)}}"
    )

    new_detail = (
        "function detailFor(w){"
        "const e=ENRICH[w.word]||{},a=WORD_DETAILS[w.word]||{};"
        "const syn=(e.syn&&e.syn.length)?e.syn:(a.syn||[]),"
        "ant=(e.ant&&e.ant.length)?e.ant:(a.ant||[]),"
        "conf=(e.conf&&e.conf.length)?e.conf:confusables(w);"
        "return {"
        "example:e.ex||genericExample(w),"
        "collocations:(e.col&&e.col.length)?e.col:genericCollocations(w),"
        "root:e.root||a.structure||rootHint(w.word),"
        "syn,ant,conf,family:a.family||[]"
        "}}"
    )

    if old_detail in text:
        text = text.replace(old_detail, new_detail, 1)
    elif "a=WORD_DETAILS[w.word]" not in text:
        # Regex fallback for the current one-line implementation.
        text, n = re.subn(
            r"function detailFor\(w\)\{const e=ENRICH\[w\.word\]\|\|\{\};return \{.*?\}\}",
            new_detail,
            text,
            count=1,
        )
        if n != 1:
            raise SystemExit("找不到 detailFor()，停止以避免破壞 app.js")

    loader = (
        "\nasync function loadWordDetails(){"
        "try{"
        "const r=await fetch(DETAILS_URL,{cache:'no-store'});"
        "if(!r.ok)throw new Error('details '+r.status);"
        "const x=await r.json();"
        "WORD_DETAILS=x.words||{};"
        "console.info('V1.4.4 details loaded',Object.keys(WORD_DETAILS).length);"
        "if(bank.length)renderAll();"
        "}catch(e){console.warn('word details unavailable',e)}"
        "}\n"
    )

    if "async function loadWordDetails()" not in text:
        marker = "async function loadBank()"
        idx = text.find(marker)
        if idx < 0:
            raise SystemExit("找不到 loadBank()")
        text = text[:idx] + loader + text[idx:]

    text = text.replace(
        "bind();loadCorpusData();loadBank();",
        "bind();loadCorpusData();loadWordDetails();loadBank();",
        1,
    )

    # Missing meaning hint should also cover the local placeholder.
    text = text.replace(
        "w.meaning==='中文釋義待補充'?'此詞在舊版中文資料未對應；仍可先用例句、字根與測驗學習。':''",
        "(w.meaning==='中文釋義待補充'||w.meaning==='—')?'此詞的中文資料仍待校正；可先用例句、字族與測驗學習。':''",
    )

    APP.write_text(text, encoding="utf-8")

def patch_index():
    text = INDEX.read_text(encoding="utf-8")
    text = text.replace("字根字首", "字首・字尾・字族")
    text = re.sub(
        r"版本 V1\.4\.[0-9.]+ · [^<]*",
        "版本 V1.4.4 · 本地中文釋義 + 完整單字資訊 + 101–115 學測語料庫",
        text,
        count=1,
    )
    INDEX.write_text(text, encoding="utf-8")

def patch_sw():
    text = SW.read_text(encoding="utf-8")
    text = re.sub(
        r"const CACHE='hs7000-v[^']+';",
        "const CACHE='hs7000-v1.4.4';",
        text,
        count=1,
    )

    if "./data/vocabulary-details.json" not in text:
        if "'./data/vocabulary-zh.json'" in text:
            text = text.replace(
                "'./data/vocabulary-zh.json'",
                "'./data/vocabulary-zh.json','./data/vocabulary-details.json'",
                1,
            )
        elif "'./data/gsat-corpus-stats.json'" in text:
            text = text.replace(
                "'./data/gsat-corpus-stats.json'",
                "'./data/gsat-corpus-stats.json','./data/vocabulary-details.json'",
                1,
            )
        else:
            raise SystemExit("找不到 Service Worker ASSETS 資料陣列")

    SW.write_text(text, encoding="utf-8")

def validate():
    app = APP.read_text(encoding="utf-8")
    idx = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")
    details = json.loads(DETAILS.read_text(encoding="utf-8"))
    vocab = json.loads(VOCAB.read_text(encoding="utf-8"))

    assert "const LOCAL_VOCAB_URL='data/vocabulary-zh.json?v=1.4.4';" in app
    assert "const DETAILS_URL='data/vocabulary-details.json?v=1.4.4';" in app
    assert "async function loadWordDetails()" in app
    assert "bind();loadCorpusData();loadWordDetails();loadBank();" in app
    assert "字首・字尾・字族" in idx
    assert "V1.4.4" in idx
    assert "hs7000-v1.4.4" in sw
    assert "./data/vocabulary-details.json" in sw

    assert details["version"] == "1.4.4"
    assert len(details["words"]) >= 6000
    assert details["words"]["absence"]["syn"]
    assert "presence" in details["words"]["absence"]["ant"]
    assert details["words"]["absence"]["family"]
    assert "字族" in details["words"]["absence"]["structure"]

    by_word = {x["word"]: x for x in vocab["words"]}
    assert by_word["absence"]["meaning"] not in ("", "—", "中文釋義待補充")

    print("V1.4.4 validation passed")
    print("absence meaning:", by_word["absence"]["meaning"])
    print("absence details:", details["words"]["absence"])

def main():
    for p in (APP, INDEX, SW, VOCAB):
        if not p.exists():
            raise SystemExit(f"缺少必要檔案：{p}")

    build_details()
    patch_app()
    patch_index()
    patch_sw()
    validate()

if __name__ == "__main__":
    main()
