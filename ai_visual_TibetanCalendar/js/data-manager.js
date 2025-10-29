/**
 * 数据管理模块
 * 处理数据缓存、状态管理和数据流控制
 */

class DataManager {
    constructor() {
        // 数据缓存
        this.cache = new Map();
        this.maxCacheSize = 1000;
        
        // 当前状态
        this.currentState = {
            date: new Date('2024-01-01'),
            viewMode: 'geocentric',
            displayMode: '3d',
            playbackSpeed: 1,
            isPlaying: false,
            selectedTerm: null,
            observerLocation: {
                latitude: 29.65,
                longitude: 91.1,
                altitude: 3650
            }
        };
        
        // 事件监听器
        this.listeners = new Map();
        
        // 性能监控
        this.performanceMetrics = {
            calculationTime: [],
            renderTime: [],
            memoryUsage: []
        };
        
        this.initializeStorage();
    }

    /**
     * 初始化本地存储
     */
    initializeStorage() {
        // 从本地存储恢复设置
        const savedState = localStorage.getItem('tibetan-astronomy-state');
        if (savedState) {
            try {
                const parsed = JSON.parse(savedState);
                this.currentState = { ...this.currentState, ...parsed };
            } catch (error) {
                console.warn('无法恢复保存的状态:', error);
            }
        }
    }

    /**
     * 保存状态到本地存储
     */
    saveState() {
        try {
            localStorage.setItem('tibetan-astronomy-state', JSON.stringify(this.currentState));
        } catch (error) {
            console.warn('无法保存状态:', error);
        }
    }

    /**
     * 更新数据
     * @param {Object} data 新数据
     */
    updateData(data) {
        const startTime = performance.now();
        
        // 生成缓存键
        const cacheKey = this.generateCacheKey(data.date);
        
        // 检查缓存
        if (this.cache.has(cacheKey)) {
            const cachedData = this.cache.get(cacheKey);
            this.notifyListeners('dataUpdated', cachedData);
            return cachedData;
        }
        
        // 处理新数据
        const processedData = this.processData(data);
        
        // 添加到缓存
        this.addToCache(cacheKey, processedData);
        
        // 更新当前状态
        this.currentState.date = data.date;
        this.saveState();
        
        // 记录性能指标
        const calculationTime = performance.now() - startTime;
        this.recordPerformance('calculation', calculationTime);
        
        // 通知监听器
        this.notifyListeners('dataUpdated', processedData);
        
        return processedData;
    }

    /**
     * 处理数据
     * @param {Object} rawData 原始数据
     * @returns {Object} 处理后的数据
     */
    processData(rawData) {
        const processed = {
            ...rawData,
            timestamp: Date.now(),
            processed: true
        };
        
        // 添加计算的衍生数据
        if (rawData.sun && rawData.moon) {
            processed.sunMoonAngle = this.calculateAngularSeparation(
                rawData.sun.rightAscension,
                rawData.sun.declination,
                rawData.moon.rightAscension,
                rawData.moon.declination
            );
        }
        
        // 添加可见性信息
        if (rawData.sun) {
            processed.sun.altitude = this.calculateAltitude(
                rawData.sun.rightAscension,
                rawData.sun.declination,
                rawData.date
            );
            processed.sun.visible = processed.sun.altitude > 0;
        }
        
        if (rawData.moon) {
            processed.moon.altitude = this.calculateAltitude(
                rawData.moon.rightAscension,
                rawData.moon.declination,
                rawData.date
            );
            processed.moon.visible = processed.moon.altitude > 0;
        }
        
        return processed;
    }

    /**
     * 计算角距离
     * @param {number} ra1 第一个天体的赤经
     * @param {number} dec1 第一个天体的赤纬
     * @param {number} ra2 第二个天体的赤经
     * @param {number} dec2 第二个天体的赤纬
     * @returns {number} 角距离（度）
     */
    calculateAngularSeparation(ra1, dec1, ra2, dec2) {
        const ra1Rad = ra1 * Math.PI / 180;
        const dec1Rad = dec1 * Math.PI / 180;
        const ra2Rad = ra2 * Math.PI / 180;
        const dec2Rad = dec2 * Math.PI / 180;
        
        const cosAngle = Math.sin(dec1Rad) * Math.sin(dec2Rad) +
                        Math.cos(dec1Rad) * Math.cos(dec2Rad) * Math.cos(ra1Rad - ra2Rad);
        
        return Math.acos(Math.max(-1, Math.min(1, cosAngle))) * 180 / Math.PI;
    }

    /**
     * 计算高度角
     * @param {number} ra 赤经
     * @param {number} dec 赤纬
     * @param {Date} date 日期
     * @returns {number} 高度角（度）
     */
    calculateAltitude(ra, dec, date) {
        // 简化的高度角计算
        const lst = this.calculateLocalSiderealTime(date);
        const hourAngle = (lst - ra / 15) * 15 * Math.PI / 180;
        const decRad = dec * Math.PI / 180;
        const latRad = this.currentState.observerLocation.latitude * Math.PI / 180;
        
        const sinAlt = Math.sin(decRad) * Math.sin(latRad) +
                      Math.cos(decRad) * Math.cos(latRad) * Math.cos(hourAngle);
        
        return Math.asin(Math.max(-1, Math.min(1, sinAlt))) * 180 / Math.PI;
    }

    /**
     * 计算地方恒星时
     * @param {Date} date 日期
     * @returns {number} 地方恒星时（小时）
     */
    calculateLocalSiderealTime(date) {
        // 简化的地方恒星时计算
        const J2000 = new Date('2000-01-01T12:00:00Z');
        const daysSinceJ2000 = (date - J2000) / (1000 * 60 * 60 * 24);
        
        const gst = (18.697374558 + 24.06570982441908 * daysSinceJ2000) % 24;
        const lst = (gst + this.currentState.observerLocation.longitude / 15) % 24;
        
        return lst;
    }

    /**
     * 生成缓存键
     * @param {Date} date 日期
     * @returns {string} 缓存键
     */
    generateCacheKey(date) {
        const dateStr = date.toISOString().split('T')[0];
        const hour = date.getHours();
        return `${dateStr}-${hour}`;
    }

    /**
     * 添加到缓存
     * @param {string} key 缓存键
     * @param {Object} data 数据
     */
    addToCache(key, data) {
        // 如果缓存已满，删除最旧的条目
        if (this.cache.size >= this.maxCacheSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        
        this.cache.set(key, data);
    }

    /**
     * 从缓存获取数据
     * @param {string} key 缓存键
     * @returns {Object|null} 缓存的数据
     */
    getFromCache(key) {
        return this.cache.get(key) || null;
    }

    /**
     * 清空缓存
     */
    clearCache() {
        this.cache.clear();
        this.notifyListeners('cacheCleared');
    }

    /**
     * 添加事件监听器
     * @param {string} event 事件名称
     * @param {Function} callback 回调函数
     */
    addEventListener(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * 移除事件监听器
     * @param {string} event 事件名称
     * @param {Function} callback 回调函数
     */
    removeEventListener(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * 通知监听器
     * @param {string} event 事件名称
     * @param {*} data 事件数据
     */
    notifyListeners(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`事件监听器错误 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 更新状态
     * @param {Object} newState 新状态
     */
    updateState(newState) {
        const oldState = { ...this.currentState };
        this.currentState = { ...this.currentState, ...newState };
        
        this.saveState();
        this.notifyListeners('stateChanged', {
            oldState,
            newState: this.currentState
        });
    }

    /**
     * 获取当前状态
     * @returns {Object} 当前状态
     */
    getState() {
        return { ...this.currentState };
    }

    /**
     * 记录性能指标
     * @param {string} type 指标类型
     * @param {number} value 指标值
     */
    recordPerformance(type, value) {
        if (!this.performanceMetrics[type]) {
            this.performanceMetrics[type] = [];
        }
        
        this.performanceMetrics[type].push({
            timestamp: Date.now(),
            value: value
        });
        
        // 保持最近100条记录
        if (this.performanceMetrics[type].length > 100) {
            this.performanceMetrics[type].shift();
        }
    }

    /**
     * 获取性能统计
     * @returns {Object} 性能统计信息
     */
    getPerformanceStats() {
        const stats = {};
        
        for (const [type, metrics] of Object.entries(this.performanceMetrics)) {
            if (metrics.length > 0) {
                const values = metrics.map(m => m.value);
                stats[type] = {
                    count: values.length,
                    average: values.reduce((a, b) => a + b, 0) / values.length,
                    min: Math.min(...values),
                    max: Math.max(...values),
                    latest: values[values.length - 1]
                };
            }
        }
        
        return stats;
    }

    /**
     * 导出数据
     * @param {string} format 导出格式
     * @returns {string} 导出的数据
     */
    exportData(format = 'json') {
        const exportData = {
            state: this.currentState,
            cache: Array.from(this.cache.entries()),
            performance: this.performanceMetrics,
            timestamp: new Date().toISOString()
        };
        
        switch (format) {
            case 'json':
                return JSON.stringify(exportData, null, 2);
            case 'csv':
                return this.convertToCSV(exportData);
            default:
                throw new Error(`不支持的导出格式: ${format}`);
        }
    }

    /**
     * 转换为CSV格式
     * @param {Object} data 数据
     * @returns {string} CSV字符串
     */
    convertToCSV(data) {
        // 简化的CSV转换
        const headers = ['Date', 'Sun RA', 'Sun Dec', 'Moon RA', 'Moon Dec', 'Sidereal Time'];
        const rows = [headers.join(',')];
        
        for (const [key, value] of data.cache) {
            if (value.sun && value.moon) {
                const row = [
                    value.date,
                    value.sun.rightAscension.toFixed(2),
                    value.sun.declination.toFixed(2),
                    value.moon.rightAscension.toFixed(2),
                    value.moon.declination.toFixed(2),
                    value.siderealTime.toFixed(2)
                ];
                rows.push(row.join(','));
            }
        }
        
        return rows.join('\n');
    }

    /**
     * 获取缓存统计信息
     * @returns {Object} 缓存统计
     */
    getCacheStats() {
        return {
            size: this.cache.size,
            maxSize: this.maxCacheSize,
            usage: (this.cache.size / this.maxCacheSize * 100).toFixed(1) + '%',
            keys: Array.from(this.cache.keys())
        };
    }

    /**
     * 清理过期缓存
     * @param {number} maxAge 最大年龄（毫秒）
     */
    cleanupCache(maxAge = 24 * 60 * 60 * 1000) { // 默认24小时
        const now = Date.now();
        const keysToDelete = [];
        
        for (const [key, value] of this.cache.entries()) {
            if (value.timestamp && (now - value.timestamp) > maxAge) {
                keysToDelete.push(key);
            }
        }
        
        keysToDelete.forEach(key => this.cache.delete(key));
        
        if (keysToDelete.length > 0) {
            this.notifyListeners('cacheCleanup', { deletedKeys: keysToDelete });
        }
    }
}

// 导出类供其他模块使用
window.DataManager = DataManager;
