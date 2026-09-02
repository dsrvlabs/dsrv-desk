# 공유용 스토리보드 뷰어(storyboard_share.html) 빌드 스크립트
# 사용법: python3 build_share.py  (storyboard 폴더에서 실행)
import json

CSS = open('screen.css', encoding='utf-8').read()
JS = open('screen.js', encoding='utf-8').read()

SCREENS = [
    ('인증·온보딩', 'ONB-00', '초대 이메일', 'onb-00.html'),
    (None, 'ONB-01', '활성화 · 비밀번호 설정', 'onb-01.html'),
    (None, 'ONB-02', '활성화 · 2FA 앱 연결', 'onb-02.html'),
    (None, 'ONB-03', '활성화 · 복구 코드 저장', 'onb-03.html'),
    (None, 'ONB-04', '초대 링크 오류', 'onb-04.html'),
    (None, 'AUTH-01', '로그인', 'auth-01.html'),
    (None, 'AUTH-02', '2차 인증', 'auth-02.html'),
    ('대시보드', 'DASH-01', '대시보드', 'dash-01.html'),
    (None, 'DASH-02', '비밀번호 수정', 'dash-02.html'),
    (None, 'DASH-03', '2차 인증 재설정', 'dash-03.html'),
    ('나목 교환 (DSRV 자산과 교환)', 'EXC-01', '교환하기', 'exc-01.html'),
    (None, 'EXC-02', '비율 확인·수락', 'exc-02.html'),
    (None, 'EXC-03', '승인 진행', 'exc-03.html'),
    (None, 'EXC-04', '내역·완료', 'exc-04.html'),
    ('마목 중개 — 게시(RFQ 등록)', 'BRK-01', '교환 게시판', 'brk-01.html'),
    (None, 'BRK-02', '거래의향 등록', 'brk-02.html'),
    (None, 'BRK-06', '내 게시 상세·회수', 'brk-06.html'),
    ('마목 중개 — 신청·수락(기존 RFQ 거래)', 'BRK-03', '신청하기', 'brk-03.html'),
    (None, 'BRK-07', '내 신청 상세', 'brk-07.html'),
    (None, 'BRK-04', '받은 신청·수락', 'brk-04.html'),
    (None, 'BRK-05', '이전·완료', 'brk-05.html'),
    ('관리자 (DSRV Admin)', 'ADM-02', '어드민 홈', 'adm-02.html'),
    (None, 'ADM-03', '설정', 'adm-03.html'),
]

files = {f: open(f, encoding='utf-8').read() for _, _, _, f in SCREENS}

# process.html 패치: 호버 섬네일을 srcdoc 방식으로, 부모가 넘긴 문서맵 수신
proc = open('process.html', encoding='utf-8').read()
old_thumb = 'if(src!==currentSrc){floatIframe.src=src;currentSrc=src;}'
assert old_thumb in proc, 'thumb hook not found — process.html 구조 변경됨'
proc = proc.replace(
    old_thumb,
    "if(src!==currentSrc){floatIframe.removeAttribute('src');"
    "floatIframe.srcdoc=(window.SCREEN_DOCS&&window.SCREEN_DOCS[src])||'';currentSrc=src;}")
proc = proc.replace(
    '</body>',
    "<script>window.addEventListener('message',function(e){"
    "if(e.data&&e.data.type==='screenDocs')window.SCREEN_DOCS=e.data.docs;});</script>\n</body>", 1)

# IA(정보구조)·표기 규칙·케이스분기 — 자립형 문서, navigate postMessage는 뷰어 리스너가 그대로 처리
IA = open('ia.html', encoding='utf-8').read()
GLOSS = open('notation.html', encoding='utf-8').read()
STATES = open('states.html', encoding='utf-8').read()


def js_str(obj):
    # 인라인 <script> 안에 안전하게 넣기 위해 모든 '<'를 \u003c로 이스케이프
    # (</script>, <script, <!-- 가 HTML 파서를 깨뜨리는 것을 원천 차단)
    return json.dumps(obj, ensure_ascii=False).replace('<', '\\u003c')


nav_items = [{'group': g, 'id': i, 'name': n, 'file': f} for g, i, n, f in SCREENS]

viewer = """<title>교환·중개 화면기획 스토리보드</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');
:root{--bg:#f4f5f3;--panel:#ffffff;--line:#e3e6e2;--ink:#1e293b;--muted:#64748b;--accent:#1d4ed8;--accent-bg:#eff6ff;--mono:ui-monospace,'SF Mono',Consolas,monospace;}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;}
body{font-family:'Noto Sans KR',system-ui,sans-serif;background:var(--bg);color:var(--ink);display:flex;overflow:hidden;}
.sidebar{width:236px;flex-shrink:0;background:var(--panel);border-right:1px solid var(--line);display:flex;flex-direction:column;height:100vh;}
.sb-head{padding:16px 16px 12px;border-bottom:1px solid var(--line);}
.sb-head h1{font-size:14px;font-weight:800;line-height:1.35;}
.sb-head .sub{font-size:10.5px;color:var(--muted);margin-top:4px;}
.sb-head .tag{display:inline-block;margin-top:6px;font-size:9.5px;font-weight:700;color:#92400e;background:#fef9ec;border:1px solid #fde68a;padding:1px 7px;border-radius:8px;}
.sb-list{flex:1;overflow-y:auto;padding:8px 0 20px;}
.sb-list::-webkit-scrollbar{width:4px;}.sb-list::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:2px;}
.grp{font-size:10px;font-weight:800;color:var(--muted);letter-spacing:.04em;padding:14px 16px 5px;}
.nav{display:flex;align-items:baseline;gap:7px;width:100%;text-align:left;border:0;background:none;font-family:inherit;cursor:pointer;padding:6px 16px;font-size:12px;color:var(--ink);border-left:3px solid transparent;}
.nav:hover{background:#f8fafc;}
.nav.active{background:var(--accent-bg);border-left-color:var(--accent);font-weight:700;color:var(--accent);}
.nav .nid{font-family:var(--mono);font-size:9.5px;color:var(--muted);flex-shrink:0;width:52px;}
.nav.active .nid{color:var(--accent);}
.nav.proc{font-weight:700;padding:9px 16px;}
.nav.proc .nid{width:auto;}
.main{flex:1;height:100vh;overflow-y:auto;position:relative;background:#fafafa;}
.sec{border-bottom:2px solid #e0e0e0;position:relative;}
.sec iframe{display:block;width:100%;border:0;background:#fafafa;height:480px;}
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:2000;padding:28px;}
.overlay.active{display:flex;flex-direction:column;}
.ov-head{display:flex;justify-content:space-between;align-items:center;padding:9px 16px;background:#0f172a;border-radius:8px 8px 0 0;color:#fff;}
.ov-title{font-size:13px;font-weight:700;}
.ov-close{background:none;border:0;color:#fff;font-size:20px;cursor:pointer;padding:4px 8px;line-height:1;}
.ov-close:hover{opacity:.7;}
.overlay iframe{flex:1;width:100%;border:0;background:#fafafa;border-radius:0 0 8px 8px;}
</style>
<div class="sidebar">
  <div class="sb-head">
    <h1>교환·중개 화면기획<br>스토리보드</h1>
    <div class="sub">화면 21개 + IA·표기 규칙(공통 UI 규격)·프로세스맵·케이스분기 · 2026-09-02 기준</div>
    <span class="tag">내부 검토용 초안 — 제출용 아님</span>
  </div>
  <div class="sb-list" id="sbList">
    <button class="nav proc" data-doc="ia"><span class="nid">◫</span><span>IA (정보구조)</span></button>
    <button class="nav proc" data-doc="gloss"><span class="nid">≡</span><span>표기 규칙 · 공통 UI 규격</span></button>
    <button class="nav proc" data-doc="states"><span class="nid">⇄</span><span>케이스분기</span></button>
    <button class="nav proc" data-doc="proc"><span class="nid">◈</span><span>화면 흐름도 (프로세스맵)</span></button>
  </div>
</div>
<div class="main" id="main"></div>
<div class="overlay" id="overlay">
  <div class="ov-head"><span class="ov-title" id="ovTitle"></span><button class="ov-close" id="ovClose" title="닫기">&times;</button></div>
  <iframe id="ovFrame" title="문서"></iframe>
</div>
<script>
const NAV=__NAV__;
const FILES=__FILES__;
const CSS=__CSS__;
const JS=__JS__;
const DOCS_EXTRA={proc:{title:'화면 흐름도 — DSRV 교환·중개',html:__PROC__},ia:{title:'IA (정보구조) — DSRV 교환·중개',html:__IA__},gloss:{title:'표기 규칙 · 공통 UI 규격 — DSRV 교환·중개',html:__GLOSS__},states:{title:'케이스분기 — 거래·계정 상태 분기와 화면 반영 · DSRV 교환·중개',html:__STATES__}};
function inlineDoc(name){
  let d=FILES[name];if(!d)return '';
  d=d.replace('\\u003clink rel="stylesheet" href="screen.css">','\\u003cstyle>'+CSS+'\\u003c/style>');
  d=d.replace('\\u003cscript src="screen.js">\\u003c/script>','\\u003cscript>'+JS+'\\u003c/script>');
  return d;
}
const DOCS={};for(const k in FILES)DOCS[k]=inlineDoc(k);
const main=document.getElementById('main');
const list=document.getElementById('sbList');
const overlay=document.getElementById('overlay');
const ovFrame=document.getElementById('ovFrame');
const ovTitle=document.getElementById('ovTitle');
const winToFrame=new WeakMap();
const navBtn={};
let currentPid=null,openDoc=null;
NAV.forEach(it=>{
  if(it.group){const g=document.createElement('div');g.className='grp';g.textContent=it.group;list.appendChild(g);}
  const b=document.createElement('button');b.className='nav';b.dataset.pid=it.id;
  const nid=document.createElement('span');nid.className='nid';nid.textContent=it.id;
  const nm=document.createElement('span');nm.textContent=it.name;
  b.append(nid,nm);
  b.onclick=()=>goTo(it.id);
  list.appendChild(b);navBtn[it.id]=b;
  const sec=document.createElement('section');sec.className='sec';sec.id='sec-'+it.id;
  const f=document.createElement('iframe');f.title=it.id+' '+it.name;f.setAttribute('scrolling','no');
  f.addEventListener('load',()=>{if(f.contentWindow)winToFrame.set(f.contentWindow,f);scheduleVP();});
  f.srcdoc=DOCS[it.file];
  sec.appendChild(f);main.appendChild(sec);
});
function goTo(pid){
  closeDoc();
  const sec=document.getElementById('sec-'+pid);
  if(sec)sec.scrollIntoView({behavior:'smooth',block:'start'});
}
const obs=new IntersectionObserver(entries=>{
  entries.forEach(en=>{
    const pid=en.target.id.slice(4);const b=navBtn[pid];if(!b)return;
    if(en.isIntersecting){currentPid=pid;b.classList.add('active');b.scrollIntoView({block:'nearest'});}
    else b.classList.remove('active');
  });
},{root:main,rootMargin:'0px 0px -60% 0px',threshold:0});
main.querySelectorAll('.sec').forEach(s=>obs.observe(s));
function showDoc(key){
  const d=DOCS_EXTRA[key];if(!d)return;
  openDoc=key;ovTitle.textContent=d.title;ovFrame.srcdoc=d.html;overlay.classList.add('active');
}
function closeDoc(){openDoc=null;overlay.classList.remove('active');ovFrame.removeAttribute('srcdoc');}
list.querySelectorAll('.nav[data-doc]').forEach(b=>{b.onclick=()=>showDoc(b.dataset.doc);});
document.getElementById('ovClose').onclick=closeDoc;
overlay.addEventListener('click',e=>{if(e.target===overlay)closeDoc();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDoc();});
ovFrame.addEventListener('load',()=>{
  if(openDoc==='proc'&&ovFrame.contentWindow){
    ovFrame.contentWindow.postMessage({type:'screenDocs',docs:DOCS},'*');
    if(currentPid)ovFrame.contentWindow.postMessage({type:'highlightPage',pid:currentPid},'*');
  }
});
window.addEventListener('message',e=>{
  if(!e.data)return;
  if(e.data.type==='iframeHeight'&&e.data.h>50){const f=winToFrame.get(e.source);if(f){f.style.height=e.data.h+'px';scheduleVP();}}
  if(e.data.type==='navigate'&&e.data.pageId){goTo(e.data.pageId);}
});
// 보이는 영역을 각 화면 iframe에 전달 → 화면 안에서 목업 패널이 따라온다(screen.js followPanel)
function pushViewport(){
  const mr=main.getBoundingClientRect();
  main.querySelectorAll('.sec iframe').forEach(f=>{
    const r=f.getBoundingClientRect();
    if(r.bottom<mr.top-300||r.top>mr.bottom+300)return;
    if(f.contentWindow)f.contentWindow.postMessage({type:'viewport',top:mr.top-r.top,height:mr.height},'*');
  });
}
let vpReq=false;
function scheduleVP(){if(vpReq)return;vpReq=true;requestAnimationFrame(()=>{vpReq=false;pushViewport();});}
main.addEventListener('scroll',scheduleVP,{passive:true});
window.addEventListener('resize',scheduleVP);
</script>
"""

viewer = (viewer
          .replace('__NAV__', js_str(nav_items))
          .replace('__FILES__', js_str(files))
          .replace('__CSS__', js_str(CSS))
          .replace('__JS__', js_str(JS))
          .replace('__PROC__', js_str(proc))
          .replace('__IA__', js_str(IA))
          .replace('__GLOSS__', js_str(GLOSS))
          .replace('__STATES__', js_str(STATES)))

open('storyboard_share.html', 'w', encoding='utf-8').write(viewer)

# 검증: 인라인 스크립트 밖으로 새는 위험 시퀀스가 없어야 함
import re
body = viewer
assert body.count('<script>') == 1 and body.count('</script>') == 1, 'script 태그 불균형'
assert '<!--' not in body, '주석 시퀀스 잔존'
inner = body[body.index('<script>') + 8: body.index('</script>')]
assert '<script' not in inner and '</' not in inner.replace('\\u003c/', ''), '스크립트 내부 위험 시퀀스'
import os
print('OK', os.path.getsize('storyboard_share.html'), 'bytes')
