// DateSelector.js: 年/月/日下拉
(function(global){
  function renderDateSelector(containerSelector, opts){
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const section = document.createElement('div'); section.className='section';
    const ySel = document.createElement('select'); const mSel = document.createElement('select'); const dSel = document.createElement('select');
    const yLab = document.createElement('label'); yLab.textContent='年';
    const mLab = document.createElement('label'); mLab.textContent='月';
    const dLab = document.createElement('label'); dLab.textContent='日';
    section.append(yLab,ySel,mLab,mSel,dLab,dSel); container.appendChild(section);

    const now = new Date();
    const y0 = (opts?.minYear)|| (now.getFullYear()-5), y1 = (opts?.maxYear)|| (now.getFullYear()+5);
    for(let y=y0; y<=y1; y++){ const o=document.createElement('option'); o.value=y; o.textContent=y; ySel.appendChild(o); }
    for(let m=1; m<=12; m++){ const o=document.createElement('option'); o.value=m; o.textContent=m; mSel.appendChild(o); }
    function fillDays(){ const y=parseInt(ySel.value), m=parseInt(mSel.value); const days=new Date(y,m,0).getDate(); dSel.innerHTML=''; for(let d=1; d<=days; d++){ const o=document.createElement('option'); o.value=d; o.textContent=d; dSel.appendChild(o);} }
    ySel.addEventListener('change', ()=>{ fillDays(); container.dispatchEvent(new CustomEvent('date-change',{detail:getDate()})); });
    mSel.addEventListener('change', ()=>{ fillDays(); container.dispatchEvent(new CustomEvent('date-change',{detail:getDate()})); });
    dSel.addEventListener('change', ()=>{ container.dispatchEvent(new CustomEvent('date-change',{detail:getDate()})); });

    function initToNow(){ ySel.value=now.getFullYear(); mSel.value=now.getMonth()+1; fillDays(); dSel.value=now.getDate(); }
    function getDate(){ return { year: parseInt(ySel.value), month: parseInt(mSel.value), day: parseInt(dSel.value) }; }
    initToNow();
    return { getDate };
  }
  global.DateSelector = { renderDateSelector };
})(window);