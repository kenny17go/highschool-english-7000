#!/usr/bin/env python3
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path

VERSION='1.5.1'
VOCAB=Path('data/vocabulary-zh.json')
AI=Path('data/ai-original-examples.json')
EXAMPLES=Path('data/vocabulary-examples.json')
SOURCES=Path('data/vocabulary-example-sources.json')
AUDIT=Path('data/vocabulary-quality-audit.json')
APP=Path('app.js'); INDEX=Path('index.html'); SW=Path('sw.js')
BANNED=('In this passage, the word','The word “','helps readers understand its meaning','http://','https://')

def load(p,default):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def tokens(s):return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",s)

def exact_surface(word,s):
    return bool(re.search(rf'(?i)(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])',s))

def quality(word,en,zh):
    en=' '.join(str(en or '').split()); zh=str(zh or '').strip(); notes=[]; score=0
    if not en or not zh:return 0,'P',['missing_example_or_translation']
    if any(x.lower() in en.lower() for x in BANNED):return 0,'P',['banned_or_invalid_example']
    wc=len(tokens(en))
    if exact_surface(word,en):score+=40
    else:notes.append('target_not_exact_surface')
    if 8<=wc<=22:score+=25
    elif 6<=wc<=26:score+=15;notes.append('length_near_target')
    else:notes.append('length_outside_target')
    if en[-1:] in '.!?':score+=10
    else:notes.append('missing_terminal_punctuation')
    if len(set(t.lower() for t in tokens(en)))>=5:score+=10
    if zh:score+=15
    grade='A' if score>=90 else 'B' if score>=80 else 'C' if score>=70 else 'D'
    return score,grade,notes

def load_ai_batches():
    merged={}; files=[]; duplicate_overrides=[]
    paths=[AI]+sorted(Path('data').glob('ai-original-examples-batch-*.json'))
    for p in paths:
        if not p.exists():continue
        payload=load(p,{})
        if payload.get('version')!=VERSION:raise SystemExit(f'AI example batch version mismatch: {p}')
        words=payload.get('words',{})
        if not isinstance(words,dict):raise SystemExit(f'Invalid AI example batch: {p}')
        files.append({'file':str(p),'words':len(words)})
        for w,x in words.items():
            if w in merged:duplicate_overrides.append({'word':w,'file':str(p)})
            merged[w]=x
    return merged,files,duplicate_overrides

def main():
    vocab=load(VOCAB,{}).get('words',[])
    ai,ai_files,duplicate_overrides=load_ai_batches()
    old=load(EXAMPLES,{}).get('words',{})
    if len(vocab)<6000:raise SystemExit('vocabulary data incomplete')
    if not ai:raise SystemExit('AI original examples missing')

    rows={}; issues=[]; source_counts={}; grades={g:0 for g in 'ABCDP'}
    ai_ready=0; preserved_ready=0; ai_failed=0; ai_not_in_vocab=[]
    seen=set()
    vocab_keys={str(x.get('word','')) for x in vocab}
    for w in sorted(ai):
        if w not in vocab_keys: ai_not_in_vocab.append(w)

    for item in vocab:
        w=item['word']
        if w in seen:continue
        seen.add(w)
        level=int(item.get('level') or 7)
        if w in ai:
            en=ai[w].get('en',''); zh=ai[w].get('zh','')
            q,grade,notes=quality(w,en,zh)
            if grade in ('A','B','C'):
                row={'en':en,'zh':zh,'source':'ai_original','sourceKey':'chatgpt_original','status':'ready','quality':'reviewed','qualityGrade':grade,'qualityScore':q,'qualityNotes':notes,'wordCount':len(tokens(en)),'level':level}
                ai_ready+=1
            else:
                ai_failed+=1
                row={'en':'','zh':'','source':'pending','sourceKey':'pending','status':'needs_review','quality':'pending','qualityGrade':'P','qualityScore':0,'qualityNotes':notes,'wordCount':0,'level':level}
                issues.append({'word':w,'level':level,'reason':'ai_example_failed_quality','notes':notes})
        else:
            prev=old.get(w,{})
            pq,pgrade,pnotes=quality(w,prev.get('en',''),prev.get('zh',''))
            if prev.get('status')=='ready' and pgrade in ('A','B','C'):
                row={**prev,'status':'ready','qualityGrade':pgrade,'qualityScore':pq,'qualityNotes':pnotes,'wordCount':len(tokens(prev.get('en',''))),'level':level}
                row['sourceKey']=row.get('sourceKey') or ('site_reviewed' if row.get('source') in ('manual','reviewed') else row.get('source','legacy_reviewed'))
                preserved_ready+=1
            else:
                row={'en':'','zh':'','source':'pending','sourceKey':'pending','status':'needs_review','quality':'pending','qualityGrade':'P','qualityScore':0,'qualityNotes':['awaiting_ai_original'],'wordCount':0,'level':level}
                issues.append({'word':w,'level':level,'reason':'awaiting_ai_original'})
        rows[w]=row
        grades[row['qualityGrade']]=grades.get(row['qualityGrade'],0)+1
        source_counts[row['sourceKey']]=source_counts.get(row['sourceKey'],0)+1

    ready=sum(r['status']=='ready' for r in rows.values()); pending=len(rows)-ready
    coverage=round(ready/max(1,len(rows)),6)
    EXAMPLES.write_text(json.dumps({'version':VERSION,'generatedAt':now(),'policy':{'primarySource':'ChatGPT original examples','commercialDictionaryCopying':False,'preferredLength':'8-22 words','fakeFallbackDisabled':True,'workflow':'word + POS + current Chinese meaning -> original sentence + zh-Hant-TW translation -> basic quality check'},'summary':{'words':len(rows),'ready':ready,'pending':pending,'coverage':coverage,'aiOriginalInput':len(ai),'aiOriginalReady':ai_ready,'aiOriginalFailed':ai_failed,'preservedReady':preserved_ready,'qualityGrades':grades,'sources':source_counts,'batchFiles':ai_files,'duplicateOverrides':len(duplicate_overrides),'aiWordsNotInVocabulary':len(ai_not_in_vocab)},'words':rows},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    SOURCES.write_text(json.dumps({'version':VERSION,'generatedAt':now(),'sources':{'chatgpt_original':{'name':'ChatGPT 原創例句','type':'original','textImported':True,'copiedFromCommercialDictionary':False},'site_reviewed':{'name':'高中英文7000既有審核例句','type':'original/reviewed','textImported':True},'commercial_dictionaries':{'name':'Cambridge/Oxford/Longman 等商業詞典','type':'reference only','textImported':False,'note':'可用於確認常見義項與用法，不批次複製例句'},'legacy_wordnet_pipeline':{'name':'V1.4.9-V1.5.0 WordNet 候選資料','type':'legacy/archive','textImported':False,'note':'保留舊資料檔供追蹤，不再作為主流程'}},'rules':{'originalExamplesPreferred':True,'externalCommercialExamplesCopied':False}},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    AUDIT.write_text(json.dumps({'version':VERSION,'generatedAt':now(),'summary':{'words':len(rows),'ready':ready,'pending':pending,'coverage':coverage,'aiOriginalInput':len(ai),'aiOriginalReady':ai_ready,'aiOriginalFailed':ai_failed,'preservedReady':preserved_ready,'batchFiles':ai_files,'duplicateOverrides':duplicate_overrides,'aiWordsNotInVocabulary':ai_not_in_vocab},'issues':issues},ensure_ascii=False,separators=(',',':')),encoding='utf-8')

    app=APP.read_text(encoding='utf-8')
    if "const STORAGE_KEY='hs7000-v1';" not in app:raise SystemExit('STORAGE_KEY changed')
    app=re.sub(r"const EXAMPLES_URL='data/vocabulary-examples\.json\?v=[^']+';","const EXAMPLES_URL='data/vocabulary-examples.json?v=1.5.1';",app,count=1)
    app=re.sub(r"console\.info\('V1\.[0-9.]+ examples loaded'","console.info('V1.5.1 examples loaded'",app,count=1)
    APP.write_text(app,encoding='utf-8')
    idx=INDEX.read_text(encoding='utf-8');idx=re.sub(r'版本 V1\.[0-9.]+ · [^<]*','版本 V1.5.1 · AI 原創例句全量補全',idx,count=1);INDEX.write_text(idx,encoding='utf-8')
    sw=SW.read_text(encoding='utf-8');sw=re.sub(r"const CACHE='hs7000-v[^']+';","const CACHE='hs7000-v1.5.1';",sw,count=1);SW.write_text(sw,encoding='utf-8')

    data=load(EXAMPLES,{})
    assert data.get('version')==VERSION and len(data.get('words',{}))>=6000
    assert data.get('summary',{}).get('aiOriginalReady',0)>0
    assert data.get('summary',{}).get('aiOriginalInput',0)==len(ai)
    assert "const STORAGE_KEY='hs7000-v1';" in APP.read_text(encoding='utf-8')
    assert 'vocabulary-examples.json?v=1.5.1' in APP.read_text(encoding='utf-8')
    print('V1.5.1 AI-original pipeline passed',data['summary'])

if __name__=='__main__':main()
