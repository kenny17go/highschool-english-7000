#!/usr/bin/env python3
import json, re, subprocess, tempfile, urllib.request
from pathlib import Path
from collections import Counter, defaultdict

SOURCES = {
101: 'https://www.ceec.edu.tw/files/file_pool/1/0j076570671923496609/02-101%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7%E5%AE%9A%E7%A8%BF.pdf',
102: 'https://www.ceec.edu.tw/files/file_pool/1/0j051824585770646720/102%E5%B9%B4%E5%AD%B8%E7%A7%91%E8%83%BD%E5%8A%9B%E6%B8%AC%E9%A9%97%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A_00.pdf',
103: 'https://www.ceec.edu.tw/files/file_pool/1/0j076572147183041652/02-103%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87-%E5%AE%9A%E7%A8%BF.pdf',
104: 'https://www.ceec.edu.tw/files/file_pool/1/0j076572827714606282/02-104%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E5%AE%9A%E7%A8%BF.pdf',
105: 'https://www.ceec.edu.tw/files/file_pool/1/0j051825763397987863/105%E5%AD%B8%E6%B8%AC%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A.pdf',
106: 'https://www.ceec.edu.tw/files/file_pool/1/0j051826215298462880/106%E5%AD%B8%E6%B8%AC%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A.pdf',
107: 'https://www.ceec.edu.tw/files/file_pool/1/0j051826568834816834/107%E5%AD%B8%E6%B8%AC%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A.pdf',
108: 'https://www.ceec.edu.tw/files/file_pool/1/0j301533916033318514/108%E5%AD%B8%E6%B8%AC%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A_%E5%AE%8C%E6%88%90%E6%AA%9420190705.pdf',
109: 'https://www.ceec.edu.tw/files/file_pool/1/0k050359836694452838/02-109%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7-%E5%AE%9A%E7%A8%BF.pdf',
110: 'https://www.ceec.edu.tw/files/file_pool/1/0L022396748545177938/02-110%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7.pdf',
111: 'https://www.ceec.edu.tw/files/file_pool/1/0m053357638065462325/02-111%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7.pdf',
112: 'https://www.ceec.edu.tw/files/file_pool/1/0N014423635146157074/02-112%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7.pdf',
113: 'https://www.ceec.edu.tw/files/file_pool/1/0O021576671649197989/02-113%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E7%A7%91%E8%A9%A6%E9%A1%8C.pdf',
114: 'https://www.ceec.edu.tw/files/file_pool/1/0p056425554473267580/02-114%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E9%A1%8C.pdf',
115: 'https://www.ceec.edu.tw/files/file_pool/1/0q054532302653501476/02-115%E5%AD%B8%E6%B8%AC%E8%8B%B1%E6%96%87%E8%A9%A6%E5%8D%B7.pdf',
}
WORK_REPORT_YEARS={102,105,106,107,108}
SECTIONS=[
 ('vocabulary', r'(?:一、)?詞彙(?:題)?'),('cloze',r'(?:二、)?綜合測驗'),('discourse',r'篇章結構'),
 ('fill',r'文意選填'),('reading',r'閱讀測驗'),('mixed',r'混合題'),('translation',r'中譯英'),('writing',r'英文作文')
]
STOP=set('a an the and or but if then than that this these those i you he she it we they me him her us them my your his our their is am are was were be been being have has had do does did can could may might must shall should will would of to in on at by for from with as into over under about after before between through during without within not no so very more most less least many much some any each every all both either neither one two three four five first second third who whom whose which what when where why how'.split())
WORD_RE=re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")

def download(url,path):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 GSAT-corpus-builder'})
    with urllib.request.urlopen(req,timeout=60) as r, open(path,'wb') as f: f.write(r.read())

def pdf_text(pdf,txt):
    subprocess.run(['pdftotext','-layout',str(pdf),str(txt)],check=True)
    return txt.read_text('utf-8',errors='ignore')

def english_segment(text, year):
    if year not in WORK_REPORT_YEARS: return text
    # Work reports contain many subjects. Pick the English-exam occurrence nearest a real section heading.
    candidates=[]
    for m in re.finditer(r'英文\s*考科',text):
        window=text[m.start():m.start()+70000]
        if re.search(r'第[壹一]部分|詞彙題|單選題',window[:5000]): candidates.append(m.start())
    if not candidates: return text
    start=candidates[0]
    tail=text[start:]
    end=len(tail)
    for pat in [r'\n\s*(?:國文|數學|社會|自然)\s*考科\s*\n',r'\n\s*第[貳二]篇']:
        mm=re.search(pat,tail[5000:])
        if mm: end=min(end,5000+mm.start())
    return tail[:end]

def tokens(text): return [x.lower().replace('’',"'") for x in WORD_RE.findall(text)]

def split_sections(text):
    marks=[]
    for key,pat in SECTIONS:
        m=re.search(pat,text)
        if m: marks.append((m.start(),key))
    marks.sort()
    out={}
    for i,(pos,key) in enumerate(marks):
        end=marks[i+1][0] if i+1<len(marks) else len(text)
        out[key]=text[pos:end]
    return out

def main():
    out=Path('data/gsat-corpus-stats.json'); out.parent.mkdir(parents=True,exist_ok=True)
    yearly={}; agg=Counter(); word_years=defaultdict(set); by_year=defaultdict(Counter); by_section=defaultdict(Counter)
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        for year,url in SOURCES.items():
            pdf=td/f'{year}.pdf'; txt=td/f'{year}.txt'
            print('fetch',year,url,flush=True)
            download(url,pdf); raw=pdf_text(pdf,txt); text=english_segment(raw,year)
            ts=tokens(text); content=[w for w in ts if w not in STOP and len(w)>1]
            c=Counter(content); agg.update(c); by_year[year].update(c)
            for w in c: word_years[w].add(year)
            sec_stats={}
            for sec,chunk in split_sections(text).items():
                sc=Counter(w for w in tokens(chunk) if w not in STOP and len(w)>1)
                by_section[sec].update(sc); sec_stats[sec]={'tokens':sum(sc.values()),'unique':len(sc)}
            yearly[str(year)]={'source':url,'tokens':len(content),'unique':len(c),'sections':sec_stats,'status':'tokenized'}
    words={}
    for w,count in agg.most_common():
        years=sorted(word_years[w]); words[w]={
          'count':count,'yearCount':len(years),'years':years,
          'byYear':{str(y):by_year[y][w] for y in years},
          'sections':{s:c[w] for s,c in by_section.items() if c[w]}
        }
    data={'version':'1.4.1','range':[101,115],'generatedAt':__import__('datetime').datetime.utcnow().isoformat()+'Z','years':yearly,
          'summary':{'papers':len(yearly),'tokens':sum(x['tokens'] for x in yearly.values()),'unique':len(agg)},'words':words,
          'method':'Official CEEC PDFs -> pdftotext -> English word tokenization; stop words excluded from content-word frequency. All observed content-word types are retained as derived statistics; full exam text is not stored.'}
    out.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),'utf-8')
    print('wrote',out, out.stat().st_size)
if __name__=='__main__': main()
