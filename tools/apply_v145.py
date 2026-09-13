#!/usr/bin/env python3
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
from nltk.corpus import wordnet as wn

APP=Path('app.js'); INDEX=Path('index.html'); CSS=Path('styles.css'); SW=Path('sw.js')
VOCAB=Path('data/vocabulary-zh.json'); EXAMPLES=Path('data/vocabulary-examples.json'); AUDIT=Path('data/vocabulary-quality-audit.json')

MANUAL={
'absence':('The absence of clear instructions caused unnecessary confusion.','缺乏清楚的指示，造成了不必要的混亂。'),
'ability':('She has the ability to explain difficult ideas clearly.','她有能力把困難的概念解釋得很清楚。'),
'abandon':('The hikers had to abandon their plan because of the sudden storm.','登山客因為突如其來的暴風雨，只好放棄原本的計畫。'),
'accept':('Learning to accept different opinions is an important part of teamwork.','學會接受不同的意見，是團隊合作中很重要的一部分。'),
'achieve':('With steady practice, you can achieve your academic goals.','只要持續練習，你就能達成學業上的目標。'),
'academic':('The school provides extra academic support before major exams.','學校會在大型考試前提供額外的學業輔導。'),
'acknowledge':('The writer acknowledged that the first explanation was incomplete.','作者承認第一個解釋並不完整。'),
'accurate':('Accurate information is essential when you write a research report.','撰寫研究報告時，準確的資訊非常重要。'),
'adjust':('It may take a few weeks to adjust to a new study schedule.','適應新的讀書作息可能需要幾個星期。'),
'affect':('Lack of sleep can affect your concentration in class.','睡眠不足會影響你在課堂上的專注力。'),
'analyze':('Students were asked to analyze the causes of the problem.','學生被要求分析這個問題發生的原因。'),
'annual':('The school holds an annual science fair every spring.','學校每年春天都會舉辦科學展覽。'),
'approach':('We need a different approach to solve this complicated problem.','我們需要用不同的方法來解決這個複雜的問題。'),
'assume':('Do not assume that every source on the Internet is reliable.','不要以為網路上的每個資訊來源都可靠。'),
'available':('The new learning materials are available online for free.','新的學習教材可以在網路上免費取得。'),
'benefit':('Regular exercise can benefit both your body and your mind.','規律運動對身體與心理都有好處。'),
'challenge':('Learning to manage your time is a common challenge for high school students.','學會管理時間，是高中生常見的挑戰。'),
'consider':('You should consider several factors before making a final decision.','做最後決定前，你應該考慮幾項因素。'),
'contribute':('Small daily habits can contribute to long-term success.','每天的小習慣可以促成長期的成功。'),
'develop':('Reading widely can help students develop stronger critical-thinking skills.','廣泛閱讀能幫助學生培養更好的批判思考能力。'),
'environment':('A quiet environment can make it easier to concentrate on studying.','安靜的環境能讓人更容易專心讀書。'),
'evidence':('The scientist collected more evidence before drawing a conclusion.','科學家在下結論前蒐集了更多證據。'),
'factor':('Cost is only one factor to consider when choosing a school.','費用只是選擇學校時要考慮的其中一項因素。'),
'impact':('Social media can have a strong impact on the way people communicate.','社群媒體會對人們溝通的方式產生很大的影響。'),
'indicate':('The results indicate that regular review improves long-term memory.','結果顯示，規律複習能提升長期記憶。'),
'involve':('The project will involve students from several different classes.','這項計畫將會有好幾個不同班級的學生參與。'),
'maintain':('It is easier to maintain a study habit when your daily goal is realistic.','每天的目標訂得實際，比較容易維持讀書習慣。'),
'occur':('Most accidents occur when people stop paying attention to their surroundings.','大多數意外都發生在人們不再注意周遭環境的時候。'),
'participate':('Students are encouraged to participate actively in class discussions.','老師鼓勵學生主動參與課堂討論。'),
'provide':('The chart provides useful information about changes over time.','這張圖表提供了有關長期變化的實用資訊。'),
'require':('This task requires careful reading and logical thinking.','這項任務需要仔細閱讀與邏輯思考。'),
'significant':('There was a significant improvement in her reading speed after months of practice.','經過幾個月的練習後，她的閱讀速度有了明顯進步。'),
'specific':('Give a specific example to support your main idea.','請舉一個具體的例子來支持你的主要想法。'),
'suggest':('The data suggest that students learn better when they review regularly.','資料顯示，學生規律複習時學習效果比較好。'),
'support':('Use facts and examples to support your argument.','請用事實與例子來支持你的論點。'),
'various':('The library offers various resources for students preparing for exams.','圖書館提供各種資源給準備考試的學生。')}

def short_meaning(s):
    s=str(s or '').replace('\\r','；').replace('\\n','；').strip()
    s=re.sub(r'\[[^\]]+\]','',s)
    s=re.sub(r'\b(?:n|v|vt|vi|a|adj|adv|prep|conj|pron)\.\s*','',s,flags=re.I)
    return re.split(r'[；;,，]',s)[0].strip(' .；，,') or '這個概念'

def lexname(w):
    ss=wn.synsets(w)
    return ss[0].lexname() if ss else ''

def make_example(x):
    w=x['word']
    if w in MANUAL: return (*MANUAL[w],'manual')
    pos=(x.get('pos') or [''])[0]; m=short_meaning(x.get('meaning')); lx=lexname(w)
    if pos.startswith('v'):
        if lx in ('verb.communication','verb.cognition'):
            return f'Students should {w} their ideas carefully before reaching a conclusion.',f'學生在下結論前，應該仔細地{m}自己的想法。','template'
        if lx in ('verb.change','verb.creation'):
            return f'A small change can {w} the final result in an unexpected way.',f'一個小小的改變，可能會以意想不到的方式{m}最後的結果。','template'
        return f'Learning when and how to {w} is important in real-life situations.',f'在真實情境中，學會何時以及如何{m}很重要。','template'
    if pos.startswith('adj'):
        return f'The situation seemed {w} at first, but it became clearer after discussion.',f'這個情況起初看起來很{m}，但討論之後就變得更清楚了。','template'
    if pos.startswith('adv'):
        return f'The speaker explained the main point {w} so that the audience could understand it.',f'講者{m}地說明重點，讓聽眾能夠理解。','template'
    if pos.startswith('n'):
        if lx=='noun.person': return f'The {w} played an important role in solving the problem.',f'這位{m}在解決問題的過程中扮演了重要角色。','template'
        if lx in ('noun.state','noun.attribute','noun.feeling'): return f'The {w} became more noticeable as the situation continued to change.',f'隨著情況持續變化，這種{m}變得更加明顯。','template'
        return f'The article explains why {w} is important in this situation.',f'這篇文章說明了為什麼{m}在這個情況中很重要。','template'
    return f'The word “{w}” appears in a context that helps readers understand its meaning.',f'「{w}」出現在有助於讀者理解其意思的上下文中。','template'

def build_examples(vocab):
    rows={}
    for x in vocab['words']:
        en,zh,src=make_example(x); rows[x['word']]={'en':en,'zh':zh,'source':src}
    payload={'version':'1.4.5','generatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'summary':{'words':len(rows),'manual':sum(v['source']=='manual' for v in rows.values()),'template':sum(v['source']=='template' for v in rows.values())},'words':rows}
    EXAMPLES.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    return payload

def build_audit(vocab,examples):
    issues=[]; suspicious=('棻','飻','נ','춣','ם','fiea','tumpike','etemity','amobiography')
    for x in vocab['words']:
        w=x['word']; m=str(x.get('meaning') or ''); score=0; reasons=[]
        if not m or m=='—': score+=100; reasons.append('missing_meaning')
        if any(t in m.lower() for t in suspicious): score+=80; reasons.append('garbled_meaning')
        if len(m)>120: score+=20; reasons.append('meaning_too_long')
        if any(t in m for t in ('[醫]','[經]','[計]','[化]')): score+=15; reasons.append('technical_dictionary_noise')
        if examples['words'][w]['source']=='template': score+=10; reasons.append('template_example')
        if score: issues.append({'word':w,'level':x.get('level'),'score':score,'reasons':reasons,'meaning':m[:180]})
    issues.sort(key=lambda z:(-z['score'],z['level'] or 9,z['word']))
    payload={'version':'1.4.5','generatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'summary':{'flagged':len(issues),'highPriority':sum(x['score']>=60 for x in issues)},'issues':issues}
    AUDIT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

def patch_app():
    t=APP.read_text(encoding='utf-8')
    t=t.replace("const DETAILS_URL='data/vocabulary-details.json?v=1.4.4';","const DETAILS_URL='data/vocabulary-details.json?v=1.4.5';\nconst EXAMPLES_URL='data/vocabulary-examples.json?v=1.4.5';")
    if 'let WORD_EXAMPLES=' not in t: t=t.replace('let WORD_DETAILS={};','let WORD_DETAILS={};\nlet WORD_EXAMPLES={};')
    t=t.replace("mode:'7000',autoSpeak:true}","mode:'7000',autoSpeak:true,showExampleZh:true}")
    old="return {example:e.ex||genericExample(w),collocations:(e.col&&e.col.length)?e.col:genericCollocations(w),root:e.root||a.structure||rootHint(w.word),syn,ant,conf,family:a.family||[]}"
    new="const x=WORD_EXAMPLES[w.word]||{};return {example:e.ex||x.en||genericExample(w),exampleZh:x.zh||'',exampleSource:e.ex?'manual':(x.source||'fallback'),collocations:(e.col&&e.col.length)?e.col:genericCollocations(w),root:e.root||a.structure||rootHint(w.word),syn,ant,conf,family:a.family||[]}"
    if old not in t: raise SystemExit('找不到 V1.4.4 detailFor')
    t=t.replace(old,new,1)
    if 'async function loadWordExamples()' not in t:
        loader="async function loadWordExamples(){try{const r=await fetch(EXAMPLES_URL,{cache:'no-store'});if(!r.ok)throw new Error('examples '+r.status);const x=await r.json();WORD_EXAMPLES=x.words||{};console.info('V1.4.5 examples loaded',Object.keys(WORD_EXAMPLES).length);if(bank.length)renderAll();}catch(e){console.warn('word examples unavailable',e)}}\n"
        t=t.replace('async function loadWordDetails()',loader+'async function loadWordDetails()',1)
    t=t.replace("document.getElementById('wordExample').textContent=d.example;","document.getElementById('wordExample').textContent=d.example;const wz=document.getElementById('wordExampleZh');if(wz){wz.textContent=d.exampleZh||'';wz.classList.toggle('hidden',!state.settings.showExampleZh||!d.exampleZh)};")
    t=t.replace("document.getElementById('detailExample').textContent=d.example;","document.getElementById('detailExample').textContent=d.example;const dz=document.getElementById('detailExampleZh');if(dz){dz.textContent=d.exampleZh||'';dz.classList.toggle('hidden',!state.settings.showExampleZh||!d.exampleZh)};")
    t=t.replace("document.getElementById('autoSpeak').checked=state.settings.autoSpeak","document.getElementById('autoSpeak').checked=state.settings.autoSpeak;const ez=document.getElementById('showExampleZh');if(ez)ez.checked=state.settings.showExampleZh!==false")
    t=t.replace("state.settings.autoSpeak=document.getElementById('autoSpeak').checked;saveState();renderAll()","state.settings.autoSpeak=document.getElementById('autoSpeak').checked;const ez=document.getElementById('showExampleZh');state.settings.showExampleZh=ez?ez.checked:true;saveState();renderAll()")
    t=t.replace('bind();loadCorpusData();loadWordDetails();loadBank();','bind();loadCorpusData();loadWordExamples();loadWordDetails();loadBank();')
    APP.write_text(t,encoding='utf-8')

def patch_index():
    t=INDEX.read_text(encoding='utf-8')
    t=t.replace('<div class="example" id="wordExample">—</div></div>','<div class="example" id="wordExample">—</div><div class="example-zh" id="wordExampleZh">—</div></div>')
    t=t.replace('<section class="detail-section"><h3>高中程度例句</h3><p id="detailExample">—</p><button class="text-btn" id="detailExampleSpeak">','<section class="detail-section"><h3>高中程度例句</h3><p id="detailExample">—</p><p class="example-zh" id="detailExampleZh">—</p><button class="text-btn" id="detailExampleSpeak">')
    marker='<label class="toggle"><input type="checkbox" id="autoSpeak" checked />顯示單字時自動發音</label>'
    if marker in t and 'id="showExampleZh"' not in t: t=t.replace(marker,marker+'\n      <label class="toggle"><input type="checkbox" id="showExampleZh" checked />顯示例句中文翻譯</label>')
    t=re.sub(r'版本 V1\.4\.[0-9.]+ · [^<]*','版本 V1.4.5 · 例句中譯 + 例句品質提升 + 101–115 學測語料庫',t,count=1)
    INDEX.write_text(t,encoding='utf-8')

def patch_css():
    t=CSS.read_text(encoding='utf-8')
    if '.example-zh{' not in t: t+='\n/* ===== V1.4.5 例句中譯 ===== */\n.example-zh{margin-top:10px;color:#71869a;font-size:.94rem;line-height:1.65;font-weight:500}.detail-section .example-zh{margin-top:8px;padding-top:8px;border-top:1px dashed #dbe5ee}.example-zh.hidden{display:none}\n'
    CSS.write_text(t,encoding='utf-8')

def patch_sw():
    t=SW.read_text(encoding='utf-8'); t=re.sub(r"const CACHE='hs7000-v[^']+';","const CACHE='hs7000-v1.4.5';",t,count=1)
    if './data/vocabulary-examples.json' not in t: t=t.replace("'./data/vocabulary-details.json'","'./data/vocabulary-details.json','./data/vocabulary-examples.json'")
    SW.write_text(t,encoding='utf-8')

def main():
    for p in (APP,INDEX,CSS,SW,VOCAB):
        if not p.exists(): raise SystemExit(f'缺少必要檔案：{p}')
    vocab=json.loads(VOCAB.read_text(encoding='utf-8')); examples=build_examples(vocab); build_audit(vocab,examples)
    patch_app(); patch_index(); patch_css(); patch_sw()
    a=APP.read_text(encoding='utf-8'); h=INDEX.read_text(encoding='utf-8'); s=SW.read_text(encoding='utf-8')
    assert examples['version']=='1.4.5' and len(examples['words'])>=6000
    assert examples['words']['absence']['source']=='manual' and '缺乏' in examples['words']['absence']['zh']
    assert 'wordExampleZh' in h and 'detailExampleZh' in h and 'showExampleZh' in h
    assert 'loadWordExamples()' in a and 'hs7000-v1.4.5' in s
    print('V1.4.5 validation passed'); print('absence:',examples['words']['absence']); print('audit:',json.loads(AUDIT.read_text(encoding='utf-8'))['summary'])
if __name__=='__main__': main()
