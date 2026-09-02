# 공유용 스토리보드 뷰어(storyboard_share.html) 빌드 스크립트
# 사용법: python3 build_share.py  (storyboard 폴더에서 실행)
import json

CSS = open('screen.css', encoding='utf-8').read()
JS = open('screen.js', encoding='utf-8').read()

SCREENS = [
    ('인증·온보딩', 'ONB-00', '초대 이메일', 'onb-00.html'),
    (None, 'ONB-01', '계정 활성화', 'onb-01.html'),
    (None, 'AUTH-01', '로그인', 'auth-01.html'),
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

# IA(정보구조)·표기 규칙·상태 전이 — 자립형 문서, navigate postMessage는 뷰어 리스너가 그대로 처리
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
.main{flex:1;height:100vh;overflow-y:auto;position:relative;}
.main.proc-mode{overflow:hidden;}
#frame{display:block;width:100%;border:0;background:#fafafa;min-height:200px;}
.main.proc-mode #frame{height:100vh;}
</style>
<div class="sidebar">
  <div class="sb-head">
    <h1>교환·중개 화면기획<br>스토리보드</h1>
    <div class="sub">화면 19개 + IA·표기 규칙(공통 UI 규격)·프로세스맵·상태 전이 · 2026-09-02 기준</div>
    <span class="tag">내부 검토용 초안 — 제출용 아님</span>
  </div>
  <div class="sb-list" id="sbList">
    <button class="nav proc" data-ia="1"><span class="nid">◫</span><span>IA (정보구조)</span></button>
    <button class="nav proc" data-gloss="1"><span class="nid">≡</span><span>표기 규칙 · 공통 UI 규격</span></button>
    <button class="nav proc" data-states="1"><span class="nid">⇄</span><span>상태 전이 (처리함)</span></button>
    <button class="nav proc" data-proc="1"><span class="nid">◈</span><span>화면 흐름도 (프로세스맵)</span></button>
  </div>
</div>
<div class="main" id="main"><iframe id="frame" title="화면 미리보기"></iframe></div>
<script>
const NAV=__NAV__;
const FILES=__FILES__;
const CSS=__CSS__;
const JS=__JS__;
const PROC=__PROC__;
const IA=__IA__;
const GLOSS=__GLOSS__;
const STATES=__STATES__;
function inlineDoc(name){
  let d=FILES[name];if(!d)return '';
  d=d.replace('\\u003clink rel="stylesheet" href="screen.css">','\\u003cstyle>'+CSS+'\\u003c/style>');
  d=d.replace('\\u003cscript src="screen.js">\\u003c/script>','\\u003cscript>'+JS+'\\u003c/script>');
  return d;
}
const DOCS={};for(const k in FILES)DOCS[k]=inlineDoc(k);
const frame=document.getElementById('frame');
const main=document.getElementById('main');
const list=document.getElementById('sbList');
let currentPid=null,procMode=false;
NAV.forEach(it=>{
  if(it.group){const g=document.createElement('div');g.className='grp';g.textContent=it.group;list.appendChild(g);}
  const b=document.createElement('button');b.className='nav';b.dataset.pid=it.id;
  const nid=document.createElement('span');nid.className='nid';nid.textContent=it.id;
  const nm=document.createElement('span');nm.textContent=it.name;
  b.append(nid,nm);
  b.onclick=()=>showScreen(it.id);
  list.appendChild(b);
});
function setActive(sel){
  list.querySelectorAll('.nav').forEach(n=>n.classList.remove('active'));
  if(sel)sel.classList.add('active');
}
function showScreen(pid){
  const it=NAV.find(x=>x.id===pid);if(!it)return;
  currentPid=pid;procMode=false;
  main.classList.remove('proc-mode');frame.style.height='200px';
  frame.srcdoc=DOCS[it.file];
  setActive(list.querySelector('.nav[data-pid="'+pid+'"]'));
  main.scrollTop=0;
}
function showDoc(doc,btn){
  procMode=true;main.classList.add('proc-mode');frame.style.height='';
  frame.srcdoc=doc;
  setActive(btn);
}
const procBtn=list.querySelector('.nav[data-proc]');
const iaBtn=list.querySelector('.nav[data-ia]');
const glossBtn=list.querySelector('.nav[data-gloss]');
const statesBtn=list.querySelector('.nav[data-states]');
procBtn.onclick=()=>showDoc(PROC,procBtn);
iaBtn.onclick=()=>showDoc(IA,iaBtn);
glossBtn.onclick=()=>showDoc(GLOSS,glossBtn);
statesBtn.onclick=()=>showDoc(STATES,statesBtn);
frame.addEventListener('load',()=>{
  if(procMode&&frame.contentWindow){
    frame.contentWindow.postMessage({type:'screenDocs',docs:DOCS},'*');
    if(currentPid)frame.contentWindow.postMessage({type:'highlightPage',pid:currentPid},'*');
  }
});
window.addEventListener('message',e=>{
  if(!e.data)return;
  if(e.data.type==='iframeHeight'&&!procMode&&e.data.h>50){frame.style.height=e.data.h+'px';}
  if(e.data.type==='navigate'&&e.data.pageId){showScreen(e.data.pageId);}
});
showScreen('ONB-00');
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
