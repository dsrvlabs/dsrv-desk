# 공유용 스토리보드 뷰어(storyboard_share.html) 빌드 스크립트
# 사용법: python3 build_share.py [--label "이번 버전 설명"]  (storyboard 폴더에서 실행)
#
# 버전 내장(2026-09-03): git 이력에서 storyboard_share.html이 바뀐 커밋마다 그 시점의
# 화면·문서 파일을 blob(sha) 단위로 중복 없이 내장하고, 뷰어 상단 버전 드롭다운으로 골라 본다.
#  - 버전 = 공유본이 바뀐 커밋(오래된 것부터 v1). 작업 트리가 HEAD와 다르면 맨 위에 미커밋 버전 추가.
#  - 용량 예산(BUDGET) 초과 시 오래된 버전부터 제외 → 뷰어 목록에는 포함된 버전만 보인다.
import json, re, ast, os, sys, hashlib, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
REL = 'drafts/storyboard/'          # 레포 루트 기준 이 폴더 경로
SHARE = 'storyboard_share.html'
DOC_FILES = {'ia': 'ia.html', 'gloss': 'notation.html', 'states': 'states.html'}   # process.html 폐기 2026-09-04(18)
BUDGET = 13_000_000                  # 내장 데이터(JSON) 바이트 상한 — 아티팩트 한도 16MB 대비 여유
# 현재 화면 목록(정본) — 화면 추가 시 index.html PAGES·overview.html 흐름·목록·ia.html·notation 화면 ID 표와 함께 갱신
SCREENS = [
    ('시작', 'OVW', '한눈에 보기 — 서비스 · 흐름 · 읽는 법', 'overview.html'),
    ('인증·온보딩', 'ONB-00', '초대 이메일', 'onb-00.html'),
    (None, 'ONB-01', '활성화 · 비밀번호 설정', 'onb-01.html'),
    (None, 'ONB-02', '활성화 · 2FA 앱 연결', 'onb-02.html'),
    (None, 'ONB-03', '활성화 · 복구 코드 저장', 'onb-03.html'),
    (None, 'ONB-04', '초대 링크 오류', 'onb-04.html'),
    (None, 'AUTH-01', '로그인', 'auth-01.html'),
    (None, 'AUTH-02', '2차 인증', 'auth-02.html'),
    (None, 'AUTH-03', '복구 코드로 인증', 'auth-03.html'),
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

CUR_LABEL = None
if '--label' in sys.argv:
    CUR_LABEL = sys.argv[sys.argv.index('--label') + 1]


def git(*args, text=True):
    return subprocess.run(['git', *args], capture_output=True, text=text, check=True).stdout


def parse_screens(src):
    m = re.search(r'^SCREENS\s*=\s*(\[.*?^\])', src, re.S | re.M)
    assert m, 'SCREENS 블록 파싱 실패'
    return ast.literal_eval(m.group(1))


def clean_subject(s):
    s = re.sub(r'\(?\b[0-9a-f]{7,40}\b\)?', '', s)        # 커밋 해시 제거
    s = re.sub(r'\(\s*(ef|72|반영)?\s*\)', '', s)          # 빈 괄호 정리
    s = re.sub(r'\s{2,}', ' ', s).strip(' ·—-')
    return s



BLOBS = {}        # sha → 내용


def put(sha, content):
    if sha not in BLOBS:
        BLOBS[sha] = content
    return sha


def sha_of(content):
    return hashlib.sha1(content.encode('utf-8')).hexdigest()


def make_version(screens, read, date, subject):
    """read(filename) → 내용. 버전 레코드 생성(blob 등록 포함)."""
    files = {}
    for _, _, _, f in screens:
        c = read(f)
        files[f] = put(sha_of(c), c)
    css = read('screen.css'); js = read('screen.js')
    docs = {}
    for k, f in DOC_FILES.items():
        try:
            c = read(f)
        except Exception:
            continue
        docs[k] = put(sha_of(c), c)
    return {
        'date': date, 'subject': subject,
        'nav': [{'group': g, 'id': i, 'name': n, 'file': f} for g, i, n, f in screens],
        'files': files, 'css': put(sha_of(css), css), 'js': put(sha_of(js), js), 'docs': docs,
    }


# ── 1) 커밋 버전(최신순) ─────────────────────────────────────────────
commits = []
for line in git('log', '--format=%H%x09%ci%x09%s', '--', SHARE).splitlines():
    h, ci, subj = line.split('\t', 2)
    commits.append((h, ci[:16], subj))

versions = []
for h, date, subj in commits:
    def read(f, h=h):
        return git('show', f'{h}:{REL}{f}')
    screens = parse_screens(git('show', f'{h}:{REL}build_share.py'))
    v = make_version(screens, read, date, clean_subject(subj))
    v['commit'] = h[:7]
    versions.append(v)

# ── 2) 최신 버전 한 개 더 — 기본은 작업 트리, --head-only면 HEAD 커밋 내용 ─────
#     versions[0]은 storyboard_share.html을 건드린 마지막 커밋이라, 그 뒤에 화면만 바꾼
#     커밋이 있으면 그 내용이 빠진다. 그래서 여기서 맨 앞에 한 버전을 더 얹는다.
HEAD_ONLY = '--head-only' in sys.argv   # 타 세션의 미커밋 편집을 공유본에 섞지 않을 때

def read_wt(f):
    return open(f, encoding='utf-8').read()

def read_head(f):
    return git('show', f'HEAD:{REL}{f}')

if HEAD_ONLY:
    head_h = git('rev-parse', 'HEAD').strip()
    head_date = git('log', '-1', '--format=%ci', 'HEAD').strip()[:16]
    head_subj = clean_subject(git('log', '-1', '--format=%s', 'HEAD').strip())
    cur = make_version(parse_screens(read_head('build_share.py')), read_head,
                       head_date, CUR_LABEL or head_subj)
    cur['commit'] = head_h[:7]
else:
    cur = make_version(SCREENS, read_wt,
                       datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                       CUR_LABEL or '작업 중 (미커밋)')
    cur['commit'] = None

same_as_head = bool(versions) and all(
    versions[0][k] == cur[k] for k in ('files', 'css', 'js', 'docs', 'nav'))
if not same_as_head:
    versions.insert(0, cur)

# ── 3) 번호 부여(오래된 것 = v1) · 용량 예산 ─────────────────────────
total = len(versions)
for idx, v in enumerate(versions):
    v['n'] = total - idx

def js_str(obj):
    # 인라인 <script> 안에 안전하게 넣기 위해 모든 '<'를 \u003c로 이스케이프
    # (</script>, <script, <!-- 가 HTML 파서를 깨뜨리는 것을 원천 차단)
    return json.dumps(obj, ensure_ascii=False).replace('<', '\\u003c')

kept, used_shas, size = [], set(), 0
for v in versions:
    shas = set(v['files'].values()) | {v['css'], v['js']} | set(v['docs'].values())
    add = sum(len(js_str(BLOBS[s])) for s in shas - used_shas) + len(js_str(v))
    if kept and size + add > BUDGET:
        break
    kept.append(v); used_shas |= shas; size += add
dropped = total - len(kept)
BLOBS = {s: BLOBS[s] for s in used_shas}

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
/* 버전 선택 */
.ver{position:relative;margin-top:10px;}
.ver-btn{display:flex;align-items:center;gap:6px;width:100%;border:1px solid var(--line);background:#fff;border-radius:7px;padding:6px 9px;font-family:inherit;font-size:11.5px;color:var(--ink);cursor:pointer;text-align:left;}
.ver-btn:hover{background:#f8fafc;}
.ver-btn .vn{font-family:var(--mono);font-weight:700;color:var(--accent);flex-shrink:0;}
.ver-btn .vd{color:var(--muted);flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ver-btn .caret{font-size:9px;color:var(--muted);flex-shrink:0;}
.ver-menu{display:none;position:absolute;left:0;top:calc(100% + 4px);width:360px;max-height:70vh;overflow-y:auto;background:#fff;border:1px solid var(--line);border-radius:9px;box-shadow:0 10px 30px rgba(15,23,42,.18);z-index:3000;padding:6px;}
.ver-menu.open{display:block;}
.ver-menu .vm-head{font-size:10px;font-weight:800;color:var(--muted);padding:6px 10px 4px;letter-spacing:.04em;}
.ver-item{display:grid;grid-template-columns:38px 1fr;gap:1px 8px;width:100%;text-align:left;border:0;background:none;font-family:inherit;cursor:pointer;padding:7px 10px;border-radius:6px;color:var(--ink);}
.ver-item:hover{background:#f8fafc;}
.ver-item.sel{background:var(--accent-bg);}
.ver-item .vn{font-family:var(--mono);font-size:11px;font-weight:700;color:var(--accent);grid-row:1/3;padding-top:1px;}
.ver-item .vt{font-size:11.5px;font-weight:700;display:flex;gap:6px;align-items:baseline;}
.ver-item .vt .cur{font-size:9.5px;font-weight:700;color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:0 6px;}
.ver-item .vs{font-size:10.5px;color:var(--muted);line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ver-menu .vm-foot{font-size:10px;color:var(--muted);padding:6px 10px 4px;border-top:1px solid var(--line);margin-top:4px;}
.oldbar{position:sticky;top:0;z-index:100;display:flex;align-items:center;gap:10px;padding:8px 16px;background:#fef9ec;border-bottom:1px solid #fde68a;color:#92400e;font-size:11.5px;font-weight:700;}
.oldbar .sub2{font-weight:400;color:#a16207;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.oldbar button{border:1px solid #f59e0b;background:#fff;color:#92400e;border-radius:6px;padding:3px 9px;font-family:inherit;font-size:11px;font-weight:700;cursor:pointer;}
.oldbar button:hover{background:#fffbeb;}
</style>
<div class="sidebar">
  <div class="sb-head">
    <h1>교환·중개 화면기획<br>스토리보드</h1>
    <div class="sub" id="sbSub"></div>
    <span class="tag">내부 검토용 초안 — 제출용 아님</span>
    <div class="ver">
      <button class="ver-btn" id="verBtn" title="버전 선택"><span class="vn" id="verN"></span><span class="vd" id="verD"></span><span class="caret">▼</span></button>
      <div class="ver-menu" id="verMenu"></div>
    </div>
  </div>
  <div class="sb-list" id="sbList"></div>
</div>
<div class="main" id="main"></div>
<div class="overlay" id="overlay">
  <div class="ov-head"><span class="ov-title" id="ovTitle"></span><button class="ov-close" id="ovClose" title="닫기">&times;</button></div>
  <iframe id="ovFrame" title="문서"></iframe>
</div>
<script>
const VERSIONS=__VERSIONS__;   // 최신순
const BLOBS=__BLOBS__;
const DROPPED=__DROPPED__;
const DOC_TITLES={ia:'IA (정보구조) — DSRV 교환·중개',gloss:'표기 규칙 · 공통 UI 규격 — DSRV 교환·중개',states:'케이스분기 — 거래·계정 상태 분기와 화면 반영 · DSRV 교환·중개'};
const DOC_NAV=[['ia','◫','IA (정보구조)'],['gloss','≡','표기 규칙 · 공통 UI 규격'],['states','⇄','케이스분기']];
function inlineDoc(v,name){
  let d=BLOBS[v.files[name]];if(!d)return '';
  d=d.replace('\\u003clink rel="stylesheet" href="screen.css">','\\u003cstyle>'+BLOBS[v.css]+'\\u003c/style>');
  d=d.replace('\\u003cscript src="screen.js">\\u003c/script>','\\u003cscript>'+BLOBS[v.js]+'\\u003c/script>');
  return d;
}
const main=document.getElementById('main');
const list=document.getElementById('sbList');
const overlay=document.getElementById('overlay');
const ovFrame=document.getElementById('ovFrame');
const ovTitle=document.getElementById('ovTitle');
const verBtn=document.getElementById('verBtn'),verMenu=document.getElementById('verMenu');
const winToFrame=new WeakMap();
let navBtn={},DOCS={},V=null,VI=0,obs=null,currentPid=null,openDoc=null;
function verLabel(v){return 'v'+v.n;}
function render(vi){
  closeDoc();
  if(obs)obs.disconnect();
  VI=vi;V=VERSIONS[vi];navBtn={};DOCS={};currentPid=null;
  V.nav.forEach(it=>{DOCS[it.file]=inlineDoc(V,it.file);});
  document.getElementById('sbSub').textContent='화면 '+V.nav.filter(x=>x.id!=='OVW').length+'개 + 한눈에 보기 · IA · 표기 규칙 · 케이스분기 · '+V.date.slice(0,10)+' 기준';
  document.getElementById('verN').textContent=verLabel(V);
  document.getElementById('verD').textContent=V.date+(vi===0?' · 최신':'');
  list.innerHTML='';main.innerHTML='';
  DOC_NAV.forEach(([k,ic,nm])=>{
    if(!V.docs[k])return;
    const b=document.createElement('button');b.className='nav proc';b.dataset.doc=k;
    const a=document.createElement('span');a.className='nid';a.textContent=ic;
    const s=document.createElement('span');s.textContent=nm;b.append(a,s);b.onclick=()=>showDoc(k);list.appendChild(b);
  });
  if(vi!==0){
    const bar=document.createElement('div');bar.className='oldbar';
    const t=document.createElement('span');t.textContent='이전 버전 '+verLabel(V)+' · '+V.date;
    const s=document.createElement('span');s.className='sub2';s.textContent=V.subject||'';
    const btn=document.createElement('button');btn.textContent='최신 버전 보기';btn.onclick=()=>selectVersion(0);
    bar.append(t,s,btn);main.appendChild(bar);
  }
  V.nav.forEach(it=>{
    if(it.group){const g=document.createElement('div');g.className='grp';g.textContent=it.group;list.appendChild(g);}
    const b=document.createElement('button');b.className='nav';b.dataset.pid=it.id;
    const nid=document.createElement('span');nid.className='nid';nid.textContent=it.id;
    const nm=document.createElement('span');nm.textContent=it.name;
    b.append(nid,nm);b.onclick=()=>goTo(it.id);list.appendChild(b);navBtn[it.id]=b;
    const sec=document.createElement('section');sec.className='sec';sec.id='sec-'+it.id;
    const f=document.createElement('iframe');f.title=it.id+' '+it.name;f.setAttribute('scrolling','no');
    f.addEventListener('load',()=>{if(f.contentWindow)winToFrame.set(f.contentWindow,f);scheduleVP();});
    f.srcdoc=DOCS[it.file];
    sec.appendChild(f);main.appendChild(sec);
  });
  obs=new IntersectionObserver(entries=>{
    entries.forEach(en=>{
      const pid=en.target.id.slice(4);const b=navBtn[pid];if(!b)return;
      if(en.isIntersecting){currentPid=pid;b.classList.add('active');b.scrollIntoView({block:'nearest'});}
      else b.classList.remove('active');
    });
  },{root:main,rootMargin:'0px 0px -60% 0px',threshold:0});
  main.querySelectorAll('.sec').forEach(s=>obs.observe(s));
  main.scrollTop=0;
  buildMenu();
  const h=vi===0?'':'#v'+V.n;
  if(location.hash!==h){try{history.replaceState(null,'',location.pathname+location.search+h);}catch(e){}}
}
function buildMenu(){
  verMenu.innerHTML='';
  const hd=document.createElement('div');hd.className='vm-head';hd.textContent='버전 기록 · '+VERSIONS.length+'개';verMenu.appendChild(hd);
  VERSIONS.forEach((v,i)=>{
    const b=document.createElement('button');b.className='ver-item'+(i===VI?' sel':'');
    const n=document.createElement('span');n.className='vn';n.textContent=verLabel(v);
    const t=document.createElement('span');t.className='vt';
    const d=document.createElement('span');d.textContent=v.date;t.appendChild(d);
    if(i===0){const c=document.createElement('span');c.className='cur';c.textContent='최신';t.appendChild(c);}
    const s=document.createElement('span');s.className='vs';s.textContent=v.subject||'';s.title=v.subject||'';
    b.append(n,t,s);b.onclick=()=>selectVersion(i);verMenu.appendChild(b);
  });
  if(DROPPED>0){const ft=document.createElement('div');ft.className='vm-foot';ft.textContent='용량 한도로 오래된 '+DROPPED+'개 버전은 이 문서에 포함되지 않았다(git 이력에는 보존).';verMenu.appendChild(ft);}
}
function selectVersion(i){verMenu.classList.remove('open');if(i!==VI)render(i);}
verBtn.onclick=e=>{e.stopPropagation();verMenu.classList.toggle('open');if(verMenu.classList.contains('open')){const s=verMenu.querySelector('.sel');if(s)s.scrollIntoView({block:'nearest'});}};
document.addEventListener('click',e=>{if(!verMenu.contains(e.target))verMenu.classList.remove('open');});
function goTo(pid){
  closeDoc();
  const sec=document.getElementById('sec-'+pid);
  if(sec)sec.scrollIntoView({behavior:'smooth',block:'start'});
}
function showDoc(key){
  const sha=V.docs[key];if(!sha)return;
  openDoc=key;ovTitle.textContent=DOC_TITLES[key]+(VI!==0?' · '+verLabel(V):'');ovFrame.srcdoc=BLOBS[sha];overlay.classList.add('active');
}
function closeDoc(){openDoc=null;overlay.classList.remove('active');ovFrame.removeAttribute('srcdoc');}
document.getElementById('ovClose').onclick=closeDoc;
overlay.addEventListener('click',e=>{if(e.target===overlay)closeDoc();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeDoc();verMenu.classList.remove('open');}});
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
// 초기 버전: #v12 같은 해시가 있으면 그 버전, 없으면 최신
(function(){
  let vi=0;const m=/^#v(\\d+)$/.exec(location.hash||'');
  if(m){const i=VERSIONS.findIndex(v=>v.n===+m[1]);if(i>=0)vi=i;}
  render(vi);
})();
</script>
"""

viewer = (viewer
          .replace('__VERSIONS__', js_str(kept))
          .replace('__BLOBS__', js_str(BLOBS))
          .replace('__DROPPED__', str(dropped)))

open(SHARE, 'w', encoding='utf-8').write(viewer)

# 검증: 인라인 스크립트 밖으로 새는 위험 시퀀스가 없어야 함
body = viewer
assert body.count('<script>') == 1 and body.count('</script>') == 1, 'script 태그 불균형'
assert '<!--' not in body, '주석 시퀀스 잔존'
inner = body[body.index('<script>') + 8: body.index('</script>')]
assert '<script' not in inner and '</' not in inner.replace('\\u003c/', ''), '스크립트 내부 위험 시퀀스'
print(f'OK {os.path.getsize(SHARE)} bytes · versions {len(kept)}/{total} (dropped {dropped}) · blobs {len(BLOBS)}'
      + ('' if same_as_head else (' · HEAD 버전 얹음' if HEAD_ONLY else ' · 작업 트리 미커밋 버전 포함')))
for v in kept[:5]:
    print(f"  v{v['n']} {v['date']} {v['commit'] or '(wt)'} {v['subject'][:60]}")
