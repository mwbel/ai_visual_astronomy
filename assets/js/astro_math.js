// 轻量天文计算工具：太阳方位/高度、月相近似
// 太阳位置算法参考 NOAA Solar Calculator 的近似公式
(function(global){
  const DEG = Math.PI/180;
  const RAD = 180/Math.PI;

  function dayOfYear(date){
    const start = new Date(date.getFullYear(),0,0);
    const diff = date - start + ((start.getTimezoneOffset()-date.getTimezoneOffset())*60*1000);
    return Math.floor(diff/(1000*60*60*24));
  }

  function solarPosition(date, latDeg, lonDeg, tz){
    const d = dayOfYear(date);
    const h = date.getHours() + date.getMinutes()/60 + date.getSeconds()/3600;
    const gamma = 2*Math.PI/365 * (d - 1 + (h - 12)/24);
    const eqTime = 229.18*(0.000075 + 0.001868*Math.cos(gamma) - 0.032077*Math.sin(gamma) - 0.014615*Math.cos(2*gamma) - 0.040849*Math.sin(2*gamma));
    const decl = 0.006918 - 0.399912*Math.cos(gamma) + 0.070257*Math.sin(gamma) - 0.006758*Math.cos(2*gamma) + 0.000907*Math.sin(2*gamma) - 0.002697*Math.cos(3*gamma) + 0.00148*Math.sin(3*gamma);
    const timeOffset = eqTime + 4*lonDeg - 60*tz; // minutes
    const tst = h*60 + timeOffset; // minutes
    const haDeg = tst/4 - 180; // hour angle in degrees
    const ha = haDeg*DEG;
    const lat = latDeg*DEG;
    const cosZenith = Math.sin(lat)*Math.sin(decl) + Math.cos(lat)*Math.cos(decl)*Math.cos(ha);
    const zenith = Math.acos(Math.min(Math.max(cosZenith, -1), 1));
    const altitude = 90 - zenith*RAD;
    const az = Math.atan2(Math.sin(ha), Math.cos(ha)*Math.sin(lat) - Math.tan(decl)*Math.cos(lat))*RAD;
    let azimuth = az;
    if (azimuth < 0) azimuth += 360;
    return { azimuth, altitude, declination: decl*RAD, equationOfTime: eqTime, hourAngle: haDeg };
  }

  // 粗略计算日出/日落时刻：高度角近似为 -0.833°（折射与太阳半径）
  function approximateSunriseSunset(date, latDeg, lonDeg, tz){
    const d = dayOfYear(date);
    const lat = latDeg*DEG;
    const h0 = -0.833*DEG; // 日出/日落参考高度
    // 先估算当天 decl 与 eqTime 使用正午时刻
    const noon = new Date(date);
    noon.setHours(12,0,0,0);
    const posNoon = solarPosition(noon, latDeg, lonDeg, tz);
    const decl = posNoon.declination*DEG;
    const cosH = (Math.sin(h0) - Math.sin(lat)*Math.sin(decl)) / (Math.cos(lat)*Math.cos(decl));
    if (cosH < -1 || cosH > 1) return { sunrise: null, sunset: null, polarDay: cosH < -1, polarNight: cosH > 1 };
    const H = Math.acos(cosH)*RAD; // hour angle degrees
    // 太阳中天时刻（近似考虑 EoT 与经度）
    const gamma = 2*Math.PI/365 * (d - 1 + (0)/24);
    const eqTime = 229.18*(0.000075 + 0.001868*Math.cos(gamma) - 0.032077*Math.sin(gamma) - 0.014615*Math.cos(2*gamma) - 0.040849*Math.sin(2*gamma));
    const solarNoonMin = 720 - 4*lonDeg - eqTime + 60*tz; // minutes
    const deltaMin = 4*H*60/360; // minutes
    const sunriseMin = solarNoonMin - deltaMin;
    const sunsetMin  = solarNoonMin + deltaMin;
    function toTime(min){
      const m = Math.round(min);
      let hh = Math.floor(m/60), mm = m%60;
      hh = (hh%24+24)%24;
      return { h:hh, m:mm };
    }
    return { sunrise: toTime(sunriseMin), sunset: toTime(sunsetMin), solarNoon: toTime(solarNoonMin) };
  }

  // 儒略日（近似），用于月相计算
  function julianDay(date){
    const year = date.getUTCFullYear();
    const month = date.getUTCMonth()+1;
    const day = date.getUTCDate() + (date.getUTCHours()/24) + (date.getUTCMinutes()/1440) + (date.getUTCSeconds()/86400);
    let a = Math.floor((14 - month)/12);
    const y = year + 4800 - a;
    const m = month + 12*a - 3;
    let jd = day + Math.floor((153*m + 2)/5) + 365*y + Math.floor(y/4) - Math.floor(y/100) + Math.floor(y/400) - 32045;
    return jd;
  }

  // 月相（照明比例与相位名）近似：基于 2000-01-06 新月参考与朔望月长度
  function moonIllumination(date){
    const jd = julianDay(date);
    const synodic = 29.530588853; // days
    const ref = 2451550.1; // 2000-01-06 18:14 UT
    let phase = ((jd - ref) / synodic) % 1;
    if (phase < 0) phase += 1;
    const illumination = 0.5*(1 - Math.cos(2*Math.PI*phase));
    const ageDays = phase*synodic;
    let name;
    if (phase < 0.03) name = '新月';
    else if (phase < 0.25) name = '峨眉月（上弦前）';
    else if (Math.abs(phase-0.25) < 0.03) name = '上弦月';
    else if (phase < 0.5) name = '盈凸月';
    else if (Math.abs(phase-0.5) < 0.03) name = '满月';
    else if (phase < 0.75) name = '亏凸月';
    else if (Math.abs(phase-0.75) < 0.03) name = '下弦月';
    else name = '残月（下弦后）';
    return { fraction: illumination, phase, ageDays, name };
  }

  global.AstroMath = { solarPosition, approximateSunriseSunset, moonIllumination };
})(window);