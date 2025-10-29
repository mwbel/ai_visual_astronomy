/**
 * UI控制模块
 * 处理用户界面交互和控制面板功能
 */

class UIControls {
    constructor(threeScene, astronomyCalculator, dataManager, demoDataProvider = null) {
        this.threeScene = threeScene;
        this.astronomyCalculator = astronomyCalculator;
        this.dataManager = dataManager;
        this.demoDataProvider = demoDataProvider;
        
        // 播放状态
        this.isPlaying = false;
        this.playbackSpeed = 1;
        this.currentDate = new Date('2024-01-01');
        this.animationInterval = null;
        
        // UI元素引用
        this.elements = {};
        
        this.initializeElements();
        this.bindEvents();
        this.updateUI();
    }

    /**
     * 初始化UI元素引用
     */
    initializeElements() {
        // 日期控制
        this.elements.dateInput = document.getElementById('dateInput');
        this.elements.timeInput = document.getElementById('timeInput');
        
        // 术语选择
        this.elements.termSelect = document.getElementById('termSelect');
        
        // 播放控制
        this.elements.prevBtn = document.getElementById('prevBtn');
        this.elements.playPauseBtn = document.getElementById('playPauseBtn');
        this.elements.nextBtn = document.getElementById('nextBtn');
        this.elements.speedSlider = document.getElementById('speedSlider');
        this.elements.speedValue = document.getElementById('speedValue');
        
        // 视角控制
        this.elements.geocentricBtn = document.getElementById('geocentricBtn');
        this.elements.heliocentricBtn = document.getElementById('heliocentricBtn');
        this.elements.lunarcentricBtn = document.getElementById('lunarcentricBtn');
        
        // 显示模式
        this.elements.mode3dBtn = document.getElementById('mode3dBtn');
        this.elements.mode2dBtn = document.getElementById('mode2dBtn');
        this.elements.starMapBtn = document.getElementById('starMapBtn');
        
        // 可视化控制
        this.elements.resetViewBtn = document.getElementById('resetViewBtn');
        this.elements.fullscreenBtn = document.getElementById('fullscreenBtn');
        
        // 时间轴
        this.elements.timelineSlider = document.getElementById('timelineSlider');
        this.elements.timelineStart = document.getElementById('timelineStart');
        this.elements.timelineEnd = document.getElementById('timelineEnd');
        
        // 数据显示
        this.elements.currentDate = document.getElementById('currentDate');
        this.elements.siderealTime = document.getElementById('siderealTime');
        this.elements.solarTime = document.getElementById('solarTime');
        this.elements.sunRA = document.getElementById('sunRA');
        this.elements.sunDec = document.getElementById('sunDec');
        this.elements.moonRA = document.getElementById('moonRA');
        this.elements.moonDec = document.getElementById('moonDec');
        this.elements.timeDifference = document.getElementById('timeDifference');
        this.elements.termExplanation = document.getElementById('termExplanation');
        
        // 模态对话框
        this.elements.settingsModal = document.getElementById('settingsModal');
        this.elements.helpModal = document.getElementById('helpModal');
        this.elements.settingsBtn = document.getElementById('settingsBtn');
        this.elements.helpBtn = document.getElementById('helpBtn');
        this.elements.exportBtn = document.getElementById('exportBtn');
        
        // 设置项
        this.elements.locationLat = document.getElementById('locationLat');
        this.elements.locationLon = document.getElementById('locationLon');
        this.elements.locationAlt = document.getElementById('locationAlt');
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 日期时间控制
        this.elements.dateInput?.addEventListener('change', (e) => {
            this.setDate(new Date(e.target.value));
        });
        
        this.elements.timeInput?.addEventListener('change', (e) => {
            const [hours, minutes] = e.target.value.split(':');
            const newDate = new Date(this.currentDate);
            newDate.setHours(parseInt(hours), parseInt(minutes));
            this.setDate(newDate);
        });
        
        // 术语选择
        this.elements.termSelect?.addEventListener('change', (e) => {
            this.showTermExplanation(e.target.value);
        });
        
        // 播放控制
        this.elements.prevBtn?.addEventListener('click', () => this.previousDay());
        this.elements.playPauseBtn?.addEventListener('click', () => this.togglePlayback());
        this.elements.nextBtn?.addEventListener('click', () => this.nextDay());
        
        this.elements.speedSlider?.addEventListener('input', (e) => {
            this.setPlaybackSpeed(parseFloat(e.target.value));
        });
        
        // 视角控制
        this.elements.geocentricBtn?.addEventListener('click', () => this.setViewMode('geocentric'));
        this.elements.heliocentricBtn?.addEventListener('click', () => this.setViewMode('heliocentric'));
        this.elements.lunarcentricBtn?.addEventListener('click', () => this.setViewMode('lunarcentric'));
        
        // 显示模式
        this.elements.mode3dBtn?.addEventListener('click', () => this.setDisplayMode('3d'));
        this.elements.mode2dBtn?.addEventListener('click', () => this.setDisplayMode('2d'));
        this.elements.starMapBtn?.addEventListener('click', () => this.setDisplayMode('starmap'));
        
        // 可视化控制
        this.elements.resetViewBtn?.addEventListener('click', () => this.threeScene.resetView());
        this.elements.fullscreenBtn?.addEventListener('click', () => this.toggleFullscreen());
        
        // 时间轴
        this.elements.timelineSlider?.addEventListener('input', (e) => {
            const dayOffset = parseInt(e.target.value);
            const startDate = new Date('2024-01-01');
            const newDate = new Date(startDate);
            newDate.setDate(startDate.getDate() + dayOffset);
            this.setDate(newDate);
        });
        
        // 模态对话框
        this.elements.settingsBtn?.addEventListener('click', () => this.showModal('settings'));
        this.elements.helpBtn?.addEventListener('click', () => this.showModal('help'));
        this.elements.exportBtn?.addEventListener('click', () => this.exportData());
        
        // 关闭模态对话框
        document.querySelectorAll('.close').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                e.target.closest('.modal').style.display = 'none';
            });
        });
        
        // 点击模态对话框外部关闭
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    /**
     * 设置当前日期
     * @param {Date} date 新日期
     */
    setDate(date) {
        this.currentDate = new Date(date);
        this.updateUI();
        this.updateAstronomyData();
    }

    /**
     * 切换播放/暂停
     */
    togglePlayback() {
        this.isPlaying = !this.isPlaying;
        
        if (this.isPlaying) {
            this.elements.playPauseBtn.textContent = '⏸️';
            this.startAnimation();
        } else {
            this.elements.playPauseBtn.textContent = '▶️';
            this.stopAnimation();
        }
    }

    /**
     * 开始动画
     */
    startAnimation() {
        const intervalMs = 1000 / this.playbackSpeed;
        
        this.animationInterval = setInterval(() => {
            const newDate = new Date(this.currentDate);
            newDate.setDate(newDate.getDate() + 1);
            this.setDate(newDate);
        }, intervalMs);
    }

    /**
     * 停止动画
     */
    stopAnimation() {
        if (this.animationInterval) {
            clearInterval(this.animationInterval);
            this.animationInterval = null;
        }
    }

    /**
     * 设置播放速度
     * @param {number} speed 播放速度
     */
    setPlaybackSpeed(speed) {
        this.playbackSpeed = speed;
        this.elements.speedValue.textContent = `${speed}x`;
        
        if (this.isPlaying) {
            this.stopAnimation();
            this.startAnimation();
        }
    }

    /**
     * 前一天
     */
    previousDay() {
        const newDate = new Date(this.currentDate);
        newDate.setDate(newDate.getDate() - 1);
        this.setDate(newDate);
    }

    /**
     * 后一天
     */
    nextDay() {
        const newDate = new Date(this.currentDate);
        newDate.setDate(newDate.getDate() + 1);
        this.setDate(newDate);
    }

    /**
     * 设置视角模式
     * @param {string} mode 视角模式
     */
    setViewMode(mode) {
        // 更新按钮状态
        document.querySelectorAll('.btn-view').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`${mode}Btn`)?.classList.add('active');
        
        // 设置3D场景视角
        this.threeScene.setViewMode(mode);
    }

    /**
     * 设置显示模式
     * @param {string} mode 显示模式
     */
    setDisplayMode(mode) {
        // 更新按钮状态
        document.querySelectorAll('.btn-mode').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`mode${mode === '3d' ? '3d' : mode === '2d' ? '2d' : 'starMap'}Btn`)?.classList.add('active');
        
        // 设置3D场景显示模式
        this.threeScene.setDisplayMode(mode);
    }

    /**
     * 显示术语解释
     * @param {string} termKey 术语键值
     */
    showTermExplanation(termKey) {
        if (!termKey) {
            this.elements.termExplanation.innerHTML = '<p>选择左侧术语查看详细解释...</p>';
            return;
        }

        // 优先使用增强的术语解释
        const explanation = this.demoDataProvider ?
            this.demoDataProvider.getEnhancedTermExplanation(termKey) :
            this.astronomyCalculator.getTermExplanation(termKey);

        let html = `
            <h4>${explanation.title}</h4>
            <p>${explanation.description}</p>
            <div class="term-details">
                <small>${explanation.details}</small>
            </div>
        `;

        // 添加公式（如果有）
        if (explanation.formula) {
            html += `
                <div class="term-formula">
                    <strong>公式：</strong><code>${explanation.formula}</code>
                </div>
            `;
        }

        // 添加意义说明（如果有）
        if (explanation.significance) {
            html += `
                <div class="term-significance">
                    <strong>意义：</strong>${explanation.significance}
                </div>
            `;
        }

        // 添加相关术语（如果有）
        if (explanation.relatedTerms && explanation.relatedTerms.length > 0) {
            html += `
                <div class="related-terms">
                    <strong>相关术语：</strong>
                    ${explanation.relatedTerms.map(term => `<span class="related-term">${term}</span>`).join(', ')}
                </div>
            `;
        }

        this.elements.termExplanation.innerHTML = html;
    }

    /**
     * 更新天文数据
     */
    updateAstronomyData() {
        // 计算太阳位置
        const sunPosition = this.astronomyCalculator.calculateSunPosition(this.currentDate);
        
        // 计算月亮位置
        const moonPosition = this.astronomyCalculator.calculateMoonPosition(this.currentDate);
        
        // 计算恒星时
        const siderealTime = this.astronomyCalculator.calculateSiderealTime(this.currentDate);
        
        // 更新3D场景
        this.threeScene.updateCelestialPositions({
            sun: sunPosition,
            moon: moonPosition
        });
        
        // 更新数据显示
        this.updateDataDisplay(sunPosition, moonPosition, siderealTime);
        
        // 通知数据管理器
        this.dataManager.updateData({
            date: this.currentDate,
            sun: sunPosition,
            moon: moonPosition,
            siderealTime: siderealTime
        });
    }

    /**
     * 更新数据显示
     */
    updateDataDisplay(sunPosition, moonPosition, siderealTime) {
        // 更新实时数据
        if (this.elements.currentDate) {
            this.elements.currentDate.textContent = this.currentDate.toLocaleDateString('zh-CN');
        }
        
        if (this.elements.siderealTime) {
            const hours = Math.floor(siderealTime);
            const minutes = Math.floor((siderealTime - hours) * 60);
            const seconds = Math.floor(((siderealTime - hours) * 60 - minutes) * 60);
            this.elements.siderealTime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        if (this.elements.solarTime) {
            this.elements.solarTime.textContent = this.currentDate.toLocaleTimeString('zh-CN');
        }
        
        // 更新天体位置
        if (this.elements.sunRA && sunPosition) {
            this.elements.sunRA.textContent = `${sunPosition.rightAscension.toFixed(1)}°`;
        }
        
        if (this.elements.sunDec && sunPosition) {
            this.elements.sunDec.textContent = `${sunPosition.declination.toFixed(1)}°`;
        }
        
        if (this.elements.moonRA && moonPosition) {
            this.elements.moonRA.textContent = `${moonPosition.rightAscension.toFixed(1)}°`;
        }
        
        if (this.elements.moonDec && moonPosition) {
            this.elements.moonDec.textContent = `${moonPosition.declination.toFixed(1)}°`;
        }
        
        // 计算时间差
        const startOfYear = new Date(this.currentDate.getFullYear(), 0, 1);
        const daysDiff = Math.floor((this.currentDate - startOfYear) / (1000 * 60 * 60 * 24));
        const timeDiff = daysDiff * (this.astronomyCalculator.SOLAR_DAY_HOURS - this.astronomyCalculator.SIDEREAL_DAY_HOURS) * 60;
        
        if (this.elements.timeDifference) {
            this.elements.timeDifference.textContent = `${timeDiff.toFixed(1)} 分钟`;
        }
    }

    /**
     * 更新UI界面
     */
    updateUI() {
        // 更新日期输入框
        if (this.elements.dateInput) {
            this.elements.dateInput.value = this.currentDate.toISOString().split('T')[0];
        }
        
        if (this.elements.timeInput) {
            const hours = this.currentDate.getHours().toString().padStart(2, '0');
            const minutes = this.currentDate.getMinutes().toString().padStart(2, '0');
            this.elements.timeInput.value = `${hours}:${minutes}`;
        }
        
        // 更新时间轴
        if (this.elements.timelineSlider) {
            const startOfYear = new Date(this.currentDate.getFullYear(), 0, 1);
            const dayOfYear = Math.floor((this.currentDate - startOfYear) / (1000 * 60 * 60 * 24));
            this.elements.timelineSlider.value = dayOfYear;
        }
    }

    /**
     * 显示模态对话框
     * @param {string} type 对话框类型
     */
    showModal(type) {
        const modal = document.getElementById(`${type}Modal`);
        if (modal) {
            modal.style.display = 'block';
        }
    }

    /**
     * 切换全屏模式
     */
    toggleFullscreen() {
        const container = this.threeScene.container;
        
        if (!document.fullscreenElement) {
            container.requestFullscreen().catch(err => {
                console.error('无法进入全屏模式:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * 导出数据
     */
    exportData() {
        // 这里可以实现数据导出功能
        console.log('导出功能待实现');
        alert('导出功能正在开发中...');
    }

    /**
     * 处理键盘快捷键
     * @param {KeyboardEvent} e 键盘事件
     */
    handleKeyboard(e) {
        switch (e.key) {
            case ' ':
                e.preventDefault();
                this.togglePlayback();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.previousDay();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.nextDay();
                break;
            case 'r':
                if (e.ctrlKey) {
                    e.preventDefault();
                    this.threeScene.resetView();
                }
                break;
            case 'f':
                if (e.ctrlKey) {
                    e.preventDefault();
                    this.toggleFullscreen();
                }
                break;
        }
    }
}

// 导出类供其他模块使用
window.UIControls = UIControls;
