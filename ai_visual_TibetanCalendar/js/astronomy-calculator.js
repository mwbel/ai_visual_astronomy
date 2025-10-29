/**
 * 藏历天文历算计算模块
 * 实现恒星日与太阳日差异计算、朔望月周期计算、基础天体位置计算
 */

class AstronomyCalculator {
    constructor() {
        // 天文常数
        this.SIDEREAL_DAY_HOURS = 23.93447; // 恒星日长度（小时）
        this.SOLAR_DAY_HOURS = 24.0; // 太阳日长度（小时）
        this.LUNAR_MONTH_DAYS = 29.530588853; // 朔望月周期（天）
        this.TROPICAL_YEAR_DAYS = 365.24219; // 回归年长度（天）
        
        // 二十八宿星座数据
        this.CONSTELLATION_28 = [
            { name: '角宿', ra: 183.8, dec: -11.2 },
            { name: '亢宿', ra: 186.6, dec: -9.5 },
            { name: '氐宿', ra: 240.1, dec: -22.6 },
            { name: '房宿', ra: 247.4, dec: -26.1 },
            { name: '心宿', ra: 250.3, dec: -26.6 },
            { name: '尾宿', ra: 265.6, dec: -37.1 },
            { name: '箕宿', ra: 279.2, dec: -40.1 },
            { name: '斗宿', ra: 279.9, dec: -30.9 },
            { name: '牛宿', ra: 294.4, dec: -18.0 },
            { name: '女宿', ra: 314.3, dec: -5.8 },
            { name: '虚宿', ra: 327.9, dec: 9.9 },
            { name: '危宿', ra: 334.2, dec: 20.8 },
            { name: '室宿', ra: 349.3, dec: 32.7 },
            { name: '壁宿', ra: 8.9, dec: 29.6 },
            { name: '奎宿', ra: 24.5, dec: 20.8 },
            { name: '娄宿', ra: 41.8, dec: 20.8 },
            { name: '胃宿', ra: 56.2, dec: 21.0 },
            { name: '昴宿', ra: 56.9, dec: 24.1 },
            { name: '毕宿', ra: 68.9, dec: 15.6 },
            { name: '觜宿', ra: 83.0, dec: 22.5 },
            { name: '参宿', ra: 84.1, dec: -1.2 },
            { name: '井宿', ra: 102.0, dec: 16.0 },
            { name: '鬼宿', ra: 130.0, dec: 19.8 },
            { name: '柳宿', ra: 134.2, dec: 8.4 },
            { name: '星宿', ra: 142.7, dec: -11.2 },
            { name: '张宿', ra: 157.6, dec: -27.9 },
            { name: '翼宿', ra: 169.5, dec: -20.5 },
            { name: '轸宿', ra: 182.1, dec: -15.8 }
        ];
        
        // 藏历术语解释
        this.TERM_EXPLANATIONS = {
            'sidereal_day': {
                title: '恒星日',
                description: '地球相对于恒星自转一周的时间，约23小时56分4秒。比太阳日短约4分钟。',
                details: '恒星日是天文学中的基本时间单位，反映了地球的真实自转周期。'
            },
            'solar_day': {
                title: '太阳日',
                description: '太阳连续两次经过同一地点天顶的时间间隔，平均为24小时。',
                details: '太阳日比恒星日长，是因为地球在公转的同时也在自转。'
            },
            'lunar_month': {
                title: '朔望月',
                description: '月亮从新月到下一个新月的周期，约29.53天。',
                details: '朔望月是农历月份的基础，包含新月、上弦、满月、下弦四个主要月相。'
            },
            'constellation_28': {
                title: '二十八宿',
                description: '中国古代天文学将黄道附近的星空分为二十八个星座。',
                details: '二十八宿是中国传统天文学的重要组成部分，用于观测和记录天体运动。'
            },
            'constellation_27': {
                title: '二十七宿',
                description: '印度天文学系统，将黄道分为27个星座，每个约13.33度。',
                details: '二十七宿系统在藏历天文学中有重要应用，与二十八宿系统略有不同。'
            },
            'solar_terms': {
                title: '节气',
                description: '根据太阳在黄道上的位置划分的24个时间节点。',
                details: '节气反映了太阳直射点的移动规律，是农业生产的重要时间参考。'
            }
        };
    }

    /**
     * 计算恒星日与太阳日的时间差异
     * @param {Date} startDate 开始日期
     * @param {number} days 计算天数
     * @returns {Array} 时间差异数据
     */
    calculateSiderealSolarDifference(startDate, days = 365) {
        const results = [];
        let cumulativeDiff = 0;
        
        for (let i = 0; i < days; i++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);
            
            // 每日时间差（分钟）
            const dailyDiff = (this.SOLAR_DAY_HOURS - this.SIDEREAL_DAY_HOURS) * 60;
            cumulativeDiff += dailyDiff;
            
            // 计算恒星时
            const siderealTime = this.calculateSiderealTime(currentDate);
            
            results.push({
                date: new Date(currentDate),
                dailyDifference: dailyDiff,
                cumulativeDifference: cumulativeDiff,
                siderealTime: siderealTime,
                solarTime: currentDate.getHours() + currentDate.getMinutes() / 60
            });
        }
        
        return results;
    }

    /**
     * 计算恒星时
     * @param {Date} date 日期
     * @returns {number} 恒星时（小时）
     */
    calculateSiderealTime(date) {
        // 简化的恒星时计算
        const J2000 = new Date('2000-01-01T12:00:00Z');
        const daysSinceJ2000 = (date - J2000) / (1000 * 60 * 60 * 24);
        
        // 格林威治恒星时
        const gst = (18.697374558 + 24.06570982441908 * daysSinceJ2000) % 24;
        
        return gst;
    }

    /**
     * 计算太阳位置
     * @param {Date} date 日期
     * @returns {Object} 太阳的赤经赤纬
     */
    calculateSunPosition(date) {
        const dayOfYear = this.getDayOfYear(date);
        const year = date.getFullYear();
        
        // 简化的太阳位置计算
        const n = dayOfYear - 81; // 从春分点开始计算
        const L = (280.460 + 0.9856474 * n) % 360; // 太阳黄经
        const g = ((357.528 + 0.9856003 * n) % 360) * Math.PI / 180; // 平近点角
        
        // 修正黄经
        const lambda = (L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * Math.PI / 180;
        
        // 黄赤交角
        const epsilon = 23.439 * Math.PI / 180;
        
        // 转换为赤道坐标
        const ra = Math.atan2(Math.cos(epsilon) * Math.sin(lambda), Math.cos(lambda)) * 180 / Math.PI;
        const dec = Math.asin(Math.sin(epsilon) * Math.sin(lambda)) * 180 / Math.PI;
        
        return {
            rightAscension: ra < 0 ? ra + 360 : ra,
            declination: dec,
            eclipticLongitude: lambda * 180 / Math.PI
        };
    }

    /**
     * 计算月亮位置
     * @param {Date} date 日期
     * @returns {Object} 月亮的赤经赤纬和月相
     */
    calculateMoonPosition(date) {
        const daysSinceNewMoon = this.getDaysSinceNewMoon(date);
        const lunarAge = daysSinceNewMoon % this.LUNAR_MONTH_DAYS;
        
        // 简化的月亮位置计算
        const meanLongitude = (218.316 + 13.176396 * daysSinceNewMoon) % 360;
        const meanAnomaly = (134.963 + 13.064993 * daysSinceNewMoon) % 360 * Math.PI / 180;
        
        // 修正经度
        const longitude = (meanLongitude + 6.289 * Math.sin(meanAnomaly)) * Math.PI / 180;
        
        // 月亮纬度（简化）
        const latitude = 5.128 * Math.sin((93.272 + 13.229350 * daysSinceNewMoon) * Math.PI / 180) * Math.PI / 180;
        
        // 转换为赤道坐标
        const epsilon = 23.439 * Math.PI / 180;
        const ra = Math.atan2(
            Math.cos(epsilon) * Math.sin(longitude) - Math.sin(epsilon) * Math.tan(latitude),
            Math.cos(longitude)
        ) * 180 / Math.PI;
        const dec = Math.asin(
            Math.sin(epsilon) * Math.sin(longitude) + Math.cos(epsilon) * Math.sin(latitude)
        ) * 180 / Math.PI;
        
        // 月相计算
        const phase = this.calculateMoonPhase(lunarAge);
        
        return {
            rightAscension: ra < 0 ? ra + 360 : ra,
            declination: dec,
            lunarAge: lunarAge,
            phase: phase,
            illumination: (1 - Math.cos(lunarAge / this.LUNAR_MONTH_DAYS * 2 * Math.PI)) / 2
        };
    }

    /**
     * 计算月相
     * @param {number} lunarAge 月龄（天）
     * @returns {string} 月相名称
     */
    calculateMoonPhase(lunarAge) {
        const phases = ['新月', '蛾眉月', '上弦月', '盈凸月', '满月', '亏凸月', '下弦月', '残月'];
        const phaseIndex = Math.floor((lunarAge / this.LUNAR_MONTH_DAYS) * 8) % 8;
        return phases[phaseIndex];
    }

    /**
     * 获取一年中的第几天
     * @param {Date} date 日期
     * @returns {number} 天数
     */
    getDayOfYear(date) {
        const start = new Date(date.getFullYear(), 0, 0);
        const diff = date - start;
        return Math.floor(diff / (1000 * 60 * 60 * 24));
    }

    /**
     * 获取距离最近新月的天数
     * @param {Date} date 日期
     * @returns {number} 天数
     */
    getDaysSinceNewMoon(date) {
        // 使用2000年1月6日的新月作为参考点
        const referenceNewMoon = new Date('2000-01-06T18:14:00Z');
        const daysDiff = (date - referenceNewMoon) / (1000 * 60 * 60 * 24);
        return daysDiff;
    }

    /**
     * 获取术语解释
     * @param {string} termKey 术语键值
     * @returns {Object} 术语解释对象
     */
    getTermExplanation(termKey) {
        return this.TERM_EXPLANATIONS[termKey] || {
            title: '未知术语',
            description: '暂无解释',
            details: ''
        };
    }

    /**
     * 计算二十八宿当前位置
     * @param {Date} date 日期
     * @returns {Array} 二十八宿位置数据
     */
    calculateConstellations(date) {
        const siderealTime = this.calculateSiderealTime(date);
        
        return this.CONSTELLATION_28.map(constellation => {
            // 计算当前时角
            const hourAngle = (siderealTime - constellation.ra / 15) * 15;
            
            return {
                ...constellation,
                hourAngle: hourAngle,
                visible: Math.abs(hourAngle) < 90 // 简化的可见性判断
            };
        });
    }

    /**
     * 生成3D可视化数据
     * @param {Array} timeData 时间数据
     * @returns {Object} 3D坐标数据
     */
    generate3DVisualizationData(timeData) {
        const coordinates = {
            x: [],
            y: [],
            z: [],
            dates: [],
            values: []
        };

        timeData.forEach((item, index) => {
            // 将时间差转换为角度
            const angle = (item.cumulativeDifference / (365.25 * 24 * 60)) * 2 * Math.PI;
            
            // 3D螺旋坐标
            coordinates.x.push(Math.cos(angle) * (1 + index / timeData.length));
            coordinates.y.push(Math.sin(angle) * (1 + index / timeData.length));
            coordinates.z.push(index / timeData.length * 2 - 1);
            coordinates.dates.push(item.date.toISOString());
            coordinates.values.push(item.cumulativeDifference);
        });

        return coordinates;
    }
}

// 导出类供其他模块使用
window.AstronomyCalculator = AstronomyCalculator;
