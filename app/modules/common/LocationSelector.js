// LocationSelector.js: 城市选择 + 自动回填经纬海拔 + 手动微调
(function(global){
  function parseCSV(text){
    const lines = text.trim().split(/\r?\n/);
    const header = lines[0].split(',').map(s=>s.trim());
    return lines.slice(1).map(line => {
      const cols = line.split(',').map(s=>s.trim());
      const obj = {}; header.forEach((h,i)=> obj[h] = cols[i]);
      return obj;
    });
  }
  async function loadCities(url){
    try {
      const res = await fetch(url, { cache: 'no-cache' });
      if (!res.ok) throw new Error('HTTP '+res.status);
      const text = await res.text();
      return parseCSV(text);
    } catch(e){
      // fallback demo list
      return [
        {name:'上海', lon:'121.4737', lat:'31.2304', elev_m:'4'},
        {name:'北京', lon:'116.4074', lat:'39.9042', elev_m:'43'},
        {name:'拉萨', lon:'91.1409', lat:'29.6456', elev_m:'3650'},
        {name:'东京', lon:'139.6917', lat:'35.6895', elev_m:'40'},
        {name:'旧金山', lon:'-122.4194', lat:'37.7749', elev_m:'16'},
        {name:'伦敦', lon:'-0.1276', lat:'51.5074', elev_m:'35'},
        {name:'开罗', lon:'31.2357', lat:'30.0444', elev_m:'23'},
        {name:'悉尼', lon:'151.2093', lat:'-33.8688', elev_m:'58'},
        {name:'布宜诺斯艾利斯', lon:'-58.3816', lat:'-34.6037', elev_m:'25'}
      ];
    }
  }
  function renderLocationSelector(containerSelector, opts){
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const section = document.createElement('div'); section.className='section';
    const citySel = document.createElement('select'); citySel.id='citySel';
    const lonInput = document.createElement('input'); lonInput.type='number'; lonInput.step='0.0001'; lonInput.id='lonInput'; lonInput.name='longitude';
    const latInput = document.createElement('input'); latInput.type='number'; latInput.step='0.0001'; latInput.id='latInput'; latInput.name='latitude';
    const elevInput = document.createElement('input'); elevInput.type='number'; elevInput.step='1'; elevInput.id='elevInput'; elevInput.name='elevation';
    const nameLabel = document.createElement('label'); nameLabel.textContent='地点';
    const lonLabel = document.createElement('label'); lonLabel.textContent='经度(°)';
    const latLabel = document.createElement('label'); latLabel.textContent='纬度(°)';
    const elevLabel = document.createElement('label'); elevLabel.textContent='海拔(m)';
    section.append(nameLabel, citySel, lonLabel, lonInput, latLabel, latInput, elevLabel, elevInput);
    container.appendChild(section);

    function setFields(c){ lonInput.value=c.lon; latInput.value=c.lat; elevInput.value=c.elev_m; }
    loadCities(opts?.url || '/data/cities.csv').then(cities => {
      cities.forEach(c => { const o=document.createElement('option'); o.value=c.name; o.textContent=c.name; o.dataset.lon=c.lon; o.dataset.lat=c.lat; o.dataset.elev=c.elev_m; citySel.appendChild(o); });
      const init = cities.find(c=> c.name==='北京') || cities[0];
      citySel.value = init.name; setFields(init);
      container.dispatchEvent(new CustomEvent('location-change', { detail: getLocation() }));
    });

    citySel.addEventListener('change', ()=>{
      const sel = citySel.selectedOptions[0];
      setFields({ lon: sel.dataset.lon, lat: sel.dataset.lat, elev_m: sel.dataset.elev });
      container.dispatchEvent(new CustomEvent('location-change', { detail: getLocation() }));
    });
    [lonInput, latInput, elevInput].forEach(el=> el.addEventListener('change', ()=> container.dispatchEvent(new CustomEvent('location-change', { detail: getLocation() }))));

    function getLocation(){
      return { city: citySel.value, lon: parseFloat(lonInput.value), lat: parseFloat(latInput.value), elev_m: parseFloat(elevInput.value) };
    }
    return { getLocation };
  }
  global.LocationSelector = { renderLocationSelector };
})(window);