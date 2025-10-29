/**
 * 演示数据和增强功能
 * 提供丰富的术语解释和示例数据
 */

class DemoDataProvider {
    constructor() {
        this.enhancedTermExplanations = {
            'sidereal_day': {
                title: '恒星日 (Sidereal Day)',
                description: '地球相对于恒星自转一周的时间，约23小时56分4秒。比太阳日短约4分钟。',
                details: '恒星日是天文学中的基本时间单位，反映了地球的真实自转周期。由于地球在公转的同时自转，所以恒星日比太阳日短。',
                formula: '恒星日 = 23h 56m 4.0905s',
                significance: '在藏历天文学中，恒星日用于精确计算天体位置和制定历法。',
                visualization: 'sidereal_animation',
                relatedTerms: ['solar_day', 'sidereal_time']
            },
            'solar_day': {
                title: '太阳日 (Solar Day)',
                description: '太阳连续两次经过同一地点天顶的时间间隔，平均为24小时。',
                details: '太阳日是我们日常生活中使用的时间单位。由于地球轨道的椭圆性和地轴倾斜，真太阳日的长度在一年中会有变化。',
                formula: '平太阳日 = 24h 00m 00s',
                significance: '太阳日是民用时间的基础，也是藏历日期计算的重要参考。',
                visualization: 'solar_animation',
                relatedTerms: ['sidereal_day', 'equation_of_time']
            },
            'lunar_month': {
                title: '朔望月 (Lunar Month)',
                description: '月亮从新月到下一个新月的周期，约29.53天。',
                details: '朔望月是农历月份的基础，包含新月、上弦、满月、下弦四个主要月相。在藏历中，朔望月用于确定月份和节日。',
                formula: '朔望月 = 29.530588853天',
                significance: '朔望月是藏历月份划分的基础，影响宗教节日和农业活动的安排。',
                visualization: 'lunar_phases',
                relatedTerms: ['moon_phases', 'tibetan_calendar']
            },
            'constellation_28': {
                title: '二十八宿 (28 Lunar Mansions)',
                description: '中国古代天文学将黄道附近的星空分为二十八个星座。',
                details: '二十八宿是中国传统天文学的重要组成部分，每宿约占黄道13度。分为东方青龙、南方朱雀、西方白虎、北方玄武四象。',
                formula: '每宿平均 = 360° ÷ 28 ≈ 12.86°',
                significance: '在藏历天文学中，二十八宿用于观测和记录天体运动，是制定历法的重要参考。',
                visualization: 'constellation_28_map',
                relatedTerms: ['constellation_27', 'four_symbols']
            },
            'constellation_27': {
                title: '二十七宿 (27 Nakshatras)',
                description: '印度天文学系统，将黄道分为27个星座，每个约13.33度。',
                details: '二十七宿系统在藏历天文学中有重要应用，与二十八宿系统略有不同。每个nakshatra都有特定的象征意义和占星学含义。',
                formula: '每宿 = 360° ÷ 27 = 13.33°',
                significance: '二十七宿在藏传佛教天文学中用于确定吉凶时辰和进行占星预测。',
                visualization: 'nakshatra_wheel',
                relatedTerms: ['constellation_28', 'vedic_astrology']
            },
            'solar_terms': {
                title: '节气 (Solar Terms)',
                description: '根据太阳在黄道上的位置划分的24个时间节点。',
                details: '二十四节气反映了太阳直射点的移动规律，是农业生产的重要时间参考。每个节气约15天，对应太阳黄经15度的变化。',
                formula: '每节气 = 360° ÷ 24 = 15°',
                significance: '节气在藏历中用于指导农业活动和宗教仪式，是连接天文观测与实际生活的桥梁。',
                visualization: 'solar_terms_circle',
                relatedTerms: ['ecliptic_longitude', 'seasons']
            }
        };
        
        this.visualizationTemplates = {
            'sidereal_animation': this.createSiderealDayVisualization,
            'solar_animation': this.createSolarDayVisualization,
            'lunar_phases': this.createLunarPhasesVisualization,
            'constellation_28_map': this.createConstellation28Map,
            'nakshatra_wheel': this.createNakshatraWheel,
            'solar_terms_circle': this.createSolarTermsCircle
        };
        
        this.sampleCalculations = this.generateSampleCalculations();
    }

    /**
     * 获取增强的术语解释
     * @param {string} termKey 术语键值
     * @returns {Object} 增强的术语解释
     */
    getEnhancedTermExplanation(termKey) {
        return this.enhancedTermExplanations[termKey] || {
            title: '未知术语',
            description: '暂无解释',
            details: '',
            formula: '',
            significance: '',
            visualization: null,
            relatedTerms: []
        };
    }

    /**
     * 创建恒星日可视化
     */
    createSiderealDayVisualization() {
        return {
            type: 'animation',
            description: '展示地球相对于恒星的自转周期',
            data: {
                earth_rotation: 360, // 度
                star_reference: 'fixed',
                time_period: '23h 56m 4s'
            }
        };
    }

    /**
     * 创建太阳日可视化
     */
    createSolarDayVisualization() {
        return {
            type: 'animation',
            description: '展示太阳连续两次经过天顶的时间间隔',
            data: {
                sun_position: 'moving',
                earth_rotation: 360 + 0.986, // 额外的0.986度补偿公转
                time_period: '24h 00m 00s'
            }
        };
    }

    /**
     * 创建月相可视化
     */
    createLunarPhasesVisualization() {
        return {
            type: 'phase_diagram',
            description: '展示月亮的盈亏变化周期',
            data: {
                phases: [
                    { name: '新月', illumination: 0, day: 0 },
                    { name: '蛾眉月', illumination: 0.25, day: 7.4 },
                    { name: '上弦月', illumination: 0.5, day: 14.8 },
                    { name: '盈凸月', illumination: 0.75, day: 22.1 },
                    { name: '满月', illumination: 1.0, day: 29.5 }
                ]
            }
        };
    }

    /**
     * 生成示例计算数据
     */
    generateSampleCalculations() {
        const startDate = new Date('2024-01-01');
        const calculations = [];
        
        for (let i = 0; i < 365; i++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);
            
            // 模拟计算数据
            const dayOfYear = i + 1;
            const siderealTimeDiff = i * 3.943; // 每天约3.943分钟的累积差异
            
            calculations.push({
                date: currentDate.toISOString().split('T')[0],
                dayOfYear: dayOfYear,
                siderealTimeDifference: siderealTimeDiff,
                sunLongitude: (dayOfYear * 0.986) % 360, // 简化的太阳黄经
                moonPhase: (dayOfYear % 29.53) / 29.53, // 月相
                season: this.getSeason(dayOfYear)
            });
        }
        
        return calculations;
    }

    /**
     * 获取季节
     * @param {number} dayOfYear 一年中的第几天
     * @returns {string} 季节名称
     */
    getSeason(dayOfYear) {
        if (dayOfYear < 80 || dayOfYear >= 355) return '冬季';
        if (dayOfYear < 172) return '春季';
        if (dayOfYear < 266) return '夏季';
        return '秋季';
    }

    /**
     * 获取当日的特殊事件
     * @param {Date} date 日期
     * @returns {Array} 特殊事件列表
     */
    getSpecialEvents(date) {
        const events = [];
        const month = date.getMonth() + 1;
        const day = date.getDate();
        
        // 添加一些重要的天文事件和藏历节日
        const specialDates = {
            '1-1': '公历新年',
            '2-10': '藏历新年（示例）',
            '3-20': '春分',
            '6-21': '夏至',
            '9-23': '秋分',
            '12-22': '冬至',
            '4-15': '萨嘎达瓦节（示例）',
            '6-4': '转法轮节（示例）'
        };
        
        const dateKey = `${month}-${day}`;
        if (specialDates[dateKey]) {
            events.push({
                type: 'festival',
                name: specialDates[dateKey],
                description: '重要的天文或文化事件'
            });
        }
        
        return events;
    }

    /**
     * 获取实时计算提示
     * @param {Object} currentData 当前数据
     * @returns {Array} 提示信息
     */
    getCalculationTips(currentData) {
        const tips = [];
        
        if (currentData.siderealTimeDifference) {
            const diffHours = currentData.siderealTimeDifference / 60;
            if (diffHours > 12) {
                tips.push({
                    type: 'info',
                    message: `恒星时与太阳时的累积差异已超过${diffHours.toFixed(1)}小时`
                });
            }
        }
        
        if (currentData.moonPhase) {
            const phase = currentData.moonPhase;
            if (Math.abs(phase - 0) < 0.02) {
                tips.push({
                    type: 'highlight',
                    message: '今天接近新月，是观测恒星的好时机'
                });
            } else if (Math.abs(phase - 0.5) < 0.02) {
                tips.push({
                    type: 'highlight',
                    message: '今天接近满月，月光较亮'
                });
            }
        }
        
        return tips;
    }

    /**
     * 生成教育内容
     * @param {string} topic 主题
     * @returns {Object} 教育内容
     */
    getEducationalContent(topic) {
        const content = {
            'time_systems': {
                title: '时间系统比较',
                sections: [
                    {
                        subtitle: '恒星时 vs 太阳时',
                        content: '恒星时基于地球相对于恒星的自转，而太阳时基于太阳的视运动。两者的差异源于地球的公转运动。'
                    },
                    {
                        subtitle: '实际应用',
                        content: '天文观测使用恒星时，日常生活使用太阳时。藏历天文学需要同时考虑两种时间系统。'
                    }
                ]
            },
            'lunar_calendar': {
                title: '藏历月份系统',
                sections: [
                    {
                        subtitle: '朔望月基础',
                        content: '藏历以朔望月为基础，每月从新月开始，到下一个新月结束。'
                    },
                    {
                        subtitle: '闰月调节',
                        content: '为了与太阳年保持同步，藏历会在特定年份增加闰月。'
                    }
                ]
            }
        };
        
        return content[topic] || { title: '内容待添加', sections: [] };
    }
}

// 导出类供其他模块使用
window.DemoDataProvider = DemoDataProvider;
