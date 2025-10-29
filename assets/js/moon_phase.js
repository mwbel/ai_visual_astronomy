// 实时月相明暗盘渲染（近似模型）
(function(){
  const canvas = document.getElementById('moon');
  const ctx = canvas.getContext('2d');
  const dateEl = document.getElementById('date');
  const timeEl = document.getElementById('time');
  const nowBtn = document.getElementById('nowBtn');
  const renderBtn = document.getElementById('renderBtn');
  const illumEl = document.getElementById('illum');
  const phaseNameEl = document.getElementById('phaseName');
  const ageEl = document.getElementById('age');

  function setNow(){
    const now = new Date();
    dateEl.value = now.toISOString().slice(0,10);
    timeEl.value = now.toTimeString().slice(0,5);
  }
  function resize(){
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.floor(rect.width);
    canvas.height = Math.floor(rect.height);
  }

  function drawMoon(fraction, waxing){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    const grad = ctx.createLinearGradient(0,0,0,canvas.height);
    grad.addColorStop(0,'#0c1220'); grad.addColorStop(1,'#0a0d12');
    ctx.fillStyle = grad; ctx.fillRect(0,0,canvas.width,canvas.height);

    const cx = canvas.width/2, cy = canvas.height/2;
    const r = Math.min(canvas.width, canvas.height)*0.35;

    // moon disk
    ctx.fillStyle = '#11161f';
    ctx.beginPath(); ctx.arc(cx,cy,r,0,2*Math.PI); ctx.fill();

    // illuminated shape: use elliptical clipping to simulate terminator
    const phaseAngle = Math.acos(2*fraction - 1); // 0=new, π=full
    // orientation: waxing -> light on right; waning -> light on left
    const dir = waxing ? 1 : -1;
    const k = Math.cos(phaseAngle); // ellipse factor

    // draw lit hemisphere using composite operations
    ctx.save();
    ctx.beginPath(); ctx.arc(cx,cy,r,0,2*Math.PI); ctx.clip();

    // gradient glow
    const glow = ctx.createRadialGradient(cx,cy,r*0.2,cx,cy,r);
    glow.addColorStop(0,'#e8edf7'); glow.addColorStop(1,'#9fb3d4');
    ctx.fillStyle = glow;

    // illuminated region via sweeping vertical strips
    // ellipse equation x^2 + (y^2)/(1-k^2) <= r^2 approximated by clipping width
    const steps = 400;
    for(let i=0;i<steps;i++){
      const t = (i/(steps-1))*2 - 1; // -1..1 across diameter
      const x = t*r;
      const w = r*Math.sqrt(1 - (x*x)/(r*r)); // circle half-height
      const cutoff = k*r; // terminator offset
      let left = cx - dir*cutoff;
      let right = cx + dir*r;
      // Draw illuminated side rectangle at slice x
      ctx.fillRect(Math.min(left,right), cy - w, Math.abs(right-left), 2*w);
    }
    ctx.restore();

    // rim highlight
    ctx.strokeStyle = '#2b3b55'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(cx,cy,r,0,2*Math.PI); ctx.stroke();
  }

  function render(){
    resize();
    const d = new Date(dateEl.value ? dateEl.value+'T'+(timeEl.value || '00:00')+':00' : new Date());
    const info = AstroMath.moonIllumination(d);
    const fraction = info.fraction; // 0..1
    const waxing = info.phase < 0.5; // 简单判断盈亏
    drawMoon(fraction, waxing);
    illumEl.textContent = (fraction*100).toFixed(1) + '%';
    phaseNameEl.textContent = info.name;
    ageEl.textContent = info.ageDays.toFixed(2);
  }

  setNow();
  window.addEventListener('resize', render);
  nowBtn.addEventListener('click', ()=>{ setNow(); render(); });
  renderBtn.addEventListener('click', render);
  [dateEl,timeEl].forEach(el=> el.addEventListener('change', render));
  render();
})();