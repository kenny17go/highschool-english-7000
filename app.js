const CURRENT_URL='https://raw.githubusercontent.com/EngTW/English-for-Programmers/main/lists/Taiwan-high-school-6K-108-edition/Data/Taiwan-high-school-english-reference-vocabulary-list-108-edition.json';
const LEGACY_URL='https://raw.githubusercontent.com/mahavivo/english-wordlists/master/%E5%8F%B0%E7%81%A3%E9%AB%98%E4%B8%AD%E8%8B%B1%E6%96%87%E5%8F%83%E8%80%83%E8%A9%9E%E5%BD%99%E8%A1%A8.txt';
const LOCAL_VOCAB_URL='data/vocabulary-zh.json?v=1.4.4';
const DETAILS_URL='data/vocabulary-details.json?v=1.4.5';
const EXAMPLES_URL='data/vocabulary-examples.json?v=1.4.8';
let WORD_DETAILS={};
let WORD_EXAMPLES={};
const STORAGE_KEY='hs7000-v1';
const HIGH_FREQ_WORDS=new Set(['abandon','ability','accept','achieve','academic','acknowledge','accurate','adjust','affect','analyze','annual','approach','assume','available','benefit','challenge','consequence','consider','contribute','develop','environment','evidence','factor','feature','impact','indicate','individual','involve','issue','maintain','occur','participate','particularly','provide','require','significant','specific','suggest','support','therefore','various']);
const FALLBACK=[
 {word:'ability',pos:['n.'],level:1,meaning:'能力；才能'},{word:'accept',pos:['v.'],level:2,meaning:'接受；同意；承認'},{word:'achieve',pos:['v.'],level:3,meaning:'達成；實現；取得'},{word:'academic',pos:['adj.'],level:4,meaning:'學術的；學業的'},{word:'acknowledge',pos:['v.'],level:5,meaning:'承認；確認；致謝'},{word:'abbreviate',pos:['v.'],level:6,meaning:'縮寫；節略'},{word:'abandon',pos:['v.'],level:4,meaning:'放棄；拋棄；遺棄'},{word:'accurate',pos:['adj.'],level:3,meaning:'準確的；精確的'},{word:'adjust',pos:['v.'],level:4,meaning:'調整；適應'},{word:'affect',pos:['v.'],level:2,meaning:'影響；感動'},{word:'analyze',pos:['v.'],level:4,meaning:'分析；解析'},{word:'annual',pos:['adj.'],level:4,meaning:'每年的；年度的'}
];
const ENRICH={
 ability:{ex:'She has the ability to explain difficult ideas clearly.',col:['have the ability to','reading ability','natural ability'],root:'able（能夠的）＋ -ity（名詞字尾）',syn:['capacity','skill','talent'],ant:['inability'],conf:['capability']},
 accept:{ex:'You do not have to accept every opinion you hear.',col:['accept an offer','accept responsibility','widely accepted'],root:'ac-（朝向）＋ cept（取、拿）',syn:['receive','admit','approve'],ant:['reject','refuse'],conf:['except']},
 achieve:{ex:'With steady practice, you can achieve your academic goals.',col:['achieve a goal','achieve success','achieve a balance'],root:'a- ＋ chieve（完成、達到）',syn:['accomplish','attain','reach'],ant:['fail'],conf:['achievement']},
 academic:{ex:'The school provides extra academic support before major exams.',col:['academic performance','academic year','academic achievement'],root:'academy ＋ -ic（形容詞字尾）',syn:['scholarly','educational'],ant:['nonacademic'],conf:['academy']},
 acknowledge:{ex:'The writer acknowledged that the first explanation was incomplete.',col:['acknowledge a fact','acknowledge the importance of','widely acknowledged'],root:'knowledge（知識）相關字族',syn:['admit','recognize','confirm'],ant:['deny','ignore'],conf:['knowledge']},
 abandon:{ex:'The team had to abandon the plan because of the sudden storm.',col:['abandon a plan','abandon an idea','abandon hope'],root:'源自「置於控制之外」的語意發展',syn:['give up','leave','desert'],ant:['keep','continue'],conf:['abundant']},
 accurate:{ex:'Accurate information is especially important when you write a report.',col:['accurate information','highly accurate','accurate description'],root:'accurate → accuracy（名詞）',syn:['correct','precise','exact'],ant:['inaccurate','wrong'],conf:['actual']},
 adjust:{ex:'It may take a few weeks to adjust to a new study schedule.',col:['adjust to','adjust the settings','make an adjustment'],root:'ad-（朝向）＋ just（調整、使合適）',syn:['adapt','modify','alter'],ant:[],conf:['adapt']},
 affect:{ex:'Lack of sleep can affect your concentration in class.',col:['affect performance','greatly affect','be affected by'],root:'af-（朝向）＋ fect（做、造成）',syn:['influence','impact'],ant:[],conf:['effect']},
 analyze:{ex:'Students were asked to analyze the causes of the problem.',col:['analyze data','analyze a problem','carefully analyze'],root:'ana-（分開、向上）＋ -lyze（分解）',syn:['examine','study','evaluate'],ant:[],conf:['analysis']},
 annual:{ex:'The school holds an annual science fair every spring.',col:['annual report','annual meeting','annual income'],root:'ann（年）＋ -ual（形容詞字尾）',syn:['yearly'],ant:['monthly','daily'],conf:['annually']}
};
const PREFIXES=[['anti','反對、對抗'],['inter','在…之間'],['trans','跨越、轉移'],['sub','在下、次級'],['super','在上、超越'],['pre','在前、預先'],['post','在後、之後'],['re','再、回'],['un','不、相反'],['dis','不、分離'],['mis','錯誤'],['over','過度、在上'],['under','不足、在下']];
const SUFFIXES=[['tion','名詞字尾：行為／結果'],['sion','名詞字尾：行為／結果'],['ment','名詞字尾：狀態／結果'],['ness','名詞字尾：性質／狀態'],['ity','名詞字尾：性質／狀態'],['able','形容詞字尾：能…的'],['ible','形容詞字尾：能…的'],['less','形容詞字尾：沒有…的'],['ful','形容詞字尾：充滿…的'],['ous','形容詞字尾：具有…的'],['ive','形容詞字尾：具有…性質'],['ly','副詞字尾'],['er','人／物，或比較級字尾']];
let bank=[],session=[],sessionIndex=0,quiz=[],quizIndex=0,quizScore=0,examMode='regular',currentQuestion=null,bookFilter='all',currentDetailWord=null;
let state=loadState();
function loadState(){const base={progress:{},mistakes:{},favorites:{},stats:{correct:0,total:0},settings:{dailyGoal:20,mode:'7000',autoSpeak:true,showExampleZh:true},lastStudy:null,streak:0};try{const saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||'{}');return {...base,...saved,progress:saved.progress||{},mistakes:saved.mistakes||{},favorites:saved.favorites||{},stats:{...base.stats,...(saved.stats||{})},settings:{...base.settings,...(saved.settings||{})}}}catch{return base}}
function saveState(){localStorage.setItem(STORAGE_KEY,JSON.stringify(state))}
function normalizeWord(w){return String(w||'').toLowerCase().replace(/^\*/,'').trim()}
function parseLegacy(text){const map=new Map();text.split(/\r?\n/).forEach(line=>{line=line.trim();if(!line||/^[A-Z]$/.test(line)||line.includes('大學學測'))return;const m=line.match(/^\*?([A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*)?)\s+(.+)$/);if(!m)return;const word=normalizeWord(m[1]);let rest=m[2].trim();const posMatch=rest.match(/^((?:adj\.|adv\.|n\.|v\.|prep\.|conj\.|pron\.|art\.|num\.|aux\.|int\.)[^\u4e00-\u9fff]*)/i);let pos=[],meaning=rest;if(posMatch){pos=posMatch[1].split(/[\/;, ]+/).filter(x=>x.includes('.'));meaning=rest.slice(posMatch[0].length).trim()}map.set(word,{meaning:meaning||'—',pos})});return map}
function rootHint(word){if(ENRICH[word]?.root)return ENRICH[word].root;const pre=PREFIXES.find(([x])=>word.startsWith(x)&&word.length>x.length+3);const suf=SUFFIXES.find(([x])=>word.endsWith(x)&&word.length>x.length+3);const bits=[];if(pre)bits.push(`${pre[0]}-（${pre[1]}）`);if(suf)bits.push(`-${suf[0]}（${suf[1]}）`);return bits.length?bits.join(' ＋ '):'此字建議以字族與例句一起記憶'}
function genericExample(w){return '例句待校正'}
function genericCollocations(w){if(ENRICH[w.word]?.col)return ENRICH[w.word].col;const p=(w.pos||[])[0]||'';if(p.startsWith('v'))return [`${w.word} + 受詞`,`can / may + ${w.word}`,`${w.word} carefully`];if(p.startsWith('adj'))return [`be ${w.word}`,`very / highly ${w.word}`,`${w.word} + 名詞`];if(p.startsWith('n'))return [`a / the ${w.word}`,`${w.word} of ...`,`important ${w.word}`];return [`常見於句中依詞性搭配`];}
function editDistance(a,b){const m=a.length,n=b.length,d=Array.from({length:m+1},()=>Array(n+1).fill(0));for(let i=0;i<=m;i++)d[i][0]=i;for(let j=0;j<=n;j++)d[0][j]=j;for(let i=1;i<=m;i++)for(let j=1;j<=n;j++)d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]===b[j-1]?0:1));return d[m][n]}
function confusables(w){if(ENRICH[w.word]?.conf)return ENRICH[w.word].conf;return bank.filter(x=>x.word!==w.word&&Math.abs(x.word.length-w.word.length)<=1&&x.word[0]===w.word[0]).map(x=>({x,d:editDistance(w.word,x.word)})).filter(o=>o.d>0&&o.d<=2).sort((a,b)=>a.d-b.d).slice(0,3).map(o=>o.x.word)}
function detailFor(w){const e=ENRICH[w.word]||{},a=WORD_DETAILS[w.word]||{},x=WORD_EXAMPLES[w.word]||{};const syn=(e.syn&&e.syn.length)?e.syn:(a.syn||[]),ant=(e.ant&&e.ant.length)?e.ant:(a.ant||[]),conf=(e.conf&&e.conf.length)?e.conf:confusables(w);const ready=!!e.ex||(x.status==='ready'&&!!x.en);return {example:e.ex||x.en||(x.status==='needs_review'?'例句待校正':genericExample(w)),exampleZh:e.ex?(x.zh||''):(x.zh||''),exampleSource:e.ex?'manual':(x.source||'fallback'),exampleReady:ready,collocations:(e.col&&e.col.length)?e.col:genericCollocations(w),root:e.root||a.structure||rootHint(w.word),syn,ant,conf,family:a.family||[]}}
function isFavorite(word){return !!state.favorites?.[word]}
function toggleFavorite(word){state.favorites=state.favorites||{};if(state.favorites[word])delete state.favorites[word];else state.favorites[word]=Date.now();saveState();renderBook();renderProgress();if(currentDetailWord?.word===word)fillDetail(currentDetailWord)}
function isHighFreq(w){return HIGH_FREQ_WORDS.has(w.word)||(w.level>=3&&w.level<=5&&!!ENRICH[w.word])}
function frequencyLabel(w){return isHighFreq(w)?'🔥 學測優先':'一般'}
function parseCustomWords(){return (document.getElementById('customWords')?.value||'').toLowerCase().split(/[\s,;，、]+/).map(normalizeWord).filter(Boolean)}

async function loadWordExamples(){try{const r=await fetch(EXAMPLES_URL,{cache:'no-store'});if(!r.ok)throw new Error('examples '+r.status);const x=await r.json();WORD_EXAMPLES=x.words||{};console.info('V1.4.8 examples loaded',Object.keys(WORD_EXAMPLES).length);if(bank.length)renderAll();}catch(e){console.warn('word examples unavailable',e)}}
async function loadWordDetails(){try{const r=await fetch(DETAILS_URL,{cache:'no-store'});if(!r.ok)throw new Error('details '+r.status);const x=await r.json();WORD_DETAILS=x.words||{};console.info('V1.4.4 details loaded',Object.keys(WORD_DETAILS).length);if(bank.length)renderAll();}catch(e){console.warn('word details unavailable',e)}}
async function loadBank(){
  const status=document.getElementById('bankStatus');
  status.textContent='載入本地中文字庫…';
  try{
    const localRes=await fetch(LOCAL_VOCAB_URL,{cache:'no-store'});
    if(localRes.ok){
      const local=await localRes.json();
      if(Array.isArray(local.words)&&local.words.length>=6000){
        bank=local.words.map(x=>({
          word:normalizeWord(x.word),
          pos:Array.isArray(x.pos)?x.pos:[],
          level:Number(x.level)||7,
          meaning:String(x.meaning||'—').trim()||'—',
          source:x.source||'local'
        }));
        const missing=bank.filter(x=>!x.meaning||x.meaning==='—'||x.meaning.includes('待補充')).length;
        status.textContent=`已載入 ${bank.length.toLocaleString()} 字 · 中文釋義本地版${missing?` · ${missing} 字待校正`:''}`;
        renderAll();
        return;
      }
    }
  }catch(e){console.warn('local vocabulary unavailable',e)}
  status.textContent='本地字庫未建置，改用線上備援…';
  try{
    const [curRes,oldRes]=await Promise.all([fetch(CURRENT_URL),fetch(LEGACY_URL)]);
    if(!curRes.ok||!oldRes.ok)throw new Error('network');
    const current=await curRes.json(),legacy=parseLegacy(await oldRes.text()),currentSet=new Set();
    bank=current.map(x=>{
      const word=normalizeWord(x.Word);currentSet.add(word);const old=legacy.get(word);
      return {word,pos:x.PartsOfSpeech||old?.pos||[],level:Number(x.Level)||1,meaning:old?.meaning||'中文釋義待補充',source:'108'};
    });
    const extras=[];
    for(const [word,info] of legacy){
      if(!currentSet.has(word)&&extras.length<1000)extras.push({word,pos:info.pos,level:7,meaning:info.meaning,source:'legacy'});
    }
    bank.push(...extras);
    status.textContent=`已載入 ${bank.length.toLocaleString()} 字 · 線上備援`;
  }catch(e){
    bank=[...FALLBACK];
    status.textContent='離線示範字庫';
  }
  renderAll();
}
function eligibleBank(){const mode=state.settings.mode;return bank.filter(w=>mode==='7000'?true:mode==='6000'?w.level<=6:w.level<=4)}
function getProgress(word){return state.progress[word]||null}function isDue(p){return p&&p.due&&new Date(p.due)<=new Date()}function getNewWords(n){return eligibleBank().filter(w=>!getProgress(w.word)).slice(0,n)}function getDueWords(){return eligibleBank().filter(w=>isDue(getProgress(w.word))).sort((a,b)=>new Date(getProgress(a.word).due)-new Date(getProgress(b.word).due))}
function updateStreak(){const today=new Date().toISOString().slice(0,10);if(state.lastStudy===today)return;const y=new Date(Date.now()-86400000).toISOString().slice(0,10);state.streak=state.lastStudy===y?(state.streak||0)+1:1;state.lastStudy=today;saveState()}
function speak(word){if(!('speechSynthesis'in window))return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(word);u.lang='en-US';u.rate=.9;speechSynthesis.speak(u)}
function renderAll(){renderHome();renderLevels();renderBook();renderProgress();renderInsights();syncSettingsUI()}
function renderHome(){const total=eligibleBank().length,learned=eligibleBank().filter(w=>getProgress(w.word)).length,due=getDueWords().length,today=Math.min(Number(state.settings.dailyGoal)||20,getNewWords(999).length);document.getElementById('learnedCount').textContent=learned;document.getElementById('reviewCount').textContent=due;document.getElementById('streakCount').textContent=state.streak||0;document.getElementById('accuracyCount').textContent=state.stats.total?Math.round(state.stats.correct/state.stats.total*100)+'%':'—';document.getElementById('todaySummary').textContent=due?`${due} 字到期複習，再學 ${today} 個新字`:`今天安排 ${today} 個新字`;const pct=total?Math.round(learned/total*100):0;document.getElementById('todayPct').textContent=pct+'%';document.getElementById('todayRing').style.setProperty('--p',pct+'%')}
function renderLevels(){const el=document.getElementById('levelList');el.innerHTML='';const labels=['','基礎地基','高一核心','中級過渡','學測主力','高分衝刺','進階查閱','7000 補充'];for(let lv=1;lv<=7;lv++){if(lv===7&&state.settings.mode!=='7000')continue;const words=eligibleBank().filter(w=>w.level===lv),learned=words.filter(w=>getProgress(w.word)).length,d=document.createElement('div');d.className='level-card';d.innerHTML=`<div class="level-badge">L${lv}</div><div><h4>${lv===7?'進階補充':`Level ${lv}`} · ${labels[lv]}</h4><p>${learned.toLocaleString()} / ${words.length.toLocaleString()} 已學</p></div><strong>${words.length?Math.round(learned/words.length*100):0}%</strong>`;d.onclick=()=>startSession(words.filter(w=>!getProgress(w.word)).slice(0,state.settings.dailyGoal));el.appendChild(d)}}
function startSession(words){session=words.length?words:getDueWords().slice(0,state.settings.dailyGoal);if(!session.length){alert('目前沒有需要學習的單字。');return}sessionIndex=0;showView('learn');showSessionWord()}
function showSessionWord(){const w=session[sessionIndex];if(!w){renderAll();showView('home');return}const d=detailFor(w);document.getElementById('wordText').textContent=w.word;document.getElementById('wordLevel').textContent=w.level===7?'進階補充':`Level ${w.level}`;document.getElementById('wordPos').textContent=(w.pos||[]).join(' / ')||'—';document.getElementById('wordMeaning').textContent=w.meaning;document.getElementById('wordExample').textContent=d.example;const wz=document.getElementById('wordExampleZh');if(wz){wz.textContent=d.exampleZh||'';wz.classList.toggle('hidden',!state.settings.showExampleZh||!d.exampleZh||!d.exampleReady)};document.getElementById('wordCollocations').textContent=d.collocations.join(' · ');document.getElementById('wordRoot').textContent=d.root;document.getElementById('wordSynonyms').textContent=d.syn.length?d.syn.join(' · '):'—';document.getElementById('wordAntonyms').textContent=d.ant.length?d.ant.join(' · '):'—';document.getElementById('wordConfusables').textContent=d.conf.length?d.conf.join(' · '):'—';document.getElementById('wordHint').textContent=(w.meaning==='中文釋義待補充'||w.meaning==='—')?'此詞的中文資料仍待校正；可先用例句、字族與測驗學習。':'';const lf=document.getElementById('learnFavoriteBtn');if(lf){lf.textContent=isFavorite(w.word)?'★':'☆';lf.classList.toggle('active',isFavorite(w.word))}document.getElementById('answerArea').classList.add('hidden');document.getElementById('ratingGrid').classList.add('hidden');document.getElementById('showAnswerBtn').classList.remove('hidden');document.getElementById('sessionCounter').textContent=`${sessionIndex+1}/${session.length}`;document.getElementById('sessionProgress').style.width=`${sessionIndex/session.length*100}%`;if(state.settings.autoSpeak)speak(w.word)}
function gradeWord(grade){const w=session[sessionIndex],old=getProgress(w.word)||{interval:0,ease:2.3,reps:0};let days=0;if(grade==='again'){days=0;old.interval=0;old.reps=0}else if(grade==='hard'){days=1;old.interval=1;old.reps++}else if(grade==='good'){days=old.interval?Math.max(3,Math.round(old.interval*2.2)):3;old.interval=days;old.reps++}else{days=old.interval?Math.max(7,Math.round(old.interval*3)):7;old.interval=days;old.reps++}const due=new Date(Date.now()+days*86400000+(grade==='again'?10*60000:0));state.progress[w.word]={...old,last:new Date().toISOString(),due:due.toISOString(),grade};updateStreak();saveState();sessionIndex++;showSessionWord()}
function renderBook(){const q=(document.getElementById('searchInput')?.value||'').toLowerCase(),lv=document.getElementById('bookLevel')?.value||'all';let pool=eligibleBank().filter(w=>(lv==='all'||String(w.level)===lv)&&(!q||w.word.includes(q)||w.meaning.includes(q)));if(bookFilter==='favorites')pool=pool.filter(w=>isFavorite(w.word));else if(bookFilter==='highfreq')pool=pool.filter(isHighFreq);else if(bookFilter==='mistakes')pool=pool.filter(w=>state.mistakes[w.word]);const items=pool.slice(0,250);document.getElementById('bookCount').textContent=`${pool.length.toLocaleString()} 字`;const el=document.getElementById('wordList');el.innerHTML='';items.forEach(w=>{const d=detailFor(w),row=document.createElement('div');row.className='word-row';row.innerHTML=`<button class="star-btn ${isFavorite(w.word)?'active':''}" aria-label="收藏">${isFavorite(w.word)?'★':'☆'}</button><div class="word-main"><div class="word-title-line"><b>${w.word}</b>${isHighFreq(w)?'<span class="hot-tag">HOT</span>':''}</div><small>${(w.pos||[]).join(' / ')}</small><p>${w.meaning}</p><div class="extra">${d.collocations.slice(0,2).join(' · ')}</div></div><span class="tag">${w.level===7?'ADV':`L${w.level}`}</span>`;row.querySelector('.star-btn').onclick=e=>{e.stopPropagation();toggleFavorite(w.word)};row.onclick=()=>openWordDetail(w);el.appendChild(row)});if(!items.length)el.innerHTML='<div class="empty-state">找不到符合條件的單字。</div>'}
function renderProgress(){const eligible=eligibleBank(),learned=eligible.filter(w=>getProgress(w.word)).length;document.getElementById('overallLearned').textContent=learned;document.getElementById('overallTotal').textContent=eligible.length;document.getElementById('overallBar').style.width=(eligible.length?learned/eligible.length*100:0)+'%';const el=document.getElementById('levelProgress');el.innerHTML='';for(let lv=1;lv<=7;lv++){const arr=eligible.filter(w=>w.level===lv);if(!arr.length)continue;const n=arr.filter(w=>getProgress(w.word)).length,d=document.createElement('div');d.className='progress-row';d.innerHTML=`<b>${lv===7?'進階':`L${lv}`}</b><div class="mini-track"><div style="width:${n/arr.length*100}%"></div></div><span>${n}/${arr.length}</span>`;el.appendChild(d)}const mistakes=Object.keys(state.mistakes).length;document.getElementById('mistakeSummary').textContent=mistakes?`目前有 ${mistakes} 個單字需要加強。`:'目前沒有錯題。';const fav=Object.keys(state.favorites||{}).length;document.getElementById('favoriteSummary').textContent=fav?`已收藏 ${fav} 個單字，可集中複習或測驗。`:'目前沒有收藏單字。'}
function makeQuizPool(){const scope=document.getElementById('quizScope').value;let pool=eligibleBank();if(scope==='learned')pool=pool.filter(w=>getProgress(w.word));else if(scope==='favorites')pool=pool.filter(w=>isFavorite(w.word));else if(scope==='highfreq')pool=pool.filter(isHighFreq);else if(scope==='mistakes')pool=pool.filter(w=>state.mistakes[w.word]);else if(scope==='custom'){const wanted=new Set(parseCustomWords());pool=pool.filter(w=>wanted.has(w.word))}else if(/^[1-7]$/.test(scope))pool=pool.filter(w=>String(w.level)===scope);return pool.filter(w=>w.meaning&&w.meaning!=='中文釋義待補充')}
function pickType(){const selected=document.getElementById('quizType').value;if(selected!=='mixed')return selected;return examMode==='gsat'?(['cloze','cloze','en-zh'][Math.floor(Math.random()*3)]):(['en-zh','zh-en','spelling'][Math.floor(Math.random()*3)])}
function beginQuiz(){const pool=makeQuizPool(),count=Math.min(Number(document.getElementById('quizCount').value),pool.length);if(count<4){alert('目前可測驗的單字不足 4 個，請先學一些單字或切換範圍。');return}quiz=[...pool].sort(()=>Math.random()-.5).slice(0,count);quizIndex=0;quizScore=0;document.getElementById('quizSetup').classList.add('hidden');document.getElementById('examModeTabs').classList.add('hidden');document.getElementById('examDesc').classList.add('hidden');document.getElementById('quizArea').classList.remove('hidden');showQuiz()}
function distractors(w,kind){let pool=eligibleBank().filter(x=>x.word!==w.word&&x.meaning&&x.meaning!=='中文釋義待補充');if(kind==='word')pool=pool.filter(x=>x.level===w.level||Math.abs(x.level-w.level)<=1);return [...pool].sort(()=>Math.random()-.5).slice(0,3)}
function showQuiz(){if(quizIndex>=quiz.length){const pct=Math.round(quizScore/quiz.length*100);document.getElementById('quizArea').innerHTML=`<div class="dashboard-card"><h2>測驗完成</h2><div class="big-number">${pct}%</div><p>答對 ${quizScore} / ${quiz.length} 題</p><button class="primary big" onclick="location.reload()">完成</button></div>`;renderAll();return}const w=quiz[quizIndex],type=pickType(),d=detailFor(w);currentQuestion={w,type};document.getElementById('quizIndex').textContent=`${quizIndex+1}/${quiz.length}`;document.getElementById('quizScore').textContent=`${quizScore} 分`;document.getElementById('quizFeedback').textContent='';document.getElementById('nextQuizBtn').classList.add('hidden');document.getElementById('quizOptions').innerHTML='';document.getElementById('spellingBox').classList.add('hidden');document.getElementById('quizSpeakBtn').classList.toggle('hidden',type==='zh-en'||type==='spelling');document.getElementById('quizContext').textContent='';if(type==='en-zh'){document.getElementById('questionType').textContent='英 → 中';document.getElementById('quizWord').textContent=w.word;renderOptions([w,...distractors(w,'meaning')].sort(()=>Math.random()-.5),o=>o.meaning,o=>o.word===w.word,w)}else if(type==='zh-en'){document.getElementById('questionType').textContent='中 → 英';document.getElementById('quizWord').textContent=w.meaning;renderOptions([w,...distractors(w,'word')].sort(()=>Math.random()-.5),o=>o.word,o=>o.word===w.word,w)}else if(type==='spelling'){document.getElementById('questionType').textContent='拼字';document.getElementById('quizWord').textContent=w.meaning;document.getElementById('spellingBox').classList.remove('hidden');const inp=document.getElementById('spellingInput');inp.value='';setTimeout(()=>inp.focus(),50)}else{document.getElementById('questionType').textContent='學測情境克漏字';document.getElementById('quizWord').textContent='選出最適合的單字';document.getElementById('quizContext').textContent=d.example.replace(new RegExp(`\\b${w.word}\\b`,'i'),'_____');renderOptions([w,...distractors(w,'word')].sort(()=>Math.random()-.5),o=>o.word,o=>o.word===w.word,w)}}
function renderOptions(opts,label,isCorrect,w){const el=document.getElementById('quizOptions');opts.forEach(o=>{const b=document.createElement('button');b.className='option';b.textContent=label(o);b.onclick=()=>answerQuiz(b,isCorrect(o),w,label(w));el.appendChild(b)})}
function answerQuiz(btn,correct,w,answerText){document.querySelectorAll('.option').forEach(b=>b.disabled=true);state.stats.total++;if(correct){btn.classList.add('correct');quizScore++;state.stats.correct++;document.getElementById('quizFeedback').textContent='答對了！'}else{btn.classList.add('wrong');state.mistakes[w.word]=(state.mistakes[w.word]||0)+1;document.getElementById('quizFeedback').textContent=`正確答案：${answerText}`;document.querySelectorAll('.option').forEach(b=>{if(b.textContent===answerText)b.classList.add('correct')})}saveState();document.getElementById('nextQuizBtn').classList.remove('hidden')}
function submitSpelling(){if(!currentQuestion||currentQuestion.type!=='spelling')return;const {w}=currentQuestion,inp=document.getElementById('spellingInput'),ans=normalizeWord(inp.value),correct=ans===w.word;state.stats.total++;inp.disabled=true;if(correct){quizScore++;state.stats.correct++;document.getElementById('quizFeedback').textContent='拼字正確！'}else{state.mistakes[w.word]=(state.mistakes[w.word]||0)+1;document.getElementById('quizFeedback').textContent=`正確拼字：${w.word}`}saveState();document.getElementById('nextQuizBtn').classList.remove('hidden')}
function fillDetail(w){currentDetailWord=w;const d=detailFor(w),p=getProgress(w.word);document.getElementById('detailLevel').textContent=w.level===7?'進階補充':`Level ${w.level}`;document.getElementById('detailFrequency').textContent=frequencyLabel(w);document.getElementById('detailWord').textContent=w.word;document.getElementById('detailPos').textContent=(w.pos||[]).join(' / ')||'—';document.getElementById('detailMeaning').textContent=w.meaning;document.getElementById('detailExample').textContent=d.example;const dz=document.getElementById('detailExampleZh');if(dz){dz.textContent=d.exampleZh||'';dz.classList.toggle('hidden',!state.settings.showExampleZh||!d.exampleZh||!d.exampleReady)};document.getElementById('detailCollocations').textContent=d.collocations.join(' · ')||'—';document.getElementById('detailRoot').textContent=d.root;document.getElementById('detailSynonyms').textContent=d.syn.join(' · ')||'—';document.getElementById('detailAntonyms').textContent=d.ant.join(' · ')||'—';document.getElementById('detailConfusables').textContent=d.conf.join(' · ')||'—';document.getElementById('detailStudyStatus').textContent=p?`已學習 · 上次評級：${p.grade||'—'} · 下次複習：${p.due?new Date(p.due).toLocaleDateString('zh-TW'):'—'}`:'尚未學習';document.getElementById('detailFavoriteBtn').textContent=isFavorite(w.word)?'★ 已收藏':'☆ 收藏';renderDetailCorpus(w)}
function openWordDetail(w){fillDetail(w);document.getElementById('wordDetailDialog').showModal()}
function showView(name){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.dataset.view===name));document.querySelectorAll('.nav-item').forEach(n=>n.classList.toggle('active',n.dataset.target===name));if(name==='book')renderBook();if(name==='progress')renderProgress();if(name==='insights')renderInsights();window.scrollTo({top:0,behavior:'smooth'})}
function syncSettingsUI(){document.getElementById('dailyGoal').value=state.settings.dailyGoal||20;document.getElementById('studyMode').value=state.settings.mode||'7000';document.getElementById('autoSpeak').checked=state.settings.autoSpeak;const ez=document.getElementById('showExampleZh');if(ez)ez.checked=state.settings.showExampleZh!==false!==false}
function setExamMode(mode){examMode=mode;document.querySelectorAll('.mode-tab').forEach(b=>b.classList.toggle('active',b.dataset.exam===mode));document.getElementById('quizModeLabel').textContent=mode==='gsat'?'學測模式':'段考模式';document.getElementById('examDesc').textContent=mode==='gsat'?'學測模式：以情境克漏字、上下文判斷與近義辨析為主。':'段考模式：中英互譯、精準字義、拼字與課內型單字題。';if(mode==='gsat')document.getElementById('quizType').value='mixed'}

// ===== V1.4 學測戰情室 / 101–115 語料庫 =====
// 近五年官方學測英文「詞彙題」選項字。僅保存單字與年度標記，不保存完整題幹。
const GSAT_VOCAB_OPTIONS={
  111:`advanced delivered offered stretched assistant influence contribution politician chat quiz puppet variety potentially delicately ambiguously optionally tagging flocking rolling snapping enormous intimate agreeable ultimate identical visible available remarkable moderate absolute promising eventual trial route strike quest bounces blushes polishes transfers`.split(/\s+/),
  112:`sticky greasy clumsy mighty clap toss pose snap siblings commuters ancestors instructors blank bare hollow queer liability generosity integrity sincerity resolve fraction privilege recall provoke counter expose convert crippled accelerated rendered ventured choked disturbed enclosed injected undoubtedly roughly understandably supposedly`.split(/\s+/),
  113:`spicy slender slight slippery emerging flashing rushing floating apt due bound docked density humidity circulation atmosphere stay take serve stand forceful realistic compulsory distinctive advantage revenge remedy credit proposes contains promises confirms appeal approach operation observation eligibly randomly apparently consequently`.split(/\s+/),
  114:`border timer container marker produce fashion brand trend blurring trimming draining glaring excessive furious offensive stubborn text brush draft plot casual fragile remote vacant gigantic exclusive multiple enormous halted hatched possessed reinforced praised graced addressed credited verbally dominantly legitimately relevantly`.split(/\s+/),
  115:`hasty tight diligent routine official instant amateur elementary career vacancy expectation inspiration initially genuinely alternatively fundamentally dimension integration provision consumption dreads stresses wanders escapes resource impact passion emphasis shattered assaulted overturned condemned crash tumble elbow struggle swift brutal harsh grave`.split(/\s+/)
};
const GSAT_PATTERN_CARDS=[
  {tag:'結果句型',title:'such / so ... that ...',note:'常用前半句提供程度線索，後半句描述結果。做題時先判斷空格需要形容詞還是副詞。',example:'The schedule was so demanding that everyone had to plan several weeks ahead.',focus:['demanding','schedule','that']},
  {tag:'搭配辨識',title:'動詞＋受詞的自然搭配',note:'學測詞彙題常把四個意思接近或詞性相同的字放在一起，真正關鍵是「哪一個和受詞搭得自然」。',example:'The new policy raised serious concerns among students and teachers.',focus:['raise concerns','serious']},
  {tag:'上下文推論',title:'前後句反差／因果',note:'先抓 although、despite、therefore、as a result 等邏輯訊號，再選符合語意方向的字。',example:'Although the device looked simple, its internal design was surprisingly complex.',focus:['although','surprisingly']},
  {tag:'片語與介系詞',title:'固定搭配比單字義更重要',note:'像 depend on、be responsible for、be exposed to 這類搭配，常需要整組辨識。',example:'The final result may depend on how carefully the data are collected.',focus:['depend on']},
  {tag:'篇章結構',title:'承接前文＋引出後文',note:'115 學年度起篇章結構為四個空格搭配五個選項；判斷時要同時看代名詞指涉、連接語與段落功能。',example:'This change, however, created a new problem that researchers had not expected.',focus:['however','This change']}
];
function buildGsatIndex(){
  const map=new Map();
  Object.entries(GSAT_VOCAB_OPTIONS).forEach(([year,words])=>words.forEach(word=>{
    word=normalizeWord(word); if(!map.has(word))map.set(word,{word,years:[],count:0});
    const x=map.get(word); x.count++; x.years.push(Number(year));
  }));
  return map;
}
const GSAT_INDEX=buildGsatIndex();
let CORPUS_DATA=null;

async function loadCorpusData(){
  try{
    const r=await fetch('./data/gsat-corpus-stats.json',{cache:'no-store'}); if(!r.ok)throw new Error('corpus');
    CORPUS_DATA=await r.json();
  }catch(e){CORPUS_DATA={version:'1.4.1',years:{},summary:{papers:15,tokens:0,unique:0},words:{}}}
  renderCorpusLab();if(currentDetailWord)renderDetailCorpus(currentDetailWord);
}
function fmtNum(n){return Number(n||0).toLocaleString('en-US')}
const CORPUS_SECTION_NAMES={vocabulary:'詞彙題',cloze:'綜合測驗',fill:'文意選填',discourse:'篇章結構',reading:'閱讀測驗',mixed:'混合題',translation:'中譯英',writing:'英文作文'};
function corpusIsReady(){return Number(CORPUS_DATA?.summary?.tokens||0)>0}
function corpusWordInfo(word){return CORPUS_DATA?.words?.[normalizeWord(word)]||null}
function recentFiveCounts(x){return [111,112,113,114,115].map(y=>Number(x?.byYear?.[String(y)]||0))}
function recentTrend(x){
  const counts=recentFiveCounts(x),n=counts.length,meanX=2,meanY=counts.reduce((a,b)=>a+b,0)/n;
  let num=0,den=0;counts.forEach((y,i)=>{num+=(i-meanX)*(y-meanY);den+=(i-meanX)**2});const slope=den?num/den:0;
  let dir='flat',label='→ 持平';if(slope>=.25){dir='up';label='↑ 上升'}else if(slope<=-.25){dir='down';label='↓ 下降'}
  return {counts,slope,dir,label,total:counts.reduce((a,b)=>a+b,0)};
}
function corpusImportance(x){
  if(!corpusIsReady())return {stars:0,score:0,label:'待建置'};
  if(!x)return {stars:1,score:0,label:'低'};
  const recent=recentTrend(x).total,sectionN=Object.keys(x.sections||{}).filter(k=>x.sections[k]>0).length;
  const score=Math.min(25,(Number(x.yearCount||0)*1.15)+(Math.log2(Number(x.count||0)+1)*1.7)+(recent*1.3)+(sectionN*.9));
  const stars=score>=18?5:score>=13?4:score>=8?3:score>=4?2:1;
  const label=['','低','留意','重要','高頻','核心'][stars];return {stars,score:Math.round(score*10)/10,label};
}
function starText(n){return n?`${'★'.repeat(n)}${'☆'.repeat(5-n)}`:'待建置'}
function renderDetailCorpus(w){
  const status=document.getElementById('detailCorpusStatus');if(!status)return;
  const x=corpusWordInfo(w.word),ready=corpusIsReady(),importance=corpusImportance(x),trend=recentTrend(x);
  document.getElementById('detailCorpusCount').textContent=ready?fmtNum(x?.count||0):'—';
  document.getElementById('detailCorpusYearCount').textContent=ready?`${x?.yearCount||0} / 15`:'—';
  document.getElementById('detailCorpusTrend').textContent=ready?trend.label:'待建置';
  document.getElementById('detailCorpusTrend').className=`trend-value ${ready?trend.dir:'pending'}`;
  document.getElementById('detailCorpusImportance').textContent=starText(importance.stars);
  document.getElementById('detailCorpusImportanceText').textContent=ready?`${importance.label} · 指數 ${importance.score}`:'完成 GitHub 語料建置後自動計算';
  status.textContent=ready?'101–115 全卷統計':'語料待建置';status.className=`corpus-status ${ready?'ready':'pending'}`;
  const years=document.getElementById('detailCorpusYears');
  years.innerHTML=ready?(x?.years?.length?x.years.map(y=>`<span>${y}</span>`).join(''):'<em>101～115 全卷未偵測到此字</em>'):'<em>請先在 GitHub Actions 執行 Build GSAT corpus</em>';
  const secs=document.getElementById('detailCorpusSections');
  if(!ready){secs.innerHTML='<div class="corpus-empty-line">完整題型分布會在語料建置後顯示。</div>'}
  else if(!x||!Object.keys(x.sections||{}).length){secs.innerHTML='<div class="corpus-empty-line">目前無題型分布紀錄。</div>'}
  else{const entries=Object.entries(x.sections).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]),max=Math.max(...entries.map(([,v])=>v));secs.innerHTML=entries.map(([k,v])=>`<div class="section-dist-row"><span>${CORPUS_SECTION_NAMES[k]||k}</span><i><b style="width:${Math.max(6,v/max*100)}%"></b></i><strong>${v}</strong></div>`).join('')}
  const chart=document.getElementById('detailRecentTrend');
  const max=Math.max(1,...trend.counts);chart.innerHTML=[111,112,113,114,115].map((y,i)=>`<div class="trend-col"><div class="trend-count">${ready?trend.counts[i]:'—'}</div><div class="trend-track"><i style="height:${ready?Math.max(ready&&trend.counts[i]?12:3,trend.counts[i]/max*100):3}%"></i></div><small>${y}</small></div>`).join('');
}
function renderCorpusLab(){
  const grid=document.getElementById('corpusYearGrid');if(!grid)return;
  const years=CORPUS_DATA?.years||{},summary=CORPUS_DATA?.summary||{};
  document.getElementById('corpusPaperCount').textContent=summary.papers||15;
  document.getElementById('corpusTokenCount').textContent=summary.tokens?fmtNum(summary.tokens):'待建置';
  document.getElementById('corpusUniqueCount').textContent=summary.unique?fmtNum(summary.unique):'待建置';
  const built=Object.values(years).filter(x=>x.status==='tokenized').length;
  document.getElementById('corpusBuildStatus').textContent=built===15?'15/15 已語料化':`來源 15/15 · 語料 ${built}/15`;
  grid.innerHTML=Array.from({length:15},(_,i)=>101+i).map(y=>{const x=years[String(y)]||{};const ready=x.status==='tokenized';return `<div class="corpus-year ${ready?'ready':''}"><b>${y}</b><small>${ready?`${fmtNum(x.tokens)} tokens`:'來源已索引'}</small></div>`}).join('');
}
function searchCorpusWord(){
  const q=normalizeWord(document.getElementById('corpusSearchInput')?.value||'');const box=document.getElementById('corpusSearchResult');if(!box)return;
  if(!q){box.innerHTML='<p>輸入英文單字後查詢。</p>';return}
  const x=CORPUS_DATA?.words?.[q];
  if(x){const secs=Object.entries(x.sections||{}).sort((a,b)=>b[1]-a[1]),imp=corpusImportance(x),trend=recentTrend(x);box.innerHTML=`<h4>${q}</h4><p>101–115 全卷共出現 <b>${x.count}</b> 次，分布於 <b>${x.yearCount}</b> 個年度。</p><div class="corpus-badges">${(x.years||[]).map(y=>`<span>${y}</span>`).join('')}</div><p>${secs.length?'題型分布：'+secs.map(([k,v])=>`${CORPUS_SECTION_NAMES[k]||k} ${v}`).join(' · '):'尚無題型分布資料'}</p><p>近5年趨勢：<b>${trend.label}</b> · 真題重要度：<b>${starText(imp.stars)}</b></p>`}
  else if((CORPUS_DATA?.summary?.tokens||0)===0){box.innerHTML=`<h4>${q}</h4><p>目前 ZIP 內是來源索引版。上傳 GitHub 後執行 <b>Build GSAT corpus</b>，就會自動產生 101–115 全卷詞頻資料。</p>`}
  else box.innerHTML=`<h4>${q}</h4><p>在 101～115 完整內容詞統計中未偵測到此字。</p>`;
}

function masteryScore(word){
  const p=getProgress(word); if(!p)return 0;
  const interval=Number(p.interval||0), ease=Number(p.ease||2.2);
  let s=Math.min(100, 20 + interval*8 + Math.max(0,ease-1.3)*20);
  if(state.mistakes?.[word])s-=Math.min(45,state.mistakes[word]*8);
  if(isDue(p))s-=15;
  return Math.max(5,Math.min(100,Math.round(s)));
}
function weaknessScore(w){
  const p=getProgress(w.word), mistakes=Number(state.mistakes?.[w.word]||0), gs=GSAT_INDEX.get(w.word);
  const cx=corpusWordInfo(w.word),ci=corpusImportance(cx);let score=mistakes*18 + (gs?18+gs.count*6:0) + (corpusIsReady()?ci.stars*5:0);
  if(p){score+=(100-masteryScore(w.word))*.45;if(isDue(p))score+=12}else score+=8;
  if(w.level>=4&&w.level<=6)score+=6;
  if(isFavorite(w.word))score+=2;
  return Math.round(score);
}
function gsatPriority(){return eligibleBank().map(w=>({w,score:weaknessScore(w),gs:GSAT_INDEX.get(w.word),mastery:masteryScore(w.word)})).filter(x=>x.gs||state.mistakes?.[x.w.word]).sort((a,b)=>b.score-a.score)}
function renderGsatRanking(){
  const el=document.getElementById('gsatRanking'); if(!el)return;
  const all=[...GSAT_INDEX.values()], top=gsatPriority().slice(0,18);
  const totalUnique=all.length;
  document.getElementById('gsatWordCount').textContent=Object.values(GSAT_VOCAB_OPTIONS).reduce((n,a)=>n+a.length,0);
  document.getElementById('riskWordCount').textContent=top.filter(x=>x.score>=35).length;
  const matched=eligibleBank().filter(w=>GSAT_INDEX.has(w.word)), mastered=matched.filter(w=>masteryScore(w.word)>=65).length;
  document.getElementById('masteredGsatPct').textContent=matched.length?`${Math.round(mastered/matched.length*100)}%`:'0%';
  el.innerHTML=top.length?top.map((x,i)=>`<button class="rank-row" data-rank-word="${x.w.word}"><span class="rank-no">${i+1}</span><span class="rank-word"><b>${x.w.word}</b><small>${x.w.meaning}</small></span><span class="rank-meta">${x.gs?`真題 ${x.gs.years.join('、')}`:'你的錯題'}<small>熟練 ${x.mastery}% · 優先度 ${x.score}</small></span></button>`).join(''):`<div class="empty-state">完成幾次測驗後，這裡會依你的弱點排序。</div>`;
  el.querySelectorAll('[data-rank-word]').forEach(b=>b.onclick=()=>{const w=bank.find(x=>x.word===b.dataset.rankWord);if(w)openWordDetail(w)});
}
function renderPatterns(){
 const el=document.getElementById('patternCards');if(!el)return;
 el.innerHTML=GSAT_PATTERN_CARDS.map((p,i)=>`<article class="pattern-card"><div class="pattern-top"><span>${p.tag}</span><b>#${i+1}</b></div><h3>${p.title}</h3><p>${p.note}</p><div class="pattern-example">${p.example}</div><div class="pattern-focus">${p.focus.map(x=>`<span>${x}</span>`).join('')}</div></article>`).join('');
}
function groupMastery(level){
 const words=eligibleBank().filter(w=>w.level===level), chunks=20, size=Math.max(1,Math.ceil(words.length/chunks)), cells=[];
 for(let i=0;i<chunks;i++){const part=words.slice(i*size,(i+1)*size);if(!part.length)continue;const score=part.reduce((s,w)=>s+masteryScore(w.word),0)/part.length;cells.push(Math.round(score))}return cells;
}
function heatClass(n){return n===0?'none':n<40?'low':n<70?'mid':'high'}
function renderMasteryMap(){
 const el=document.getElementById('masteryMap');if(!el)return;
 const levels=[1,2,3,4,5,6,7].filter(l=>eligibleBank().some(w=>w.level===l));
 el.innerHTML=levels.map(level=>{const cells=groupMastery(level),avg=cells.length?Math.round(cells.reduce((a,b)=>a+b,0)/cells.length):0;return `<div class="map-row"><div class="map-label"><b>${level===7?'進階':`L${level}`}</b><small>${avg}%</small></div><div class="heat-row">${cells.map((n,i)=>`<i class="heat ${heatClass(n)}" title="第 ${i+1} 區：${n}%"></i>`).join('')}</div></div>`}).join('');
 const learned=eligibleBank().filter(w=>getProgress(w.word));const avg=learned.length?Math.round(learned.reduce((s,w)=>s+masteryScore(w.word),0)/learned.length):0;document.getElementById('mapMasteryPct').textContent=`${avg}%`;
 const summary=document.getElementById('levelRiskSummary');
 summary.innerHTML=levels.map(level=>{const xs=eligibleBank().filter(w=>w.level===level).map(w=>weaknessScore(w)).sort((a,b)=>b-a);const risk=xs.filter(x=>x>=35).length;return `<div><b>${level===7?'進階':`Level ${level}`}</b><span>${risk} 個高風險字</span></div>`}).join('');
}
function renderAiCoach(){
 const list=document.getElementById('weaknessList');if(!list)return;const top=gsatPriority().slice(0,8);
 const t=document.getElementById('aiCoachTitle'),p=document.getElementById('aiCoachText');
 if(!Object.keys(state.progress).length&&!Object.keys(state.mistakes).length){t.textContent='先建立你的學習樣本';p.textContent='先完成一回單字學習或測驗。之後系統會把「錯題、快忘記、到期、近年真題字」一起計算。'}else{t.textContent=top[0]?`目前最該補強：${top[0].w.word}`:'目前沒有明顯弱點';p.textContent=top[0]?`它的弱點優先度是 ${top[0].score}。系統會優先用情境克漏、近義辨析與拼字交叉檢查，而不是一直重複同一種題型。`:'繼續維持複習節奏即可。'}
 list.innerHTML=top.length?top.map(x=>`<div class="weak-row"><div><b>${x.w.word}</b><small>${x.w.meaning}</small></div><div class="weak-bar"><i style="width:${Math.min(100,x.score)}%"></i></div><span>${x.score}</span></div>`).join(''):'<div class="empty-state">尚未累積足夠的學習紀錄。</div>';
}
function renderInsights(){renderGsatRanking();renderPatterns();renderMasteryMap();renderAiCoach();renderCorpusLab()}
function setInsightTab(tab){document.querySelectorAll('[data-insight-tab]').forEach(b=>b.classList.toggle('active',b.dataset.insightTab===tab));document.querySelectorAll('[data-insight-panel]').forEach(p=>p.classList.toggle('active',p.dataset.insightPanel===tab));if(tab==='map')renderMasteryMap();if(tab==='ai')renderAiCoach();if(tab==='corpus')renderCorpusLab()}
function startAiWeakQuiz(){
 const n=Number(document.getElementById('aiQuizCount')?.value||10), ranked=eligibleBank().map(w=>({w,score:weaknessScore(w)})).sort((a,b)=>b.score-a.score).filter(x=>x.score>8);
 const pool=ranked.slice(0,Math.max(n*3,30)).map(x=>x.w);if(pool.length<4){alert('目前弱點資料還不夠，先完成一些學習或一般測驗。');return}
 quiz=shuffle(pool).slice(0,Math.min(n,pool.length));quizIndex=0;quizScore=0;examMode='gsat';document.getElementById('quizType').value='mixed';showView('quiz');document.getElementById('quizSetup').classList.add('hidden');document.getElementById('quizArea').classList.remove('hidden');showQuiz();
}

function bind(){document.querySelectorAll('.nav-item').forEach(n=>n.onclick=()=>showView(n.dataset.target));document.getElementById('startTodayBtn').onclick=()=>startSession([...getDueWords(),...getNewWords(Number(state.settings.dailyGoal)||20)].slice(0,Number(state.settings.dailyGoal)||20));document.getElementById('startReviewBtn').onclick=()=>startSession(getDueWords());document.getElementById('exitLearnBtn').onclick=()=>showView('home');document.getElementById('showAnswerBtn').onclick=()=>{document.getElementById('answerArea').classList.remove('hidden');document.getElementById('ratingGrid').classList.remove('hidden');document.getElementById('showAnswerBtn').classList.add('hidden')};document.querySelectorAll('.rate').forEach(b=>b.onclick=()=>gradeWord(b.dataset.grade));document.getElementById('speakBtn').onclick=()=>session[sessionIndex]&&speak(session[sessionIndex].word);document.getElementById('learnFavoriteBtn').onclick=()=>{const w=session[sessionIndex];if(!w)return;toggleFavorite(w.word);const b=document.getElementById('learnFavoriteBtn');b.textContent=isFavorite(w.word)?'★':'☆';b.classList.toggle('active',isFavorite(w.word))};document.querySelectorAll('.mode-tab').forEach(b=>b.onclick=()=>setExamMode(b.dataset.exam));document.getElementById('beginQuizBtn').onclick=beginQuiz;document.getElementById('nextQuizBtn').onclick=()=>{quizIndex++;document.getElementById('spellingInput').disabled=false;showQuiz()};document.getElementById('quizSpeakBtn').onclick=()=>quiz[quizIndex]&&speak(quiz[quizIndex].word);document.getElementById('submitSpellingBtn').onclick=submitSpelling;document.getElementById('spellingInput').onkeydown=e=>{if(e.key==='Enter')submitSpelling()};document.getElementById('searchInput').oninput=renderBook;document.getElementById('bookLevel').onchange=renderBook;document.querySelectorAll('[data-book-filter]').forEach(b=>b.onclick=()=>{bookFilter=b.dataset.bookFilter;document.querySelectorAll('[data-book-filter]').forEach(x=>x.classList.toggle('active',x===b));renderBook()});document.getElementById('quizScope').onchange=e=>document.getElementById('customScopeBox').classList.toggle('hidden',e.target.value!=='custom');document.getElementById('customWords').oninput=()=>{const n=makeQuizPool().length;document.getElementById('customScopeStatus').textContent=`目前符合字庫：${n} 字`};document.getElementById('closeDetailBtn').onclick=()=>document.getElementById('wordDetailDialog').close();document.getElementById('detailSpeakBtn').onclick=()=>currentDetailWord&&speak(currentDetailWord.word);document.getElementById('detailExampleSpeak').onclick=()=>currentDetailWord&&speak(detailFor(currentDetailWord).example);document.getElementById('detailFavoriteBtn').onclick=()=>currentDetailWord&&toggleFavorite(currentDetailWord.word);document.getElementById('detailLearnBtn').onclick=()=>{if(!currentDetailWord)return;document.getElementById('wordDetailDialog').close();startSession([currentDetailWord])};document.getElementById('settingsBtn').onclick=()=>document.getElementById('settingsDialog').showModal();document.getElementById('saveSettingsBtn').onclick=()=>{state.settings.dailyGoal=Math.max(5,Math.min(100,Number(document.getElementById('dailyGoal').value)||20));state.settings.mode=document.getElementById('studyMode').value;state.settings.autoSpeak=document.getElementById('autoSpeak').checked;const ez=document.getElementById('showExampleZh');state.settings.showExampleZh=ez?ez.checked:true;saveState();renderAll()};document.getElementById('practiceMistakesBtn').onclick=()=>{document.getElementById('quizScope').value='mistakes';showView('quiz')};document.getElementById('practiceFavoritesBtn').onclick=()=>{document.getElementById('quizScope').value='favorites';showView('quiz')};document.getElementById('exportBtn').onclick=()=>{const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='高中英文7000字-學習紀錄.json';a.click();URL.revokeObjectURL(a.href)};document.getElementById('importInput').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{state={...loadState(),...JSON.parse(await f.text())};saveState();renderAll();alert('匯入完成')}catch{alert('檔案格式不正確')}};document.getElementById('resetBtn').onclick=()=>{if(confirm('確定清除所有學習進度？')){localStorage.removeItem(STORAGE_KEY);location.reload()}};document.getElementById('openInsightsBtn').onclick=()=>showView('insights');document.getElementById('exitInsightsBtn').onclick=()=>showView('home');document.querySelectorAll('[data-insight-tab]').forEach(b=>b.onclick=()=>setInsightTab(b.dataset.insightTab));document.getElementById('startAiQuizBtn').onclick=startAiWeakQuiz;document.getElementById('corpusSearchBtn').onclick=searchCorpusWord;document.getElementById('corpusSearchInput').onkeydown=e=>{if(e.key==='Enter')searchCorpusWord()}}
if('serviceWorker' in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js'));
bind();loadCorpusData();loadWordExamples();loadWordDetails();loadBank();
