#!/usr/bin/env python3
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path

VERSION='1.4.7'
APP=Path('app.js'); INDEX=Path('index.html'); SW=Path('sw.js')
VOCAB=Path('data/vocabulary-zh.json'); EXAMPLES=Path('data/vocabulary-examples.json')
AUDIT=Path('data/vocabulary-quality-audit.json'); CORPUS=Path('data/gsat-corpus-stats.json')
BANNED=('In this passage, the word “','The word “','helps readers understand its meaning')

NEW_BATCH={
'information':('The website provides useful information about scholarships and application deadlines.','這個網站提供有關獎學金與申請截止日期的實用資訊。'),
'research':('The students conducted research on how sleep affects learning and memory.','學生研究睡眠如何影響學習與記憶。'),
'technology':('New technology has changed the way people communicate across long distances.','新科技已改變人們進行遠距溝通的方式。'),
'decision':('She considered several options carefully before making her final decision.','她在做最後決定前仔細考慮了幾個選項。'),
'community':('Local volunteers worked together to improve the safety of their community.','當地志工共同合作，改善社區的安全。'),
'experience':('Working on the project gave him valuable experience in solving real problems.','參與這項計畫讓他獲得解決真實問題的寶貴經驗。'),
'develop':('Reading widely can help students develop stronger critical-thinking skills.','廣泛閱讀能幫助學生培養更好的批判思考能力。'),
'environment':('A quiet environment can make it easier to concentrate on studying.','安靜的環境能讓人更容易專心讀書。'),
'evidence':('The scientist collected more evidence before drawing a conclusion.','科學家在下結論前蒐集了更多證據。'),
'factor':('Cost is only one factor to consider when choosing a school.','費用只是選擇學校時要考慮的其中一項因素。'),
'feature':('One useful feature of the app is its offline study mode.','這個應用程式的一項實用功能是離線學習模式。'),
'impact':('Social media can have a strong impact on the way people communicate.','社群媒體會對人們溝通的方式產生很大的影響。'),
'indicate':('The results indicate that regular review improves long-term memory.','結果顯示，規律複習能提升長期記憶。'),
'individual':('Each individual may respond to the same situation differently.','每個人面對相同情況時，反應可能都不一樣。'),
'involve':('The project will involve students from several different classes.','這項計畫將會有好幾個不同班級的學生參與。'),
'issue':('The class discussed the issue from several different points of view.','全班從幾個不同的角度討論這項議題。'),
'maintain':('It is easier to maintain a study habit when your daily goal is realistic.','每天的目標訂得實際，比較容易維持讀書習慣。'),
'occur':('Most accidents occur when people stop paying attention to their surroundings.','大多數意外都發生在人們不再注意周遭環境的時候。'),
'participate':('Students are encouraged to participate actively in class discussions.','老師鼓勵學生主動參與課堂討論。'),
'provide':('The chart provides useful information about changes over time.','這張圖表提供了有關長期變化的實用資訊。'),
'require':('This task requires careful reading and logical thinking.','這項任務需要仔細閱讀與邏輯思考。'),
'significant':('There was a significant improvement in her reading speed after months of practice.','經過幾個月的練習後，她的閱讀速度有了明顯進步。'),
'specific':('Give a specific example to support your main idea.','請舉一個具體的例子來支持你的主要想法。'),
'suggest':('The data suggest that students learn better when they review regularly.','資料顯示，學生規律複習時學習效果比較好。'),
'support':('Use facts and examples to support your argument.','請用事實與例子來支持你的論點。'),
'various':('The library offers various resources for students preparing for exams.','圖書館提供各種資源給準備考試的學生。'),
'affect':('Lack of sleep can affect your concentration in class.','睡眠不足會影響你在課堂上的專注力。'),
'approach':('We need a different approach to solve this complicated problem.','我們需要用不同的方法來解決這個複雜的問題。'),
'assume':('Do not assume that every source on the Internet is reliable.','不要以為網路上的每個資訊來源都可靠。'),
'available':('The new learning materials are available online for free.','新的學習教材可以在網路上免費取得。'),
'benefit':('Regular exercise can benefit both your body and your mind.','規律運動對身體與心理都有好處。'),
'challenge':('Learning to manage your time is a common challenge for high school students.','學會管理時間，是高中生常見的挑戰。'),
'consequence':('Every decision may have a consequence that we did not expect.','每個決定都可能帶來我們沒有預料到的後果。'),
'consider':('You should consider several factors before making a final decision.','做最後決定前，你應該考慮幾項因素。'),
'contribute':('Small daily habits can contribute to long-term success.','每天的小習慣可以促成長期的成功。'),
'analyze':('Students were asked to analyze the causes of the problem.','學生被要求分析這個問題發生的原因。'),
'method':('The teacher introduced a simple method for remembering difficult vocabulary.','老師介紹了一個記住困難單字的簡單方法。'),
'process':('Learning a language is a gradual process that requires regular practice.','學習語言是一個需要規律練習的漸進過程。'),
'result':('The experiment produced a surprising result that no one had expected.','這項實驗產生了沒有人預料到的驚人結果。'),
'reason':('There is a good reason to check the source before sharing information online.','在網路上分享資訊前先確認來源是有充分理由的。'),
'relationship':('Trust plays an important role in building a healthy relationship.','信任在建立健康關係中扮演重要角色。'),
'responsibility':('Students should take responsibility for completing their work on time.','學生應對按時完成自己的作業負責。'),
'resource':('The school website offers many useful resources for exam preparation.','學校網站提供許多準備考試的實用資源。'),
'response':('Her response showed that she had understood the main point of the question.','她的回答顯示她已理解題目的重點。'),
'section':('Read the final section of the article before answering the questions.','回答問題前請先閱讀文章的最後一節。'),
'similar':('The two solutions look similar, but they work in very different ways.','這兩個解決方法看起來相似，但運作方式非常不同。'),
'situation':('In an emergency situation, staying calm can help you make better decisions.','在緊急情況下保持冷靜，能幫助你做出更好的決定。'),
'source':('Always check whether the source of online information is reliable.','務必確認網路資訊的來源是否可靠。'),
'standard':('The new safety standard requires all buildings to have clear emergency exits.','新的安全標準要求所有建築物都有清楚的緊急出口。'),
'structure':('The structure of the essay makes its main argument easy to follow.','這篇文章的結構讓主要論點很容易理解。'),
'system':('The new system allows students to review lessons on their phones.','新系統讓學生可以用手機複習課程。'),
'theory':('The scientist tested the theory by comparing it with real-world data.','科學家透過與真實世界資料比較來驗證這項理論。'),
'trend':('The chart shows a clear trend toward increased use of renewable energy.','圖表顯示再生能源使用量增加的明顯趨勢。'),
'value':('The survey helped the team understand the value of listening to users.','這項調查幫助團隊了解傾聽使用者意見的價值。'),
'advantage':('One advantage of studying in a group is that students can exchange ideas.','小組學習的一個優點是學生可以交換想法。'),
'alternative':('Walking or cycling can be a healthy alternative to taking a car.','步行或騎腳踏車可以是開車之外的健康替代方式。'),
'amount':('The amount of water we use each day can be reduced through simple habits.','透過簡單的習慣，我們可以減少每天的用水量。'),
'appropriate':('Choose language that is appropriate for both your audience and purpose.','請選擇適合你的讀者與寫作目的的語言。'),
'attitude':('A positive attitude can make difficult tasks feel more manageable.','正面的態度可以讓困難的任務感覺比較容易處理。'),
'behavior':('The study examined how online feedback influences student behavior.','這項研究探討網路回饋如何影響學生行為。'),
'circumstance':('Under these circumstances, delaying the trip was the safest choice.','在這些情況下，延後旅行是最安全的選擇。'),
'concept':('The teacher used a diagram to explain the difficult concept clearly.','老師用圖表清楚說明這個困難的概念。'),
'condition':('The plants grew faster when they were kept under the same condition.','這些植物在相同條件下生長得更快。'),
'context':('The meaning of an unfamiliar word can often be guessed from its context.','陌生單字的意思常常可以從上下文推測。'),
'contrast':('In contrast to the first plan, the new proposal costs much less.','與第一個方案相比，新提案的成本低很多。'),
'define':('The report clearly defines the problem before suggesting possible solutions.','這份報告在提出可能的解決方法前先清楚定義問題。'),
'demonstrate':('The experiment demonstrates how temperature can affect the speed of a reaction.','這項實驗示範溫度如何影響反應速度。'),
'distribution':('The map shows the distribution of rainfall across different regions.','這張地圖顯示不同地區的降雨分布。'),
'economic':('The city hopes the new railway will bring long-term economic benefits.','這座城市希望新鐵路能帶來長期的經濟效益。'),
'establish':('The school plans to establish a new program for student volunteers.','學校計畫成立一個新的學生志工計畫。'),
'estimate':('Experts estimate that the project will take about two years to complete.','專家估計這項計畫大約需要兩年才能完成。'),
'function':('The diagram explains the function of each part of the machine.','這張圖說明機器各部分的功能。'),
'identify':('The first step is to identify the main cause of the problem.','第一步是找出問題的主要原因。'),
'likely':('Students are more likely to remember information when they review it regularly.','學生規律複習時，更有可能記住所學資訊。'),
'major':('Traffic is a major source of air pollution in many large cities.','交通是許多大城市空氣污染的主要來源。'),
'measure':('Researchers used a simple test to measure changes in attention.','研究人員使用簡單測驗來測量注意力的變化。'),
'potential':('The new material has the potential to reduce energy use in buildings.','這種新材料有潛力降低建築物的能源使用。'),
'principle':('The design follows the basic principle that simple systems are easier to maintain.','這項設計遵循一個基本原則：簡單的系統比較容易維護。'),
'role':('Parents can play an important role in helping teenagers build healthy habits.','家長可以在幫助青少年建立健康習慣方面扮演重要角色。'),
'strategy':('She changed her study strategy after noticing which methods worked best.','她發現哪些方法最有效後，調整了自己的讀書策略。'),
'vary':('The amount of sleep people need can vary from person to person.','每個人需要的睡眠時間可能有所不同。')}

def load_json(p,default):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def corpus_scores():
    d=load_json(CORPUS,{}).get('words',{}); out={}
    for w,x in d.items():
        c=int(x.get('count',0) or 0); yc=int(x.get('yearCount',0) or 0); by=x.get('byYear',{}) or {}
        recent=sum(int(by.get(str(y),0) or 0) for y in range(111,116))
        out[w]=c+yc*4+recent*3
    return out

def valid_ready(word,x):
    en=str(x.get('en') or '').strip(); zh=str(x.get('zh') or '').strip()
    return bool(en and zh and word.lower() in en.lower() and not any(s.lower() in en.lower() for s in BANNED))

def rebuild_examples():
    vocab=load_json(VOCAB,{}).get('words',[])
    if len(vocab)<6000: raise SystemExit('vocabulary-zh.json 尚未建置完成')
    old=load_json(EXAMPLES,{}).get('words',{}); scores=corpus_scores(); rows={}
    for item in vocab:
        w=item['word']; prev=old.get(w,{})
        if w in NEW_BATCH:
            en,zh=NEW_BATCH[w]; rows[w]={'en':en,'zh':zh,'source':'reviewed','status':'ready','quality':'reviewed','corpusPriority':scores.get(w,0)}
        elif prev.get('status')=='ready' and valid_ready(w,prev):
            rows[w]={'en':prev['en'],'zh':prev['zh'],'source':prev.get('source','manual'),'status':'ready','quality':'reviewed','corpusPriority':scores.get(w,0)}
        else:
            rows[w]={'en':'','zh':'','source':'pending','status':'needs_review','quality':'pending','corpusPriority':scores.get(w,0)}
    ready=sum(x['status']=='ready' for x in rows.values()); gsat={w for w,s in scores.items() if s>0}
    payload={'version':VERSION,'generatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'policy':{'fakeFallbackDisabled':True,'pendingInsteadOfUnsafeExample':True,'priority':'101-115 GSAT corpus first'},'summary':{'words':len(rows),'ready':ready,'pending':len(rows)-ready,'reviewedBatchV147':len(NEW_BATCH),'gsatCorpusWords':len(gsat),'gsatReady':sum(1 for w in gsat if rows.get(w,{}).get('status')=='ready')},'words':rows}
    EXAMPLES.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

def rebuild_audit():
    vocab=load_json(VOCAB,{}).get('words',[]); ex=load_json(EXAMPLES,{}).get('words',{}); scores=corpus_scores(); issues=[]
    bad=('棻','춣','飻','נ','ם','�','fiea','tumpike','etemity','amobiography')
    for item in vocab:
        w=item['word']; m=str(item.get('meaning') or ''); score=scores.get(w,0); reasons=[]
        if not m or m=='—': score+=1000; reasons.append('missing_meaning')
        if any(t in m.lower() for t in bad): score+=900; reasons.append('garbled_meaning')
        if len(m)>120: score+=80; reasons.append('meaning_too_long')
        if any(tag in m for tag in ('[醫]','[經]','[計]','[化]','[法]')): score+=60; reasons.append('technical_dictionary_noise')
        if ex.get(w,{}).get('status')!='ready': score+=200+scores.get(w,0)*10; reasons.append('example_needs_review')
        if reasons: issues.append({'word':w,'level':item.get('level'),'score':score,'corpusPriority':scores.get(w,0),'reasons':reasons,'meaning':m[:180]})
    issues.sort(key=lambda x:(-x['score'],-x['corpusPriority'],x['level'] or 9,x['word']))
    AUDIT.write_text(json.dumps({'version':VERSION,'generatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'summary':{'flagged':len(issues),'pendingExamples':sum('example_needs_review' in x['reasons'] for x in issues)},'issues':issues},ensure_ascii=False,separators=(',',':')),encoding='utf-8')

def patch_frontend():
    app=APP.read_text(encoding='utf-8')
    if "const STORAGE_KEY='hs7000-v1';" not in app: raise SystemExit('STORAGE_KEY 已被改動，停止更新')
    app=re.sub(r"const EXAMPLES_URL='data/vocabulary-examples\.json\?v=[^']+';","const EXAMPLES_URL='data/vocabulary-examples.json?v=1.4.7';",app,count=1)
    app=app.replace("console.info('V1.4.5 examples loaded'","console.info('V1.4.7 examples loaded'")
    APP.write_text(app,encoding='utf-8')
    idx=INDEX.read_text(encoding='utf-8')
    idx=re.sub(r'版本 V1\.4\.[0-9.]+ · [^<]*','版本 V1.4.7 · 學測優先例句補全 + 101–115 學測語料庫',idx,count=1)
    INDEX.write_text(idx,encoding='utf-8')
    sw=SW.read_text(encoding='utf-8')
    sw=re.sub(r"const CACHE='hs7000-v[^']+';","const CACHE='hs7000-v1.4.7';",sw,count=1)
    SW.write_text(sw,encoding='utf-8')

def validate():
    ex=load_json(EXAMPLES,{}); words=ex.get('words',{})
    assert ex.get('version')==VERSION and len(words)>=6000
    assert len(NEW_BATCH)>=80
    for w in ('information','research','technology','decision','method','strategy'):
        x=words[w]; assert x['status']=='ready' and w in x['en'].lower() and x['zh'] and x['quality']=='reviewed'
    raw=EXAMPLES.read_text(encoding='utf-8')
    assert 'In this passage, the word' not in raw and 'helps readers understand its meaning' not in raw
    app=APP.read_text(encoding='utf-8'); assert "const STORAGE_KEY='hs7000-v1';" in app and 'vocabulary-examples.json?v=1.4.7' in app
    assert 'V1.4.7' in INDEX.read_text(encoding='utf-8') and 'hs7000-v1.4.7' in SW.read_text(encoding='utf-8')
    print('V1.4.7 validation passed'); print(ex['summary'])

def main():
    for p in (APP,INDEX,SW,VOCAB,EXAMPLES):
        if not p.exists(): raise SystemExit(f'缺少必要檔案：{p}')
    rebuild_examples(); rebuild_audit(); patch_frontend(); validate()

if __name__=='__main__': main()
