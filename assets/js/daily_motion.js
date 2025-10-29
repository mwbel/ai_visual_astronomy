// 实时周日视运动轨迹绘制（Azimuth vs Altitude)
(function(){
  const plot = document.getElementById('plot');
  const ctx = plot.getContext('2d');
  const latEl = document.getElementById('lat');
  const lonEl = document.getElementById('lon');
  const dateEl = document.getElementById('date');
  const timeEl = document.getElementById('time');
  const tzEl = document.getElementById('tz');
  const nowBtn = document.getElementById('nowBtn');
  const renderBtn = document.getElementById('renderBtn');
  // 顶栏选择器回退（如果局部输入不存在）
  const topbarLatEl = document.querySelector('#locationContainer input[name="latitude"]');
  const topbarLonEl = document.querySelector('#locationContainer input[name="longitude"]');
  const topbarDateEl = document.querySelector('#dateContainer select');

  function setNow(){
    const now = new Date();
    if (dateEl) dateEl.value = now.toISOString().slice(0,10);
    if (topbarDateEl) topbarDateEl.value = now.toISOString().slice(0,10);
    if (timeEl) timeEl.value = now.toTimeString().slice(0,5);
    if (tzEl) tzEl.value = -now.getTimezoneOffset()/60;
  }

  function resize(){
    // set canvas pixel size from CSS size
    const rect = plot.getBoundingClientRect();
    plot.width = Math.floor(rect.width);
    plot.height = Math.floor(rect.height);
  }

  function drawAxes(){
    ctx.clearRect(0,0,plot.width,plot.height);
    // background gradient
    const grad = ctx.createLinearGradient(0,0,0,plot.height);
    grad.addColorStop(0,'#0c1220'); grad.addColorStop(1,'#0a0d12');
    ctx.fillStyle = grad; ctx.fillRect(0,0,plot.width,plot.height);

    // axes box
    const padding = 40;
    ctx.strokeStyle = '#233047'; ctx.lineWidth = 1;
    ctx.strokeRect(padding, padding, plot.width-2*padding, plot.height-2*padding);

    // grid lines
    ctx.font = '12px system-ui'; ctx.fillStyle = '#8a93a6'; ctx.textAlign = 'center';
    const azTicks = [0,60,120,180,240,300,360];
    const altTicks = [-10,0,10,20,30,40,50,60,70,80,90];

    azTicks.forEach(az => {
      const x = mapAz(az);
      ctx.strokeStyle = '#1f2a3b'; ctx.beginPath();
      ctx.moveTo(x, padding); ctx.lineTo(x, plot.height-padding); ctx.stroke();
      ctx.fillStyle = '#8a93a6'; ctx.fillText(az.toString(), x, plot.height-padding+16);
    });

    altTicks.forEach(alt => {
      const y = mapAlt(alt);
      ctx.strokeStyle = '#1f2a3b'; ctx.beginPath();
      ctx.moveTo(padding, y); ctx.lineTo(plot.width-padding, y); ctx.stroke();
      ctx.fillStyle = '#8a93a6'; ctx.textAlign = 'right'; ctx.fillText(alt.toString(), padding-8, y+4);
      ctx.textAlign = 'center';
    });

    ctx.fillStyle = '#8a93a6';
    ctx.fillText('Azimuth (°)', (plot.width)/2, plot.height-8);
    ctx.save();
    ctx.translate(14, plot.height/2); ctx.rotate(-Math.PI/2);
    ctx.fillText('Altitude (°)', 0, 0);
    ctx.restore();
  }

  const padding = 40;
  function mapAz(az){
    const w = plot.width-2*padding; return padding + w*(az/360);
  }
  function mapAlt(alt){
    const h = plot.height-2*padding; const minAlt=-10, maxAlt=90;
    const t = (alt - minAlt)/(maxAlt-minAlt);
    return plot.height - padding - h*t;
  }

  function computeDayPath(lat, lon, tz, date){
    // every 10 minutes
    const points = [];
    const d = new Date(date);
    d.setHours(0,0,0,0);
    for (let m=0; m<24*60; m+=10){
      const t = new Date(d.getTime() + m*60000);
      const pos = AstroMath.solarPosition(t, lat, lon, tz);
      points.push({ t, az: pos.azimuth, alt: pos.altitude });
    }
    const ss = AstroMath.approximateSunriseSunset(date, lat, lon, tz);
    return { points, ss };
  }

  function drawPath(lat, lon, tz, date){
    const {points, ss} = computeDayPath(lat, lon, tz, date);
    drawAxes();
    // path
    ctx.beginPath();
    points.forEach((p,i)=>{
      if (i===0) ctx.moveTo(mapAz(p.az), mapAlt(p.alt));
      else ctx.lineTo(mapAz(p.az), mapAlt(p.alt));
    });
    ctx.strokeStyle = '#4db8ff'; ctx.lineWidth = 2; ctx.stroke();

    // highlight above horizon (alt>0)
    ctx.beginPath();
    points.forEach((p,i)=>{
      if (p.alt>0){ ctx.lineTo(mapAz(p.az), mapAlt(p.alt)); }
      else { ctx.moveTo(mapAz(p.az), mapAlt(p.alt)); }
    });
    ctx.strokeStyle = '#4db8ff'; ctx.lineWidth = 3; ctx.setLineDash([6,4]); ctx.stroke();
    ctx.setLineDash([]);

    // current time marker
    const now = currentDateTime();
    const posNow = AstroMath.solarPosition(now, lat, lon, tz);
    const x = mapAz(posNow.azimuth), y = mapAlt(posNow.altitude);
    ctx.fillStyle = '#7bd389'; ctx.beginPath(); ctx.arc(x,y,5,0,2*Math.PI); ctx.fill();

    // sunrise/sunset markers
    if (ss && ss.sunrise){
      const dSunrise = new Date(date);
      dSunrise.setHours(ss.sunrise.h, ss.sunrise.m, 0, 0);
      const p = AstroMath.solarPosition(dSunrise, lat, lon, tz);
      ctx.fillStyle = '#ffcc66'; ctx.beginPath(); ctx.arc(mapAz(p.azimuth), mapAlt(p.altitude),4,0,2*Math.PI); ctx.fill();
    }
    if (ss && ss.sunset){
      const dSunset = new Date(date);
      dSunset.setHours(ss.sunset.h, ss.sunset.m, 0, 0);
      const p2 = AstroMath.solarPosition(dSunset, lat, lon, tz);
      ctx.fillStyle = '#ffcc66'; ctx.beginPath(); ctx.arc(mapAz(p2.azimuth), mapAlt(p2.altitude),4,0,2*Math.PI); ctx.fill();
    }
  }

  function currentDateTime(){
    const d = new Date();
    const dStr = (dateEl && dateEl.value) ? dateEl.value : (topbarDateEl && topbarDateEl.value ? topbarDateEl.value : null);
    if (dStr && timeEl && timeEl.value){
      return new Date(dStr+'T'+timeEl.value+':00');
    }
    return d;
  }

  function render(){
    const lat = latEl ? parseFloat(latEl.value) : parseFloat((topbarLatEl && topbarLatEl.value) || '39.9042');
    const lon = lonEl ? parseFloat(lonEl.value) : parseFloat((topbarLonEl && topbarLonEl.value) || '116.4074');
    const tz = tzEl ? parseFloat(tzEl.value) : (-new Date().getTimezoneOffset()/60);
    const dStr = (dateEl && dateEl.value) ? dateEl.value : (topbarDateEl && topbarDateEl.value ? topbarDateEl.value : new Date().toISOString().slice(0,10));
    const date = new Date(dStr);
    resize();
    drawPath(lat, lon, tz, date);
  }

  // init
  setNow();
  window.addEventListener('resize', render);
  nowBtn && nowBtn.addEventListener('click', ()=>{ setNow(); render(); });
  renderBtn && renderBtn.addEventListener('click', render);
  const inputs = [latEl,lonEl,dateEl,timeEl,tzEl,topbarLatEl,topbarLonEl,topbarDateEl].filter(Boolean);
  inputs.forEach(el=> el.addEventListener('change', render));
  const locContainer = document.querySelector('#locationContainer');
  if (locContainer){
    locContainer.addEventListener('location-change', ()=> render());
  }
  render();
})();