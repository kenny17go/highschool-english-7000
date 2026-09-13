#!/usr/bin/env python3
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path

VERSION='1.4.8'
VOCAB=Path('data/vocabulary-zh.json')
EXAMPLES=Path('data/vocabulary-examples.json')
SOURCES=Path('data/vocabulary-example-sources.json')
AUDIT=Path('data/vocabulary-quality-audit.json')
CORPUS=Path('data/gsat-corpus-stats.json')
APP=Path('app.js'); INDEX=Path('index.html'); SW=Path('sw.js')
BANNED=('In this passage, the word','The word “','helps readers understand its meaning')

def load(p,default):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def corpus_scores():
    out={}
    for w,x in load(CORPUS,{}).get('words',{}).items():
        by=x.get('byYear',{}) or {}; recent=sum(int(by.get(str(y),0) or 0) for y in range(111,116))
        out[w]=int(x.get('count',0) or 0)+4*int(x.get('yearCount',0) or 0)+3*recent
    return out

def wordnet_meta(word):
    try:
        from nltk.corpus import wordnet as wn
        syn=wn.synsets(word)
        return {'available':bool(syn),'synsetCount':len(syn),'exampleCount':sum(len(s.examples()) for s in syn),'synsets':[s.name() for s in syn[:6]]}
    except Exception:
        return {'available':False,'synsetCount':0,'exampleCount':0,'synsets':[]}

def quality(word,row):
    en=str(row.get('en') or '').strip(); zh=str(row.get('zh') or '').strip(); notes=[]; score=0
    if not en or not zh:return 0,'P',['missing_example_or_translation']
    if any(x.lower() in en.lower() for x in BANNED):return 0,'P',['banned_fake_example']
    tokens=re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",en); wc=len(tokens)
    if re.search(rf'(?i)(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])',en):score+=30
    else: notes.append('target_not_exact_surface')
    if 8<=wc<=22:score+=20
    elif 6<=wc<=26:score+=12;notes.append('length_ok_but_not_preferred')
    else:notes.append('length_outside_target')
    if zh:score+=20
    if row.get('source') in ('manual','reviewed'):score+=20
    if len(set(t.lower() for t in tokens))>=5:score+=10
    grade='A' if score>=90 else 'B' if score>=80 else 'C' if score>=70 else 'D'
    return score,grade,notes

def main():
    vocab=load(VOCAB,{}).get('words',[]); old=load(EXAMPLES,{}).get('words',{}); scores=corpus_scores()
    if len(vocab)<6000:raise SystemExit('vocabulary data incomplete')
    rows={}; audit=[]; grade_counts={g:0 for g in 'ABCDP'}; source_counts={}
    for item in vocab:
        w=item['word']; prev=old.get(w,{})
        q,grade,notes=quality(w,prev)
        wn=wordnet_meta(w)
        level=int(item.get('level') or 7); priority=scores.get(w,0)*10+(8-level)*12+(40 if wn['exampleCount'] else 0)
        ready=grade in ('A','B','C') and prev.get('status')=='ready'
        if ready:
            source_key='site_reviewed' if prev.get('source') in ('manual','reviewed') else str(prev.get('source') or 'legacy_reviewed')
            row={**prev,'status':'ready','qualityGrade':grade,'qualityScore':q,'qualityNotes':notes,'wordCount':len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",prev.get('en',''))),'sourceKey':source_key,'corpusPriority':scores.get(w,0),'reviewPriority':priority,'externalCandidates':{'wordnet':wn}}
        else:
            row={'en':'','zh':'','source':'pending','status':'needs_review','quality':'pending','qualityGrade':'P','qualityScore':0,'qualityNotes':notes or ['needs_review'],'wordCount':0,'sourceKey':'pending','corpusPriority':scores.get(w,0),'reviewPriority':priority,'externalCandidates':{'wordnet':wn}}
            audit.append({'word':w,'level':level,'reviewPriority':priority,'corpusPriority':scores.get(w,0),'wordnetExampleCount':wn['exampleCount'],'reason':'example_needs_review'})
        rows[w]=row;grade_counts[row['qualityGrade']]+=1;source_counts[row['sourceKey']]=source_counts.get(row['sourceKey'],0)+1
    audit.sort(key=lambda x:(-x['reviewPriority'],x['level'],x['word']))
    examples_payload={'version':VERSION,'generatedAt':now(),'policy':{'fakeFallbackDisabled':True,'preferredLength':'8-22 words','priority':'GSAT corpus > recent years > Level 1-6 > Level 7','externalTextImport':'disabled in V1.4.8; metadata only'},'summary':{'words':len(rows),'ready':sum(r['status']=='ready' for r in rows.values()),'pending':sum(r['status']!='ready' for r in rows.values()),'qualityGrades':grade_counts,'sources':source_counts},'words':rows}
    EXAMPLES.write_text(json.dumps(examples_payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    sources_payload={'version':VERSION,'generatedAt':now(),'sources':{'site_reviewed':{'name':'高中英文7000本站審核例句','type':'original/reviewed','license':'site-authored','textImported':True},'princeton_wordnet':{'name':'Princeton WordNet via NLTK','type':'candidate metadata','license':'WordNet License','textImported':False},'words_tw_reference':{'name':'words.tw','type':'reference only','textImported':False,'note':'僅參考覆蓋率與呈現方式，不複製例句'},'tatoeba':{'name':'Tatoeba','type':'future candidate source','license':'CC BY 2.0 FR / sentence-specific','textImported':False}},'rules':{'attributionRequired':True,'externalExampleTextImported':False}}
    SOURCES.write_text(json.dumps(sources_payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    AUDIT.write_text(json.dumps({'version':VERSION,'generatedAt':now(),'summary':{'pendingExamples':len(audit)},'issues':audit},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    app=APP.read_text(encoding='utf-8')
    if "const STORAGE_KEY='hs7000-v1';" not in app:raise SystemExit('STORAGE_KEY changed')
    app=re.sub(r"const EXAMPLES_URL='data/vocabulary-examples\.json\?v=[^']+';","const EXAMPLES_URL='data/vocabulary-examples.json?v=1.4.8';",app,count=1)
    app=re.sub(r"function genericExample\(w\)\{.*?\}\nfunction genericCollocations", "function genericExample(w){return '例句待校正'}\nfunction genericCollocations", app, count=1, flags=re.S)
    app=app.replace("console.info('V1.4.7 examples loaded'","console.info('V1.4.8 examples loaded'")
    APP.write_text(app,encoding='utf-8')
    idx=INDEX.read_text(encoding='utf-8');idx=re.sub(r'版本 V1\.4\.[0-9.]+ · [^<]*','版本 V1.4.8 · 全量例句引擎 + 來源追蹤 + 品質分級',idx,count=1);INDEX.write_text(idx,encoding='utf-8')
    sw=SW.read_text(encoding='utf-8');sw=re.sub(r"const CACHE='hs7000-v[^']+';","const CACHE='hs7000-v1.4.8';",sw,count=1);SW.write_text(sw,encoding='utf-8')
    data=load(EXAMPLES,{})
    assert data.get('version')==VERSION and len(data.get('words',{}))>=6000
    assert "const STORAGE_KEY='hs7000-v1';" in APP.read_text(encoding='utf-8')
    assert 'vocabulary-examples.json?v=1.4.8' in APP.read_text(encoding='utf-8')
    assert SOURCES.exists() and 'words_tw_reference' in load(SOURCES,{}).get('sources',{})
    print('V1.4.8 example engine passed',data['summary'])

if __name__=='__main__':main()
