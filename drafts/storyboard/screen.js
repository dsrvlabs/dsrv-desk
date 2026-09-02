// DSRV 교환·중개 화면기획 — 공통 인터랙션 (영역 브래킷 · 핀↔항목↔상세 연결선 · 클릭 하이라이트 · iframe 높이)
function drawBrackets(){
  const zones=[...document.querySelectorAll('.frame .zone')];
  const labels=[...document.querySelectorAll('.lbl')];
  const svg=document.getElementById('bracketSvg');
  if(!zones.length||!svg) return;
  let totalH=0;
  zones.forEach((z,i)=>{ const h=z.offsetHeight; if(labels[i]) labels[i].style.height=h+'px'; totalH+=h; });
  svg.setAttribute('height',totalH); svg.innerHTML='';
  const mk=(tag,attrs)=>{const el=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v));return el;};
  let y=0;
  zones.forEach((z)=>{ const h=z.offsetHeight; const top=y+6,bot=y+h-6,x=4;
    svg.appendChild(mk('line',{x1:x,y1:top,x2:x,y2:bot,stroke:'#bbb','stroke-width':'1'}));
    svg.appendChild(mk('line',{x1:x,y1:top,x2:x+8,y2:top,stroke:'#bbb','stroke-width':'1'}));
    svg.appendChild(mk('line',{x1:x,y1:bot,x2:x+8,y2:bot,stroke:'#bbb','stroke-width':'1'}));
    y+=h;
  });
}
function drawConnectors(){
  const svg=document.getElementById('connSvg'); const main=document.querySelector('.main');
  if(!svg||!main) return; svg.innerHTML=''; const mRect=main.getBoundingClientRect();
  document.querySelectorAll('.pin').forEach(pin=>{
    const idx=pin.dataset.idx; const itm=document.querySelector(`.itm[data-idx="${idx}"]`); if(!itm) return;
    const pRect=pin.getBoundingClientRect(); const iRect=itm.querySelector('.num').getBoundingClientRect();
    if(iRect.left<pRect.right) return; // 좁은 창에서 항목 컬럼이 프레임 아래로 접히면 연결선 생략
    const line=document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1',pRect.right-mRect.left+4); line.setAttribute('y1',pRect.top+pRect.height/2-mRect.top);
    line.setAttribute('x2',iRect.left-mRect.left-4); line.setAttribute('y2',iRect.top+iRect.height/2-mRect.top);
    line.setAttribute('stroke','#ccc'); line.setAttribute('stroke-width','1'); line.setAttribute('stroke-dasharray','4,3'); line.setAttribute('data-idx',idx);
    svg.appendChild(line);
  });
}
let activeIdx=null;
function selectItem(idx,fromTop){
  if(activeIdx===idx){clearSelection();return;} clearSelection(); activeIdx=idx;
  const pin=document.querySelector(`.pin[data-idx="${idx}"]`); if(pin) pin.classList.add('active');
  const area=document.querySelector(`.item-area[data-highlight="${idx}"]`); if(area) area.style.outline='2px solid #2563eb';
  document.querySelectorAll('.zone').forEach(z=>{ const list=(z.dataset.idx||'').split(',').filter(Boolean); if(list.length===1&&list.includes(String(idx))) z.classList.add('active'); });
  const itm=document.querySelector(`.itm[data-idx="${idx}"]`); if(itm) itm.classList.add('active');
  const dtl=document.querySelector(`.dtl[data-idx="${idx}"]`); if(dtl){dtl.classList.add('active'); if(fromTop&&dtl.closest('.detail-grid')) dtl.scrollIntoView({block:'nearest',behavior:'smooth'});}
  const line=document.querySelector(`#connSvg line[data-idx="${idx}"]`); if(line){line.setAttribute('stroke','#2563eb');line.setAttribute('stroke-width','1.5');}
  followPanel(true);
}
function clearSelection(){
  activeIdx=null;
  document.querySelectorAll('.pin.active').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.zone.active').forEach(z=>z.classList.remove('active'));
  document.querySelectorAll('.itm.active').forEach(i=>i.classList.remove('active'));
  document.querySelectorAll('.dtl.active').forEach(d=>d.classList.remove('active'));
  document.querySelectorAll('.item-area').forEach(a=>a.style.outline='none');
  document.querySelectorAll('#connSvg line').forEach(l=>{l.setAttribute('stroke','#ccc');l.setAttribute('stroke-width','1');});
  followPanel(true);
}
document.addEventListener('click',(e)=>{
  const pin=e.target.closest('.pin'); const itm=e.target.closest('.itm'); const dtl=e.target.closest('.dtl');
  if(pin){selectItem(pin.dataset.idx,true);return;}
  if(itm&&itm.dataset.idx!==undefined){selectItem(itm.dataset.idx,true);return;}
  if(dtl&&dtl.dataset.idx!==undefined){selectItem(dtl.dataset.idx);return;}
  if(!e.target.closest('.zone')&&!e.target.closest('.itm')&&!e.target.closest('.dtl')) clearSelection();
});
function relayout(){drawBrackets();drawConnectors();reportH();followPanel(false);}
function reportH(){var h=Math.max(document.documentElement.scrollHeight,document.body.scrollHeight);window.parent&&window.parent.postMessage({type:"iframeHeight",h:h},"*");}
window.addEventListener('load',()=>{relayout();setTimeout(relayout,300);setTimeout(relayout,900);});
window.addEventListener('resize',relayout);

// ── 목업 패널 따라오기 ──
// 화면은 콘텐츠 높이만큼 늘어난 iframe이라 CSS sticky가 통하지 않는다. 뷰어(index.html · storyboard_share.html)가
// 스크롤마다 보이는 영역({type:'viewport', top, height} · top = iframe 문서 기준 보이는 영역의 위쪽)을 보내고,
// 여기서 .screen-panel을 translateY로 그 영역 안에 붙인다. 단독으로 열면 window 스크롤을 그대로 쓴다.
// 항목·핀·상세 카드를 선택하면(activeIdx) 패널이 뷰포트보다 클 때 그 항목의 프레임 영역이 보이도록 맞춘다.
let vp=null,snapTimer=null;
function followPanel(snap){
  const main=document.querySelector('.main'),panel=document.querySelector('.screen-panel'),items=document.querySelector('.items');
  if(!main||!panel||!vp)return;
  panel.style.transform='';
  const sy=window.scrollY||0,top=r=>r.top+sy;
  const mR=main.getBoundingClientRect(),pR=panel.getBoundingClientRect();
  const mainTop=top(mR),mainBot=mainTop+mR.height,panelTop=top(pR),panelH=pR.height;
  if(items){const iR=items.getBoundingClientRect(); if(top(iR)>=panelTop+panelH-1){drawConnectors();return;}} // 좁은 창: 항목 컬럼이 프레임 아래로 접힘 → 고정 안 함
  const pad=12,vTop=vp.top,vH=vp.height;
  let T;
  if(panelH+pad*2<=vH){ T=vTop+pad; }
  else{
    const lo=vTop+vH-panelH-pad,hi=vTop+pad; // 패널이 뷰포트보다 큼: 위·아래 여백이 생기지 않는 범위
    let anchor=null;
    if(activeIdx!=null){const a=document.querySelector(`.item-area[data-highlight="${activeIdx}"]`)||document.querySelector(`.pin[data-idx="${activeIdx}"]`); if(a)anchor=top(a.getBoundingClientRect())-panelTop;}
    if(anchor!=null){ T=vTop+pad+40-anchor; }
    else{ // 선택 없음: 항목 컬럼 진행률에 따라 패널을 위→아래로 훑어 보인다
      const travel=Math.max(1,(mainBot-panelH)-panelTop); const p=Math.min(1,Math.max(0,(vTop-panelTop)/travel));
      T=hi-p*(hi-lo);
    }
    T=Math.min(hi,Math.max(lo,T));
  }
  T=Math.min(T,mainBot-panelH); T=Math.max(T,panelTop);
  const y=Math.round(T-panelTop);
  if(snap){panel.classList.add('snap');clearTimeout(snapTimer);snapTimer=setTimeout(()=>panel.classList.remove('snap'),350);}
  panel.style.transform=y?`translateY(${y}px)`:'';
  if(snap){setTimeout(drawConnectors,360);} drawConnectors();
}
window.addEventListener('message',e=>{if(e.data&&e.data.type==='viewport'){vp={top:e.data.top,height:e.data.height};followPanel(false);}});
if(window.parent===window){
  const own=()=>{vp={top:window.scrollY,height:window.innerHeight};followPanel(false);};
  window.addEventListener('scroll',own,{passive:true});window.addEventListener('resize',own);window.addEventListener('load',own);
}

// ── 목업 인터랙션 (어드민 화면 — 행 확장 · 드롭다운 · 관리 메뉴 이동) ──
function mkCloseMenus(){document.querySelectorAll('.mk-menu').forEach(m=>m.hidden=true);}
function mkToggleRow(row){
  const key=row.dataset.exp; const wasOpen=row.classList.contains('open');
  document.querySelectorAll('.mk-row.open').forEach(r=>r.classList.remove('open'));
  document.querySelectorAll('.mk-exp').forEach(x=>x.hidden=true);
  if(!wasOpen){row.classList.add('open');
    const exp=document.querySelector('.mk-exp[data-exp="'+key+'"]'); if(exp)exp.hidden=false;}
  document.querySelectorAll('.mk-row').forEach(r=>{const c=r.querySelector('.mk-caret'); if(c)c.textContent=r.classList.contains('open')?'▼':'▶';});
  relayout();
}
function mkPick(op){
  const dd=op.closest('.mk-dd'); const menu=op.closest('.mk-menu');
  menu.hidden=true;
  const host=dd.parentElement; host.querySelectorAll('.mk-hint').forEach(h=>h.remove());
  if(op.dataset.set){
    const lab=dd.querySelector('.mk-lab'); if(lab)lab.textContent=op.dataset.set;
    menu.querySelectorAll('.op').forEach(o=>o.classList.toggle('cur',o===op));
    if(op.hasAttribute('data-dirty')){const t=dd.querySelector('.inp'); if(t)t.classList.add('mk-dirty');}
  }
  if(op.dataset.hint){const s=document.createElement('span');s.className='mk-hint';s.textContent=op.dataset.hint;dd.insertAdjacentElement('afterend',s);}
  relayout();
}
document.addEventListener('click',(e)=>{
  if(e.target.closest('.pin')) return;                      // 핀 클릭은 항목 선택 전용
  const op=e.target.closest('.mk-menu .op'); if(op){mkPick(op);return;}
  const dd=e.target.closest('.mk-dd');
  if(dd){const m=dd.querySelector('.mk-menu'); const willOpen=m&&m.hidden; mkCloseMenus(); if(m)m.hidden=!willOpen; relayout(); return;}
  mkCloseMenus();
  const go=e.target.closest('[data-go]');
  if(go){window.parent&&window.parent.postMessage({type:'navigate',pageId:go.dataset.go},'*');return;}
  if(e.target.closest('.act,.field,.btn,.dl')) return;   // 처리 버튼·입력은 행 확장 대상 아님
  const row=e.target.closest('.mk-row'); if(row){mkToggleRow(row);return;}
});
document.addEventListener('keydown',(e)=>{if(e.key==='Escape')mkCloseMenus();});
