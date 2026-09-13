#!/usr/bin/env python3
"""
GSAT English corpus builder v1.4.2

Data-quality changes:
1) Extract only the English-exam segment from official CEEC PDFs/work reports.
2) Robust section detection even when pdftotext inserts spaces between Chinese characters.
3) Remove common exam-instruction / layout boilerplate words from lexical frequency.
4) Conservative English lemmatization (made->make, used->use, studies->study, etc.).
5) Preserve surfaceForms so counts remain auditable.
6) Store per-year + per-section counts for every lemma.
7) Never store the full exam text in the generated JSON.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOURCES = {
    101: "https://www.ceec.edu.tw/files/file_pool/1/0j076570671923496609/02-101%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7%E5%AE%9A%E7%A8%BF.pdf",
    102: "https://www.ceec.edu.tw/files/file_pool/1/0j051824585770646720/102%E5%B9%B4%E5%AD%B8%E7%A7%91%E8%83%BD%E5%8A%9B%E6%B8%AC%E9%A9%97%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A_00.pdf",
    103: "https://www.ceec.edu.tw/files/file_pool/1/0j076572147183041652/02-103%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87-%E5%AE%9A%E7%A8%BF.pdf",
    104: "https://www.ceec.edu.tw/files/file_pool/1/0j076572827714606282/02-104%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E5%AE%9A%E7%A8%BF.pdf",
    105: "https://www.ceec.edu.tw/files/file_pool/1/0j051825763397987863/105%E5%AD%B8%E6%B8%AC%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A.pdf",
    106: "https://www.ceec.edu.tw/files/file_pool/1/0j051826215298462880/106%E5%AD%B8%E6%B8%AC%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A.pdf",
    107: "https://www.ceec.edu.tw/files/file_pool/1/0j051826568834816834/107%E5%AD%B8%E6%B8%AC%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A.pdf",
    108: "https://www.ceec.edu.tw/files/file_pool/1/0j301533916033318514/108%E5%AD%B8%E6%B8%AC%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A_%E5%AE%8C%E6%88%90%E6%AA%9420190705.pdf",
    109: "https://www.ceec.edu.tw/files/file_pool/1/0k050359836694452838/02-109%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7-%E5%AE%9A%E7%A8%BF.pdf",
    110: "https://www.ceec.edu.tw/files/file_pool/1/0L022396748545177938/02-110%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7.pdf",
    111: "https://www.ceec.edu.tw/files/file_pool/1/0m053357638065462325/02-111%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7.pdf",
    112: "https://www.ceec.edu.tw/files/file_pool/1/0N014423635146157074/02-112%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7.pdf",
    113: "https://www.ceec.edu.tw/files/file_pool/1/0O021576671649197989/02-113%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E7%A7%91%E8%A9%A6%E9%A1%8C.pdf",
    114: "https://www.ceec.edu.tw/files/file_pool/1/0p056425554473267580/02-114%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E9%A1%8C.pdf",
    115: "https://www.ceec.edu.tw/files/file_pool/1/0q054532302653501476/02-115%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7.pdf",
}

WORK_REPORT_YEARS = {102, 105, 106, 107, 108}

SECTION_ORDER = [
    ("vocabulary", ("詞彙題", "詞彙")),
    ("cloze", ("綜合測驗",)),
    ("fill", ("文意選填",)),
    ("discourse", ("篇章結構",)),
    ("reading", ("閱讀測驗",)),
    ("mixed", ("混合題",)),
    ("translation", ("中譯英",)),
    ("writing", ("英文作文", "英文寫作")),
]

# Ordinary English function words are excluded because this statistic is meant to
# prioritize vocabulary learning, not syntactic frequency.
STOP_WORDS = set("""
a an the and or but if then than that this these those
i you he she it we they me him her us them my your his our their its
is am are was were be been being have has had do does did
can could may might must shall should will would
of to in on at by for from with as into over under about after before
between through during without within not no so very more most less least
many much some any each every all both either neither
one two three four five first second third
who whom whose which what when where why how
""".split())

# Boilerplate that appears because it is an exam, not because the word is
# meaningfully tested in the passage. Keeping these would inflate fake "high frequency".
EXAM_BOILERPLATE = set("""
passage passages following follow blank blanks answer answers answered
question questions item items choose choice choices correct appropriate
best according paragraph paragraphs section sections part parts
test testing examinee examinees page pages points point score scores
read reading write writing sentence sentences word words
number numbers option options selected select selection
""".split())

WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")

IRREGULAR = {
    "am":"be","is":"be","are":"be","was":"be","were":"be","been":"be","being":"be",
    "has":"have","had":"have","having":"have",
    "does":"do","did":"do","done":"do","doing":"do",
    "goes":"go","went":"go","gone":"go","going":"go",
    "comes":"come","came":"come","coming":"come",
    "makes":"make","made":"make","making":"make",
    "takes":"take","took":"take","taken":"take","taking":"take",
    "uses":"use","used":"use","using":"use",
    "says":"say","said":"say","saying":"say",
    "gets":"get","got":"get","gotten":"get","getting":"get",
    "gives":"give","gave":"give","given":"give","giving":"give",
    "finds":"find","found":"find","finding":"find",
    "thinks":"think","thought":"think","thinking":"think",
    "knows":"know","knew":"know","known":"know","knowing":"know",
    "sees":"see","saw":"see","seen":"see","seeing":"see",
    "leaves":"leave","left":"leave","leaving":"leave",
    "feels":"feel","felt":"feel","feeling":"feel",
    "keeps":"keep","kept":"keep","keeping":"keep",
    "becomes":"become","became":"become","becoming":"become",
    "means":"mean","meant":"mean","meaning":"mean",
    "holds":"hold","held":"hold","holding":"hold",
    "brings":"bring","brought":"bring","bringing":"bring",
    "builds":"build","built":"build","building":"build",
    "begins":"begin","began":"begin","begun":"begin","beginning":"begin",
    "runs":"run","ran":"run","running":"run",
    "writes":"write","wrote":"write","written":"write","writing":"write",
    "reads":"read","reading":"read",
    "children":"child","men":"man","women":"woman","people":"person",
    "mice":"mouse","feet":"foot","teeth":"tooth",
    "better":"good","best":"good","worse":"bad","worst":"bad",
}

def download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 GSAT-corpus-builder/1.4.2"})
    with urllib.request.urlopen(req, timeout=90) as response, open(path, "wb") as f:
        f.write(response.read())

def pdf_text(pdf: Path, txt: Path) -> str:
    subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)
    return txt.read_text("utf-8", errors="ignore")

def compact_cjk(s: str) -> str:
    """Remove PDF-inserted spaces between CJK characters while preserving English spacing."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"([\u3400-\u9fff])\s+([\u3400-\u9fff])", r"\1\2", s)
    return s

def normalized_line(line: str) -> str:
    return re.sub(r"\s+", "", compact_cjk(line))

def locate_heading_lines(text: str):
    """Return (offset,key,line) headings using line-level matching."""
    found = []
    offset = 0
    for line in text.splitlines(True):
        norm = normalized_line(line)
        for key, labels in SECTION_ORDER:
            if any(label in norm for label in labels):
                found.append((offset, key, norm))
                break
        offset += len(line)
    return found

def extract_exam_segment(text: str, year: int) -> tuple[str, str]:
    """
    Find the actual English test segment.
    Especially important for 102/105-108 where the official URL is a work report.
    """
    headings = locate_heading_lines(text)
    vocab_positions = [p for p, k, _ in headings if k == "vocabulary"]
    if not vocab_positions:
        return text, "fallback_full_pdf"

    vocab = vocab_positions[0]
    # Start near the English-exam heading immediately before vocabulary.
    start = max(0, vocab - 6000)
    prefix = text[start:vocab]
    english_matches = list(re.finditer(r"英\s*文\s*(?:考\s*科)?", prefix))
    if english_matches:
        start += english_matches[-1].start()

    tail = text[start:]
    local_headings = locate_heading_lines(tail)
    writing_positions = [p for p, k, _ in local_headings if k == "writing"]

    # End shortly after the writing prompt. For work reports this prevents
    # later analysis / other subjects from contaminating counts.
    if writing_positions:
        wpos = writing_positions[0]
        after = tail[wpos:]
        page_breaks = [m.start() for m in re.finditer(r"\f", after)]
        if len(page_breaks) >= 2:
            end = wpos + page_breaks[1]
        elif page_breaks:
            end = wpos + page_breaks[0] + 1
        else:
            end = min(len(tail), wpos + 8000)
        segment = tail[:end]
    else:
        segment = tail[:60000] if year in WORK_REPORT_YEARS else tail

    quality = "official_work_report_exam_extract" if year in WORK_REPORT_YEARS else "official_exam_pdf"
    return segment, quality

def surface_tokens(text: str):
    return [m.group(0).lower().replace("’", "'") for m in WORD_RE.finditer(text)]

def lemma(word: str) -> str:
    """Conservative lemmatizer for vocabulary-frequency aggregation."""
    w = word.lower()
    if w in IRREGULAR:
        return IRREGULAR[w]
    if "'" in w:
        w = w.split("'")[0]
    if len(w) <= 3:
        return w

    # plural / 3rd person
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith(("ches","shes","sses","xes","zes")) and len(w) > 5:
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss","us","is")) and len(w) > 4:
        return w[:-1]

    # past tense
    if w.endswith("ied") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ed") and len(w) > 4:
        base = w[:-2]
        if base.endswith(base[-1:] * 2) and len(base) > 3:
            base = base[:-1]
        if base.endswith(("at","iz","bl")):
            return base + "e"
        # hoped -> hope, used is already irregular
        if len(base) >= 3 and base[-1] not in "aeiou" and w[:-1].endswith("e"):
            return w[:-1]
        return base

    # -ing
    if w.endswith("ing") and len(w) > 5:
        base = w[:-3]
        if len(base) > 3 and base[-1] == base[-2] and base[-1] not in "lsz":
            base = base[:-1]
        # making -> make, taking -> take
        if base.endswith(("mak","tak","giv","writ","mov","us","chang","creat")):
            return base + "e"
        return base

    return w

def is_content_word(w: str) -> bool:
    return len(w) > 1 and w not in STOP_WORDS and w not in EXAM_BOILERPLATE

def lexical_tokens(text: str):
    result = []
    for surface in surface_tokens(text):
        base = lemma(surface)
        if is_content_word(base):
            result.append((base, surface))
    return result

def split_sections(text: str):
    headings = locate_heading_lines(text)
    # Keep the first occurrence of each section and sort by actual position.
    first = {}
    for pos, key, _ in headings:
        first.setdefault(key, pos)
    ordered = sorted((pos, key) for key, pos in first.items())
    result = {}
    for i, (pos, key) in enumerate(ordered):
        end = ordered[i + 1][0] if i + 1 < len(ordered) else len(text)
        result[key] = text[pos:end]
    return result

def count_chunk(chunk: str):
    lemmas = Counter()
    forms = defaultdict(Counter)
    for base, surface in lexical_tokens(chunk):
        lemmas[base] += 1
        forms[base][surface] += 1
    return lemmas, forms

def main():
    out = Path("data/gsat-corpus-stats.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    yearly = {}
    aggregate = Counter()
    word_years = defaultdict(set)
    by_year = defaultdict(Counter)
    by_section = defaultdict(Counter)
    surface_forms = defaultdict(Counter)

    with tempfile.TemporaryDirectory() as td_raw:
        td = Path(td_raw)
        for year, url in SOURCES.items():
            pdf = td / f"{year}.pdf"
            txt = td / f"{year}.txt"

            print("fetch", year, url, flush=True)
            download(url, pdf)
            raw = pdf_text(pdf, txt)
            exam, source_quality = extract_exam_segment(raw, year)

            counts, forms = count_chunk(exam)
            aggregate.update(counts)
            by_year[year].update(counts)

            for w in counts:
                word_years[w].add(year)
            for w, c in forms.items():
                surface_forms[w].update(c)

            sec_stats = {}
            sections = split_sections(exam)
            for sec, chunk in sections.items():
                sc, sf = count_chunk(chunk)
                by_section[sec].update(sc)
                for w, c in sf.items():
                    surface_forms[w].update(c)
                sec_stats[sec] = {
                    "tokens": sum(sc.values()),
                    "unique": len(sc),
                }

            yearly[str(year)] = {
                "source": url,
                "sourceQuality": source_quality,
                "tokens": sum(counts.values()),
                "unique": len(counts),
                "sections": sec_stats,
                "sectionCount": len(sec_stats),
                "status": "tokenized",
            }

    words = {}
    for w, count in aggregate.most_common():
        years = sorted(word_years[w])
        sections = {s: counter[w] for s, counter in by_section.items() if counter[w]}
        forms = dict(surface_forms[w].most_common(12))
        words[w] = {
            "count": count,
            "yearCount": len(years),
            "years": years,
            "byYear": {str(y): by_year[y][w] for y in years},
            "sections": sections,
            "surfaceForms": forms,
        }

    section_coverage = sum(1 for y in yearly.values() if y["sectionCount"] >= 4)
    data = {
        "version": "1.4.2",
        "range": [101, 115],
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "years": yearly,
        "summary": {
            "papers": len(yearly),
            "tokens": sum(x["tokens"] for x in yearly.values()),
            "unique": len(aggregate),
            "sectionCoverageYears": section_coverage,
        },
        "words": words,
        "quality": {
            "lemmatized": True,
            "boilerplateFiltered": True,
            "surfaceFormsPreserved": True,
            "fullExamTextStored": False,
            "workReportYears": sorted(WORK_REPORT_YEARS),
        },
        "method": (
            "Official CEEC PDFs -> pdftotext -> isolate English exam -> robust section detection "
            "-> conservative lemmatization -> stop-word + exam-boilerplate filtering -> derived statistics only. "
            "Full exam text is not stored."
        ),
    }

    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print("wrote", out, out.stat().st_size)
    print("summary", data["summary"])

if __name__ == "__main__":
    main()
