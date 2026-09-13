#!/usr/bin/env python3
"""
Stable Vocabulary Updater (current payload: V1.4.5.1):
1) Make the V1.4.5 upgrade idempotent.
2) Replace unsafe/generated grammatical templates with conservative fallback examples.
3) Preserve hand-checked bilingual examples.
4) Rebuild quality audit.
"""

from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path

APP=Path("app.js")
INDEX=Path("index.html")
SW=Path("sw.js")
VOCAB=Path("data/vocabulary-zh.json")
EXAMPLES=Path("data/vocabulary-examples.json")
AUDIT=Path("data/vocabulary-quality-audit.json")

MANUAL={
"absence":("The absence of clear instructions caused unnecessary confusion.","缺乏清楚的指示，造成了不必要的混亂。"),
"ability":("She has the ability to explain difficult ideas clearly.","她有能力把困難的概念解釋得很清楚。"),
"abandon":("The hikers had to abandon their plan because of the sudden storm.","登山客因為突如其來的暴風雨，只好放棄原本的計畫。"),
"accept":("Learning to accept different opinions is an important part of teamwork.","學會接受不同的意見，是團隊合作中很重要的一部分。"),
"achieve":("With steady practice, you can achieve your academic goals.","只要持續練習，你就能達成學業上的目標。"),
"academic":("The school provides extra academic support before major exams.","學校會在大型考試前提供額外的學業輔導。"),
"acknowledge":("The writer acknowledged that the first explanation was incomplete.","作者承認第一個解釋並不完整。"),
"accurate":("Accurate information is essential when you write a research report.","撰寫研究報告時，準確的資訊非常重要。"),
"adjust":("It may take a few weeks to adjust to a new study schedule.","適應新的讀書作息可能需要幾個星期。"),
"affect":("Lack of sleep can affect your concentration in class.","睡眠不足會影響你在課堂上的專注力。"),
"analyze":("Students were asked to analyze the causes of the problem.","學生被要求分析這個問題發生的原因。"),
"annual":("The school holds an annual science fair every spring.","學校每年春天都會舉辦科學展覽。"),
"approach":("We need a different approach to solve this complicated problem.","我們需要用不同的方法來解決這個複雜的問題。"),
"assume":("Do not assume that every source on the Internet is reliable.","不要以為網路上的每個資訊來源都可靠。"),
"available":("The new learning materials are available online for free.","新的學習教材可以在網路上免費取得。"),
"benefit":("Regular exercise can benefit both your body and your mind.","規律運動對身體與心理都有好處。"),
"challenge":("Learning to manage your time is a common challenge for high school students.","學會管理時間，是高中生常見的挑戰。"),
"consequence":("Every decision may have a consequence that we did not expect.","每個決定都可能帶來我們沒有預料到的後果。"),
"consider":("You should consider several factors before making a final decision.","做最後決定前，你應該考慮幾項因素。"),
"contribute":("Small daily habits can contribute to long-term success.","每天的小習慣可以促成長期的成功。"),
"develop":("Reading widely can help students develop stronger critical-thinking skills.","廣泛閱讀能幫助學生培養更好的批判思考能力。"),
"environment":("A quiet environment can make it easier to concentrate on studying.","安靜的環境能讓人更容易專心讀書。"),
"evidence":("The scientist collected more evidence before drawing a conclusion.","科學家在下結論前蒐集了更多證據。"),
"factor":("Cost is only one factor to consider when choosing a school.","費用只是選擇學校時要考慮的其中一項因素。"),
"feature":("One useful feature of the app is its offline study mode.","這個應用程式的一項實用功能是離線學習模式。"),
"impact":("Social media can have a strong impact on the way people communicate.","社群媒體會對人們溝通的方式產生很大的影響。"),
"indicate":("The results indicate that regular review improves long-term memory.","結果顯示，規律複習能提升長期記憶。"),
"individual":("Each individual may respond to the same situation differently.","每個人面對相同情況時，反應可能都不一樣。"),
"involve":("The project will involve students from several different classes.","這項計畫將會有好幾個不同班級的學生參與。"),
"issue":("The class discussed the issue from several different points of view.","全班從幾個不同的角度討論這項議題。"),
"maintain":("It is easier to maintain a study habit when your daily goal is realistic.","每天的目標訂得實際，比較容易維持讀書習慣。"),
"occur":("Most accidents occur when people stop paying attention to their surroundings.","大多數意外都發生在人們不再注意周遭環境的時候。"),
"participate":("Students are encouraged to participate actively in class discussions.","老師鼓勵學生主動參與課堂討論。"),
"particularly":("This chapter is particularly useful for students preparing for the exam.","這一章對準備考試的學生特別有幫助。"),
"provide":("The chart provides useful information about changes over time.","這張圖表提供了有關長期變化的實用資訊。"),
"require":("This task requires careful reading and logical thinking.","這項任務需要仔細閱讀與邏輯思考。"),
"significant":("There was a significant improvement in her reading speed after months of practice.","經過幾個月的練習後，她的閱讀速度有了明顯進步。"),
"specific":("Give a specific example to support your main idea.","請舉一個具體的例子來支持你的主要想法。"),
"suggest":("The data suggest that students learn better when they review regularly.","資料顯示，學生規律複習時學習效果比較好。"),
"support":("Use facts and examples to support your argument.","請用事實與例子來支持你的論點。"),
"therefore":("The road was closed; therefore, we had to take another route.","道路封閉了，因此我們只好改走另一條路。"),
"various":("The library offers various resources for students preparing for exams.","圖書館提供各種資源給準備考試的學生。"),
}

def short_meaning(s):
    s=str(s or "").strip().replace("\\r","；").replace("\\n","；")
    s=re.sub(r"\[[^\]]+\]","",s)
    s=re.sub(r"\b(?:n|v|vt|vi|a|adj|adv|prep|conj|pron)\.\s*","",s,flags=re.I)
    # Avoid using visibly corrupted meanings in fallback lines.
    if any(x in s for x in ("棻","춣","飻","נ","ם","�")):
        return "此單字"
    for sep in ("；",";",",","，"):
        if sep in s:
            s=s.split(sep)[0]
    s=s.strip(" .；，,")
    return s[:36] if s else "此單字"

def safe_fallback(word, meaning):
    """
    Intentionally conservative. It avoids inserting a word into a grammatical slot
    that may not fit its POS/sense. These are clearly marked as fallback examples
    for later human-quality review.
    """
    m=short_meaning(meaning)
    en=f'In this passage, the word “{word}” is used in a context that helps readers understand its meaning.'
    zh=f'在這段文章中，「{word}」出現在有助於讀者理解「{m}」這個意思的上下文裡。'
    return en, zh

def rebuild_examples():
    vocab=json.loads(VOCAB.read_text(encoding="utf-8"))
    rows={}
    for x in vocab["words"]:
        w=x["word"]
        if w in MANUAL:
            en,zh=MANUAL[w]
            src="manual"
        else:
            en,zh=safe_fallback(w,x.get("meaning"))
            src="fallback"
        rows[w]={"en":en,"zh":zh,"source":src}

    payload={
        "version":"1.4.5.1",
        "generatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "summary":{
            "words":len(rows),
            "manual":sum(v["source"]=="manual" for v in rows.values()),
            "fallback":sum(v["source"]=="fallback" for v in rows.values()),
        },
        "words":rows,
    }
    EXAMPLES.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")

def rebuild_audit():
    vocab=json.loads(VOCAB.read_text(encoding="utf-8"))
    ex=json.loads(EXAMPLES.read_text(encoding="utf-8"))["words"]
    issues=[]
    bad_tokens=("棻","춣","飻","נ","ם","�","fiea","tumpike","etemity","amobiography")
    for x in vocab["words"]:
        w=x["word"]; m=str(x.get("meaning") or "")
        score=0; reasons=[]
        if not m or m=="—":
            score+=100; reasons.append("missing_meaning")
        if any(t in m.lower() for t in bad_tokens):
            score+=90; reasons.append("garbled_meaning")
        if len(m)>120:
            score+=20; reasons.append("meaning_too_long")
        if any(tag in m for tag in ("[醫]","[經]","[計]","[化]","[法]")):
            score+=15; reasons.append("technical_dictionary_noise")
        if ex.get(w,{}).get("source")=="fallback":
            score+=10; reasons.append("fallback_example_needs_human_review")
        if score:
            issues.append({"word":w,"level":x.get("level"),"score":score,"reasons":reasons,"meaning":m[:180]})
    issues.sort(key=lambda z:(-z["score"],z["level"] or 9,z["word"]))
    AUDIT.write_text(json.dumps({
        "version":"1.4.5.1",
        "generatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "summary":{"flagged":len(issues),"highPriority":sum(x["score"]>=60 for x in issues)},
        "issues":issues,
    },ensure_ascii=False,separators=(",",":")),encoding="utf-8")

def ensure_frontend():
    app=APP.read_text(encoding="utf-8")
    idx=INDEX.read_text(encoding="utf-8")
    sw=SW.read_text(encoding="utf-8")

    # Already-upgraded repos should pass without requiring the old V1.4.4 shape.
    if "const EXAMPLES_URL=" not in app:
        marker="const DETAILS_URL="
        m=re.search(r"const DETAILS_URL=.*?;\n",app)
        if not m: raise SystemExit("找不到 DETAILS_URL")
        app=app[:m.end()]+"const EXAMPLES_URL='data/vocabulary-examples.json?v=1.4.5.1';\n"+app[m.end():]
    else:
        app=re.sub(r"const EXAMPLES_URL=.*?;","const EXAMPLES_URL='data/vocabulary-examples.json?v=1.4.5.1';",app,count=1)

    if "let WORD_EXAMPLES=" not in app:
        app=app.replace("let WORD_DETAILS={};","let WORD_DETAILS={};\nlet WORD_EXAMPLES={};",1)

    if "async function loadWordExamples()" not in app:
        marker="async function loadWordDetails()"
        i=app.find(marker)
        if i<0: raise SystemExit("找不到 loadWordDetails()")
        loader="async function loadWordExamples(){try{const r=await fetch(EXAMPLES_URL,{cache:'no-store'});if(!r.ok)throw new Error('examples '+r.status);const x=await r.json();WORD_EXAMPLES=x.words||{};if(bank.length)renderAll();}catch(e){console.warn('word examples unavailable',e)}}\n"
        app=app[:i]+loader+app[i:]

    # Only patch detailFor when examples are not already connected.
    if "const x=WORD_EXAMPLES[w.word]||{}" not in app:
        pat=r"function detailFor\(w\)\{const e=ENRICH\[w\.word\]\|\|\{\},a=WORD_DETAILS\[w\.word\]\|\|\{\};const syn=.*?\}\}"
        repl="function detailFor(w){const e=ENRICH[w.word]||{},a=WORD_DETAILS[w.word]||{};const syn=(e.syn&&e.syn.length)?e.syn:(a.syn||[]),ant=(e.ant&&e.ant.length)?e.ant:(a.ant||[]),conf=(e.conf&&e.conf.length)?e.conf:confusables(w);const x=WORD_EXAMPLES[w.word]||{};return {example:e.ex||x.en||genericExample(w),exampleZh:x.zh||'',exampleSource:e.ex?'manual':(x.source||'fallback'),collocations:(e.col&&e.col.length)?e.col:genericCollocations(w),root:e.root||a.structure||rootHint(w.word),syn,ant,conf,family:a.family||[]}}"
        app,n=re.subn(pat,repl,app,count=1)
        if n!=1: raise SystemExit("找不到可安全升級的 detailFor()")

    if "loadWordExamples();" not in app:
        app=app.replace("bind();loadCorpusData();loadWordDetails();loadBank();",
                        "bind();loadCorpusData();loadWordExamples();loadWordDetails();loadBank();",1)

    # Ensure translation UI exists.
    if 'id="wordExampleZh"' not in idx:
        idx=idx.replace('<div class="example" id="wordExample">—</div></div>',
                        '<div class="example" id="wordExample">—</div><div class="example-zh" id="wordExampleZh">—</div></div>')
    if 'id="detailExampleZh"' not in idx:
        idx=idx.replace('<p id="detailExample">—</p>',
                        '<p id="detailExample">—</p><p class="example-zh" id="detailExampleZh">—</p>',1)
    if 'id="showExampleZh"' not in idx:
        marker='<label class="toggle"><input type="checkbox" id="autoSpeak" checked />顯示單字時自動發音</label>'
        idx=idx.replace(marker,marker+'\n      <label class="toggle"><input type="checkbox" id="showExampleZh" checked />顯示例句中文翻譯</label>')

    idx=re.sub(r"版本 V1\.4\.[0-9.]+ · [^<]*",
               "版本 V1.4.5.1 · 例句中譯品質修正 + 101–115 學測語料庫",idx,count=1)

    sw=re.sub(r"const CACHE='hs7000-v[^']+';","const CACHE='hs7000-v1.4.5.1';",sw,count=1)
    if "./data/vocabulary-examples.json" not in sw:
        sw=sw.replace("'./data/vocabulary-details.json'",
                      "'./data/vocabulary-details.json','./data/vocabulary-examples.json'",1)

    APP.write_text(app,encoding="utf-8")
    INDEX.write_text(idx,encoding="utf-8")
    SW.write_text(sw,encoding="utf-8")

def validate():
    ex=json.loads(EXAMPLES.read_text(encoding="utf-8"))
    assert ex["version"]=="1.4.5.1"
    assert len(ex["words"])>=6000
    assert ex["words"]["absence"]["source"]=="manual"
    assert "缺乏" in ex["words"]["absence"]["zh"]
    # Regression: known bad generated sentence must be gone.
    assert "A small change can abbreviate" not in ex["words"]["abbreviate"]["en"]
    assert ex["words"]["abbreviate"]["source"]=="fallback"

    app=APP.read_text(encoding="utf-8")
    idx=INDEX.read_text(encoding="utf-8")
    sw=SW.read_text(encoding="utf-8")
    assert "vocabulary-examples.json?v=1.4.5.1" in app
    assert "wordExampleZh" in idx and "detailExampleZh" in idx
    assert "hs7000-v1.4.5.1" in sw
    print("V1.4.5.1 validation passed")
    print(ex["summary"])
    print("absence:",ex["words"]["absence"])
    print("abbreviate fallback:",ex["words"]["abbreviate"])

def main():
    for p in (APP,INDEX,SW,VOCAB):
        if not p.exists(): raise SystemExit(f"缺少必要檔案：{p}")
    rebuild_examples()
    rebuild_audit()
    ensure_frontend()
    validate()

if __name__=="__main__":
    main()
