#!/usr/bin/env python3
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path

VERSION='1.4.9'
VOCAB=Path('data/vocabulary-zh.json')
EXAMPLES=Path('data/vocabulary-examples.json')
CANDIDATES=Path('data/vocabulary-example-candidates.json')
SOURCES=Path('data/vocabulary-example-sources.json')
AUDIT=Path('data/vocabulary-quality-audit.json')
CORPUS=Path('data/gsat-corpus-stats.json')
APP=Path('app.js'); INDEX=Path('index.html'); SW=Path('sw.js')
BANNED=('In this passage, the word','The word “','helps readers understand its meaning','http://','https://')

def load(p,default):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def corpus_scores():
    out={}
    for w,x in load(CORPUS,{}).get('words',{}).items():
        by=x.get('byYear',{}) or {}
        recent=sum(int(by.get(str(y),0) or 0) for y in range(111,116))
        out[w]=int(x.get('count',0) or 0)+4*int(x.get('yearCount',0) or 0)+3*recent
    return out

def exact_surface(word,s):
    return bool(re.search(rf'(?i)(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])',s))

def sentence_tokens(s):return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",s)

def published_quality(word,row):
    en=str(row.get('en') or '').strip(); zh=str(row.get('zh') or '').strip(); notes=[]; score=0
    if not en or not zh:return 0,'P',['missing_example_or_translation']
    if any(x.lower() in en.lower() for x in BANNED):return 0,'P',['banned_or_invalid_example']
    wc=len(sentence_tokens(en))
    if exact_surface(word,en):score+=30
    else:notes.append('target_not_exact_surface')
    if 8<=wc<=22:score+=20
    elif 6<=wc<=26:score+=12;notes.append('length_ok_but_not_preferred')
    else:notes.append('length_outside_target')
    score+=20
    if row.get('source') in ('manual','reviewed'):score+=20
    if len(set(t.lower() for t in sentence_tokens(en)))>=5:score+=10
    grade='A' if score>=90 else 'B' if score>=80 else 'C' if score>=70 else 'D'
    return score,grade,notes

def candidate_score(word,s):
    s=' '.join(str(s).split()); notes=[]
    if not s or any(x.lower() in s.lower() for x in BANNED):return None
    if not exact_surface(word,s):return None
    wc=len(sentence_tokens(s))
    if wc<6 or wc>26:return None
    score=50
    if 8<=wc<=22:score+=25
    else:score+=12;notes.append('length_near_target')
    if s[0].isupper() and s[-1] in '.!?':score+=8
    if len(set(t.lower() for t in sentence_tokens(s)))>=5:score+=7
    if not re.search(r'[_{}<>]|\bwww\b',s,re.I):score+=5
    if re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',s):notes.append('possible_proper_name')
    return score,notes,wc,s

def wordnet_candidates(word):
    out=[]
    try:
        from nltk.corpus import wordnet as wn
        seen=set()
        for syn in wn.synsets(word):
            for i,s in enumerate(syn.examples()):
                x=candidate_score(word,s)
                if not x:continue
                score,notes,wc,text=x
                key=text.lower()
                if key in seen:continue
                seen.add(key)
                out.append({'en':text,'sourceKey':'princeton_wordnet','sourceId':f'{syn.name()}#{i+1}','license':'WordNet License','score':score,'wordCount':wc,'qualityNotes':notes,'translationStatus':'missing','status':'candidate'})
        out.sort(key=lambda x:(-x['score'],x['wordCount'],x['en']))
        return out[:3],len(seen)
    except Exception:
        return [],0

def main():
    vocab=load(VOCAB,{}).get('words',[]); old=load(EXAMPLES,{}).get('words',{}); scores=corpus_scores()
    if len(vocab)<6000:raise SystemExit('vocabulary data incomplete')
    rows={}; candidate_words={}; audit=[]; grades={g:0 for g in 'ABCDP'}; source_counts={}
    total_candidates=0; words_with_candidates=0
    for item in vocab:
        w=item['word']; prev=old.get(w,{})
        q,grade,notes=published_quality(w,prev)
        level=int(item.get('level') or 7); base_priority=scores.get(w,0)*10+(8-level)*12
        ready=grade in ('A','B','C') and prev.get('status')=='ready'
        cands,raw_count=wordnet_candidates(w)
        if cands:
            words_with_candidates+=1;total_candidates+=len(cands)
            candidate_words[w]={'word':w,'level':level,'corpusPriority':scores.get(w,0),'reviewPriority':base_priority+60,'candidateCount':len(cands),'rawWordNetCandidateCount':raw_count,'candidates':cands}
        if ready:
            source_key='site_reviewed' if prev.get('source') in ('manual','reviewed') else str(prev.get('source') or 'legacy_reviewed')
            row={**prev,'status':'ready','qualityGrade':grade,'qualityScore':q,'qualityNotes':notes,'wordCount':len(sentence_tokens(prev.get('en',''))),'sourceKey':source_key,'corpusPriority':scores.get(w,0),'reviewPriority':base_priority}
        else:
            row={'en':'','zh':'','source':'pending','status':'needs_review','quality':'pending','qualityGrade':'P','qualityScore':0,'qualityNotes':notes or ['needs_review'],'wordCount':0,'sourceKey':'pending','corpusPriority':scores.get(w,0),'reviewPriority':base_priority+(60 if cands else 0)}
            audit.append({'word':w,'level':level,'reviewPriority':row['reviewPriority'],'corpusPriority':scores.get(w,0),'candidateCount':len(cands),'reason':'example_needs_review'})
        rows[w]=row;grades[row['qualityGrade']]+=1;source_counts[row['sourceKey']]=source_counts.get(row['sourceKey'],0)+1
    audit.sort(key=lambda x:(-x['reviewPriority'],x['level'],x['word']))
    no_candidate=sum(1 for x in audit if x['candidateCount']==0)
    EXAMPLES.write_text(json.dumps({'version':VERSION,'generatedAt':now(),'policy':{'fakeFallbackDisabled':True,'preferredLength':'8-22 words','priority':'GSAT corpus > recent years > Level 1-6 > Level 7','candidatePublication':'review required'},'summary':{'words':len(rows),'ready':sum(r['status']=='ready' for r in rows.values()),'pending':sum(r['status']!='ready' for r in rows.values()),'qualityGrades':grades,'sources':source_counts},'words':rows},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    CANDIDATES.write_text(json.dumps({'version':VERSION,'generatedAt':now(),'summary':{'words':len(vocab),'wordsWithCandidates':words_with_candidates,'candidateSentences':total_candidates,'wordsWithoutCandidates':no_candidate},'rules':{'maxCandidatesPerWord':3,'publishAutomatically':False,'translationRequiredBeforePublish':True,'preferredLength':'8-22 words'},'words':candidate_words},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    SOURCES.write_text(json.dumps({'version':VERSION,'generatedAt':now(),'sources':{'site_reviewed':{'name':'高中英文7000本站審核例句','type':'original/reviewed','license':'site-authored','textImported':True},'princeton_wordnet':{'name':'Princeton WordNet via NLTK','type':'candidate example source','license':'WordNet License','textImported':True,'publicationPolicy':'candidate only until reviewed and translated'},'words_tw_reference':{'name':'words.tw','type':'reference only','textImported':False,'note':'僅參考覆蓋率與呈現方式，不複製例句'},'tatoeba':{'name':'Tatoeba','type':'future candidate source','license':'CC BY 2.0 FR / sentence-specific','textImported':False}},'rules':{'attributionRequired':True,'candidateReviewRequired':True}},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    AUDIT.write_text(json.dumps({'version':VERSION,'generatedAt':now(),'summary':{'pendingExamples':len(audit),'wordsWithCandidates':words_with_candidates,'candidateSentences':total_candidates,'wordsWithoutCandidates':no_candidate},'issues':audit},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    app=APP.read_text(encoding='utf-8')
    if "const STORAGE_KEY='hs7000-v1';" not in app:raise SystemExit('STORAGE_KEY changed')
    app=re.sub(r"const EXAMPLES_URL='data/vocabulary-examples\.json\?v=[^']+';","const EXAMPLES_URL='data/vocabulary-examples.json?v=1.4.9';",app,count=1)
    app=re.sub(r"console\.info\('V1\.4\.[0-9.]+ examples loaded'","console.info('V1.4.9 examples loaded'",app,count=1)
    APP.write_text(app,encoding='utf-8')
    idx=INDEX.read_text(encoding='utf-8');idx=re.sub(r'版本 V1\.4\.[0-9.]+ · [^<]*','版本 V1.4.9 · 全量例句候選補全 + 來源追蹤 + 品質分級',idx,count=1);INDEX.write_text(idx,encoding='utf-8')
    sw=SW.read_text(encoding='utf-8');sw=re.sub(r"const CACHE='hs7000-v[^']+';","const CACHE='hs7000-v1.4.9';",sw,count=1);SW.write_text(sw,encoding='utf-8')
    data=load(EXAMPLES,{});cand=load(CANDIDATES,{})
    assert data.get('version')==VERSION and len(data.get('words',{}))>=6000
    assert cand.get('version')==VERSION and cand.get('summary',{}).get('words',0)>=6000
    assert "const STORAGE_KEY='hs7000-v1';" in APP.read_text(encoding='utf-8')
    assert 'vocabulary-examples.json?v=1.4.9' in APP.read_text(encoding='utf-8')
    print('V1.4.9 candidate engine passed',cand['summary'])

if __name__=='__main__':main()
