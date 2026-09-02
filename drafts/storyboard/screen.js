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
}
function clearSelection(){
  activeIdx=null;
  document.querySelectorAll('.pin.active').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.zone.active').forEach(z=>z.classList.remove('active'));
  document.querySelectorAll('.itm.active').forEach(i=>i.classList.remove('active'));
  document.querySelectorAll('.dtl.active').forEach(d=>d.classList.remove('active'));
  document.querySelectorAll('.item-area').forEach(a=>a.style.outline='none');
  document.querySelectorAll('#connSvg line').forEach(l=>{l.setAttribute('stroke','#ccc');l.setAttribute('stroke-width','1');});
}
document.addEventListener('click',(e)=>{
  const pin=e.target.closest('.pin'); const itm=e.target.closest('.itm'); const dtl=e.target.closest('.dtl');
  if(pin){selectItem(pin.dataset.idx,true);return;}
  if(itm&&itm.dataset.idx!==undefined){selectItem(itm.dataset.idx,true);return;}
  if(dtl&&dtl.dataset.idx!==undefined){selectItem(dtl.dataset.idx);return;}
  if(!e.target.closest('.zone')&&!e.target.closest('.itm')&&!e.target.closest('.dtl')) clearSelection();
});
function relayout(){drawBrackets();drawConnectors();reportH();}
function reportH(){var h=Math.max(document.documentElement.scrollHeight,document.body.scrollHeight);window.parent&&window.parent.postMessage({type:"iframeHeight",h:h},"*");}
window.addEventListener('load',()=>{relayout();setTimeout(relayout,300);setTimeout(relayout,900);});
window.addEventListener('resize',relayout);
