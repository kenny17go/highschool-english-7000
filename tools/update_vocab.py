#!/usr/bin/env python3
"""
高中英文 7000 字學習系統 — Stable Vocabulary Updater
Current payload: V1.4.6 真實例句修正版

核心原則：
1. 禁止用 "The word X..." / "In this passage, the word X..." 冒充例句。
2. 已人工校正：顯示真正使用該字的自然高中程度例句 + 繁中翻譯。
3. 尚未校正：顯示「例句待校正」，不捏造不自然句子。
4. 品質稽核依 101–115 學測語料重要度排序，後續優先補高價值單字。
5. 固定使用 tools/update_vocab.py；不新增 Workflow。
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

APP = Path("app.js")
INDEX = Path("index.html")
SW = Path("sw.js")
VOCAB = Path("data/vocabulary-zh.json")
EXAMPLES = Path("data/vocabulary-examples.json")
AUDIT = Path("data/vocabulary-quality-audit.json")
CORPUS = Path("data/gsat-corpus-stats.json")

VERSION = "1.4.6"

# 原創、可直接用於學習的高中程度例句。
# 每一個句子都必須真正使用目標字，而不是描述「這個單字」。
MANUAL = {
    "absence": (
        "Her repeated absence from class made it difficult for her to keep up with the lessons.",
        "她一再缺課，使她很難跟上課程進度。"
    ),
    "ability": (
        "She has the ability to explain difficult ideas clearly.",
        "她有能力把困難的概念解釋得很清楚。"
    ),
    "abandon": (
        "The hikers had to abandon their plan because of the sudden storm.",
        "登山客因為突如其來的暴風雨，只好放棄原本的計畫。"
    ),
    "abbreviate": (
        "To save space, the editor abbreviated several common expressions in the chart.",
        "為了節省空間，編輯把圖表中的幾個常用詞組縮寫了。"
    ),
    "abolish": (
        "The government decided to abolish the outdated rule after years of public debate.",
        "經過多年的公共討論後，政府決定廢除這項過時的規定。"
    ),
    "absorb": (
        "Plants absorb water through their roots and use it to grow.",
        "植物透過根部吸收水分，並利用水分生長。"
    ),
    "abstract": (
        "Some abstract ideas become easier to understand when they are explained with examples.",
        "有些抽象概念在搭配例子說明後會比較容易理解。"
    ),
    "abundant": (
        "Fresh water is abundant in some regions but extremely limited in others.",
        "淡水在某些地區很充足，但在其他地區卻極為有限。"
    ),
    "abuse": (
        "The new policy was designed to prevent the abuse of personal information.",
        "這項新政策是為了防止個人資料遭到濫用。"
    ),
    "academic": (
        "The school provides extra academic support before major exams.",
        "學校會在大型考試前提供額外的學業輔導。"
    ),
    "accelerate": (
        "New technology may accelerate the spread of information across the world.",
        "新科技可能會加速資訊在全球傳播的速度。"
    ),
    "accept": (
        "Learning to accept different opinions is an important part of teamwork.",
        "學會接受不同的意見，是團隊合作中很重要的一部分。"
    ),
    "access": (
        "Students can access the digital library from home with their school accounts.",
        "學生可以使用學校帳號從家中存取數位圖書館。"
    ),
    "accompany": (
        "A teacher will accompany the students on their visit to the science museum.",
        "一位老師會陪同學生參觀科學博物館。"
    ),
    "accomplish": (
        "The team worked together to accomplish a task that seemed impossible at first.",
        "這個團隊共同合作，完成了一項起初看似不可能的任務。"
    ),
    "accumulate": (
        "Small amounts of plastic can accumulate in the ocean over many years.",
        "少量的塑膠經過多年可能會逐漸累積在海洋中。"
    ),
    "accurate": (
        "Accurate information is essential when you write a research report.",
        "撰寫研究報告時，準確的資訊非常重要。"
    ),
    "accuse": (
        "It is unfair to accuse someone without enough evidence.",
        "在沒有足夠證據的情況下指控別人是不公平的。"
    ),
    "achieve": (
        "With steady practice, you can achieve your academic goals.",
        "只要持續練習，你就能達成學業上的目標。"
    ),
    "acknowledge": (
        "The writer acknowledged that the first explanation was incomplete.",
        "作者承認第一個解釋並不完整。"
    ),
    "adjust": (
        "It may take a few weeks to adjust to a new study schedule.",
        "適應新的讀書作息可能需要幾個星期。"
    ),
    "affect": (
        "Lack of sleep can affect your concentration in class.",
        "睡眠不足會影響你在課堂上的專注力。"
    ),
    "analyze": (
        "Students were asked to analyze the causes of the problem.",
        "學生被要求分析這個問題發生的原因。"
    ),
    "annual": (
        "The school holds an annual science fair every spring.",
        "學校每年春天都會舉辦科學展覽。"
    ),
    "approach": (
        "We need a different approach to solve this complicated problem.",
        "我們需要用不同的方法來解決這個複雜的問題。"
    ),
    "assume": (
        "Do not assume that every source on the Internet is reliable.",
        "不要以為網路上的每個資訊來源都可靠。"
    ),
    "available": (
        "The new learning materials are available online for free.",
        "新的學習教材可以在網路上免費取得。"
    ),
    "benefit": (
        "Regular exercise can benefit both your body and your mind.",
        "規律運動對身體與心理都有好處。"
    ),
    "challenge": (
        "Learning to manage your time is a common challenge for high school students.",
        "學會管理時間，是高中生常見的挑戰。"
    ),
    "consequence": (
        "Every decision may have a consequence that we did not expect.",
        "每個決定都可能帶來我們沒有預料到的後果。"
    ),
    "consider": (
        "You should consider several factors before making a final decision.",
        "做最後決定前，你應該考慮幾項因素。"
    ),
    "contribute": (
        "Small daily habits can contribute to long-term success.",
        "每天的小習慣可以促成長期的成功。"
    ),
    "develop": (
        "Reading widely can help students develop stronger critical-thinking skills.",
        "廣泛閱讀能幫助學生培養更好的批判思考能力。"
    ),
    "environment": (
        "A quiet environment can make it easier to concentrate on studying.",
        "安靜的環境能讓人更容易專心讀書。"
    ),
    "evidence": (
        "The scientist collected more evidence before drawing a conclusion.",
        "科學家在下結論前蒐集了更多證據。"
    ),
    "factor": (
        "Cost is only one factor to consider when choosing a school.",
        "費用只是選擇學校時要考慮的其中一項因素。"
    ),
    "feature": (
        "One useful feature of the app is its offline study mode.",
        "這個應用程式的一項實用功能是離線學習模式。"
    ),
    "impact": (
        "Social media can have a strong impact on the way people communicate.",
        "社群媒體會對人們溝通的方式產生很大的影響。"
    ),
    "indicate": (
        "The results indicate that regular review improves long-term memory.",
        "結果顯示，規律複習能提升長期記憶。"
    ),
    "individual": (
        "Each individual may respond to the same situation differently.",
        "每個人面對相同情況時，反應可能都不一樣。"
    ),
    "involve": (
        "The project will involve students from several different classes.",
        "這項計畫將會有好幾個不同班級的學生參與。"
    ),
    "issue": (
        "The class discussed the issue from several different points of view.",
        "全班從幾個不同的角度討論這項議題。"
    ),
    "maintain": (
        "It is easier to maintain a study habit when your daily goal is realistic.",
        "每天的目標訂得實際，比較容易維持讀書習慣。"
    ),
    "occur": (
        "Most accidents occur when people stop paying attention to their surroundings.",
        "大多數意外都發生在人們不再注意周遭環境的時候。"
    ),
    "participate": (
        "Students are encouraged to participate actively in class discussions.",
        "老師鼓勵學生主動參與課堂討論。"
    ),
    "particularly": (
        "This chapter is particularly useful for students preparing for the exam.",
        "這一章對準備考試的學生特別有幫助。"
    ),
    "provide": (
        "The chart provides useful information about changes over time.",
        "這張圖表提供了有關長期變化的實用資訊。"
    ),
    "require": (
        "This task requires careful reading and logical thinking.",
        "這項任務需要仔細閱讀與邏輯思考。"
    ),
    "significant": (
        "There was a significant improvement in her reading speed after months of practice.",
        "經過幾個月的練習後，她的閱讀速度有了明顯進步。"
    ),
    "specific": (
        "Give a specific example to support your main idea.",
        "請舉一個具體的例子來支持你的主要想法。"
    ),
    "suggest": (
        "The data suggest that students learn better when they review regularly.",
        "資料顯示，學生規律複習時學習效果比較好。"
    ),
    "support": (
        "Use facts and examples to support your argument.",
        "請用事實與例子來支持你的論點。"
    ),
    "therefore": (
        "The road was closed; therefore, we had to take another route.",
        "道路封閉了，因此我們只好改走另一條路。"
    ),
    "various": (
        "The library offers various resources for students preparing for exams.",
        "圖書館提供各種資源給準備考試的學生。"
    ),
}

BANNED_SNIPPETS = (
    'In this passage, the word “',
    'The word “',
    "helps readers understand its meaning",
)

def load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback

def corpus_priorities():
    data = load_json(CORPUS, {})
    words = data.get("words", {})
    scores = {}
    for word, x in words.items():
        count = int(x.get("count", 0) or 0)
        years = int(x.get("yearCount", 0) or 0)
        by_year = x.get("byYear", {}) or {}
        recent = sum(int(by_year.get(str(y), 0) or 0) for y in range(111, 116))
        scores[word] = count + years * 4 + recent * 3
    return scores

def rebuild_examples():
    vocab = load_json(VOCAB, {})
    words = vocab.get("words", [])
    if len(words) < 6000:
        raise SystemExit("data/vocabulary-zh.json 尚未建置完成。")

    old = load_json(EXAMPLES, {}).get("words", {})
    rows = {}

    for item in words:
        word = item["word"]

        if word in MANUAL:
            en, zh = MANUAL[word]
            rows[word] = {
                "en": en,
                "zh": zh,
                "source": "manual",
                "status": "ready",
            }
            continue

        # 保留舊資料中真正人工校正、且沒有禁用假例句的項目。
        prev = old.get(word, {})
        prev_en = str(prev.get("en") or "").strip()
        prev_zh = str(prev.get("zh") or "").strip()
        is_good_manual = (
            prev.get("source") == "manual"
            and prev_en
            and prev_zh
            and word.lower() in prev_en.lower()
            and not any(s.lower() in prev_en.lower() for s in BANNED_SNIPPETS)
        )
        if is_good_manual:
            rows[word] = {
                "en": prev_en,
                "zh": prev_zh,
                "source": "manual",
                "status": "ready",
            }
        else:
            # 寧缺勿濫：不再自動放假例句。
            rows[word] = {
                "en": "",
                "zh": "",
                "source": "pending",
                "status": "needs_review",
            }

    payload = {
        "version": VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "policy": {
            "fakeFallbackDisabled": True,
            "pendingInsteadOfUnsafeExample": True,
            "manualExamplesAreOriginal": True,
        },
        "summary": {
            "words": len(rows),
            "ready": sum(x["status"] == "ready" for x in rows.values()),
            "pending": sum(x["status"] != "ready" for x in rows.values()),
        },
        "words": rows,
    }
    EXAMPLES.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

def rebuild_audit():
    vocab = load_json(VOCAB, {})
    examples = load_json(EXAMPLES, {}).get("words", {})
    priorities = corpus_priorities()
    issues = []

    bad_tokens = ("棻", "춣", "飻", "נ", "ם", "�", "fiea", "tumpike", "etemity", "amobiography")

    for item in vocab.get("words", []):
        word = item["word"]
        meaning = str(item.get("meaning") or "")
        score = priorities.get(word, 0)
        reasons = []

        if not meaning or meaning == "—":
            score += 1000
            reasons.append("missing_meaning")
        if any(t in meaning.lower() for t in bad_tokens):
            score += 900
            reasons.append("garbled_meaning")
        if len(meaning) > 120:
            score += 80
            reasons.append("meaning_too_long")
        if any(tag in meaning for tag in ("[醫]", "[經]", "[計]", "[化]", "[法]")):
            score += 60
            reasons.append("technical_dictionary_noise")

        ex = examples.get(word, {})
        if ex.get("status") != "ready":
            # 語料庫出現越多，例句校正優先度越高。
            score += 200 + priorities.get(word, 0) * 10
            reasons.append("example_needs_review")

        if reasons:
            issues.append({
                "word": word,
                "level": item.get("level"),
                "score": score,
                "corpusPriority": priorities.get(word, 0),
                "reasons": reasons,
                "meaning": meaning[:180],
            })

    issues.sort(
        key=lambda x: (
            -x["score"],
            -x["corpusPriority"],
            x["level"] or 9,
            x["word"],
        )
    )

    AUDIT.write_text(
        json.dumps({
            "version": VERSION,
            "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "summary": {
                "flagged": len(issues),
                "pendingExamples": sum("example_needs_review" in x["reasons"] for x in issues),
            },
            "issues": issues,
        }, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

def patch_app():
    text = APP.read_text(encoding="utf-8")

    text = re.sub(
        r"const EXAMPLES_URL='data/vocabulary-examples\.json\?v=[^']+';",
        "const EXAMPLES_URL='data/vocabulary-examples.json?v=1.4.6';",
        text,
        count=1,
    )

    # V1.4.6：EXAMPLES 裡有該字但 status=pending 時，不再回退到 genericExample。
    pattern = re.compile(
        r"function detailFor\(w\)\{const e=ENRICH\[w\.word\]\|\|\{\},a=WORD_DETAILS\[w\.word\]\|\|\{\};"
        r"const syn=.*?return \{example:.*?family:a\.family\|\|\[\]\}\}",
        re.S
    )
    replacement = (
        "function detailFor(w){"
        "const e=ENRICH[w.word]||{},a=WORD_DETAILS[w.word]||{},x=WORD_EXAMPLES[w.word]||{};"
        "const syn=(e.syn&&e.syn.length)?e.syn:(a.syn||[]),"
        "ant=(e.ant&&e.ant.length)?e.ant:(a.ant||[]),"
        "conf=(e.conf&&e.conf.length)?e.conf:confusables(w);"
        "const ready=!!e.ex||(x.status==='ready'&&!!x.en);"
        "return {"
        "example:e.ex||x.en||(x.status==='needs_review'?'例句待校正':genericExample(w)),"
        "exampleZh:e.ex?(x.zh||''):(x.zh||''),"
        "exampleSource:e.ex?'manual':(x.source||'fallback'),"
        "exampleReady:ready,"
        "collocations:(e.col&&e.col.length)?e.col:genericCollocations(w),"
        "root:e.root||a.structure||rootHint(w.word),syn,ant,conf,family:a.family||[]"
        "}}"
    )

    new_text, n = pattern.subn(replacement, text, count=1)
    if n != 1:
        # Already-patched V1.4.6 should simply be reusable.
        if "exampleReady:ready" not in text:
            raise SystemExit("找不到可安全更新的 detailFor()。")
        new_text = text

    text = new_text

    # 中文翻譯在待校正時隱藏。
    text = text.replace(
        "wz.classList.toggle('hidden',!state.settings.showExampleZh||!d.exampleZh)",
        "wz.classList.toggle('hidden',!state.settings.showExampleZh||!d.exampleZh||!d.exampleReady)"
    )
    text = text.replace(
        "dz.classList.toggle('hidden',!state.settings.showExampleZh||!d.exampleZh)",
        "dz.classList.toggle('hidden',!state.settings.showExampleZh||!d.exampleZh||!d.exampleReady)"
    )

    APP.write_text(text, encoding="utf-8")

def patch_index():
    text = INDEX.read_text(encoding="utf-8")
    text = re.sub(
        r"版本 V1\.4\.[0-9.]+ · [^<]*",
        "版本 V1.4.6 · 真實例句修正 + 例句中譯 + 101–115 學測語料庫",
        text,
        count=1,
    )
    INDEX.write_text(text, encoding="utf-8")

def patch_sw():
    text = SW.read_text(encoding="utf-8")
    text = re.sub(
        r"const CACHE='hs7000-v[^']+';",
        "const CACHE='hs7000-v1.4.6';",
        text,
        count=1,
    )
    SW.write_text(text, encoding="utf-8")

def validate():
    ex = load_json(EXAMPLES, {})
    words = ex.get("words", {})

    assert ex.get("version") == VERSION
    assert len(words) >= 6000

    # 真例句回歸測試
    for word in ("absence", "abbreviate", "abolish", "accuse"):
        x = words[word]
        assert x["status"] == "ready", word
        assert word.lower() in x["en"].lower(), (word, x["en"])
        assert x["zh"], word
        assert not any(s.lower() in x["en"].lower() for s in BANNED_SNIPPETS), word

    # 任一 pending 字不可再有假 fallback。
    for word, x in words.items():
        if x["status"] != "ready":
            assert x["en"] == "", word
            assert x["zh"] == "", word

    app = APP.read_text(encoding="utf-8")
    idx = INDEX.read_text(encoding="utf-8")
    sw = SW.read_text(encoding="utf-8")

    assert "vocabulary-examples.json?v=1.4.6" in app
    assert "例句待校正" in app
    assert "exampleReady:ready" in app
    assert "V1.4.6" in idx
    assert "hs7000-v1.4.6" in sw

    # 禁止舊假例句出現在輸出的例句資料。
    raw = EXAMPLES.read_text(encoding="utf-8")
    assert "In this passage, the word" not in raw
    assert "helps readers understand its meaning" not in raw

    print("V1.4.6 validation passed")
    print(ex["summary"])
    print("absence:", words["absence"])
    print("abbreviate:", words["abbreviate"])

def main():
    for p in (APP, INDEX, SW, VOCAB):
        if not p.exists():
            raise SystemExit(f"缺少必要檔案：{p}")

    rebuild_examples()
    rebuild_audit()
    patch_app()
    patch_index()
    patch_sw()
    validate()

if __name__ == "__main__":
    main()
