/**
 * 主应用程序入口
 * 初始化所有模块并协调它们之间的交互
 */

class TibetanAstronomyApp {
    constructor() {
        this.modules = {};
        this.isInitialized = false;
        this.errorHandler = new ErrorHandler();
        
        // 应用配置
        this.config = {
            debug: false,
            autoSave: true,
            performanceMonitoring: true,
            maxFPS: 60
        };
        
        this.init();
    }

    /**
     * 初始化应用程序
     */
    async init() {
        try {
            this.showLoadingScreen();
            
            // 检查浏览器兼容性
            if (!this.checkCompatibility()) {
                this.showCompatibilityError();
                return;
            }
            
            // 初始化模块
            await this.initializeModules();
            
            // 设置模块间通信
            this.setupModuleCommunication();
            
            // 启动应用
            this.startApplication();
            
            this.hideLoadingScreen();
            this.isInitialized = true;
            
            console.log('藏历天文历算可视化工具初始化完成');
            
        } catch (error) {
            this.errorHandler.handleError(error);
            this.showInitializationError(error);
        }
    }

    /**
     * 检查浏览器兼容性
     */
    checkCompatibility() {
        try {
            const requirements = {
                webgl: !!window.WebGLRenderingContext,
                es6: typeof Symbol !== 'undefined',
                requestAnimationFrame: !!window.requestAnimationFrame,
                localStorage: !!window.localStorage,
                three: typeof THREE !== 'undefined'
            };

            const missing = Object.entries(requirements)
                .filter(([key, supported]) => !supported)
                .map(([key]) => key);

            if (missing.length > 0) {
                console.error('浏览器不支持以下功能:', missing);
                return false;
            }

            return true;
        } catch (error) {
            console.error('兼容性检查失败:', error);
            return false;
        }
    }

    /**
     * 初始化所有模块
     */
    async initializeModules() {
        try {
            console.log('开始初始化模块...');

            // 初始化数据管理器
            console.log('初始化数据管理器...');
            this.modules.dataManager = new DataManager();

            // 初始化天文计算器
            console.log('初始化天文计算器...');
            this.modules.astronomyCalculator = new AstronomyCalculator();

            // 初始化演示数据提供器
            console.log('初始化演示数据提供器...');
            this.modules.demoDataProvider = new DemoDataProvider();

            // 检查Three.js容器是否存在
            const container = document.getElementById('threejs-container');
            if (!container) {
                throw new Error('找不到3D容器元素 #threejs-container');
            }

            // 初始化3D场景
            console.log('初始化3D场景...');
            this.modules.threeScene = new ThreeScene('threejs-container');

            // 初始化UI控制器
            console.log('初始化UI控制器...');
            this.modules.uiControls = new UIControls(
                this.modules.threeScene,
                this.modules.astronomyCalculator,
                this.modules.dataManager,
                this.modules.demoDataProvider
            );

            // 初始化时间轴控制器
            console.log('初始化时间轴控制器...');
            this.modules.timelineController = new TimelineController(
                this.modules.dataManager,
                this.modules.uiControls
            );

            // 等待所有模块初始化完成
            console.log('等待模块准备就绪...');
            await this.waitForModulesReady();

            console.log('所有模块初始化完成');
        } catch (error) {
            console.error('模块初始化失败:', error);
            throw error;
        }
    }

    /**
     * 等待模块准备就绪
     */
    async waitForModulesReady() {
        return new Promise((resolve) => {
            // 简单的延迟，实际应用中可以检查各模块的就绪状态
            setTimeout(resolve, 1000);
        });
    }

    /**
     * 设置模块间通信
     */
    setupModuleCommunication() {
        const { dataManager, threeScene, uiControls, astronomyCalculator } = this.modules;
        
        // 数据更新事件
        dataManager.addEventListener('dataUpdated', (data) => {
            threeScene.updateCelestialPositions(data);
        });
        
        // 状态变化事件
        dataManager.addEventListener('stateChanged', (event) => {
            this.handleStateChange(event);
        });
        
        // 性能监控
        if (this.config.performanceMonitoring) {
            this.setupPerformanceMonitoring();
        }
        
        // 错误处理
        this.setupErrorHandling();
    }

    /**
     * 设置性能监控
     */
    setupPerformanceMonitoring() {
        const { dataManager, threeScene } = this.modules;
        
        // 监控渲染性能
        let lastFrameTime = performance.now();
        const monitorFrame = () => {
            const currentTime = performance.now();
            const frameTime = currentTime - lastFrameTime;
            lastFrameTime = currentTime;
            
            dataManager.recordPerformance('render', frameTime);
            
            requestAnimationFrame(monitorFrame);
        };
        
        requestAnimationFrame(monitorFrame);
        
        // 定期输出性能统计
        setInterval(() => {
            if (this.config.debug) {
                console.log('性能统计:', dataManager.getPerformanceStats());
                console.log('场景信息:', threeScene.getSceneInfo());
            }
        }, 10000); // 每10秒输出一次
    }

    /**
     * 设置错误处理
     */
    setupErrorHandling() {
        // 全局错误处理
        window.addEventListener('error', (event) => {
            this.errorHandler.handleError(event.error);
        });
        
        // Promise错误处理
        window.addEventListener('unhandledrejection', (event) => {
            this.errorHandler.handleError(event.reason);
        });
    }

    /**
     * 处理状态变化
     */
    handleStateChange(event) {
        const { oldState, newState } = event;
        
        // 自动保存
        if (this.config.autoSave) {
            this.modules.dataManager.saveState();
        }
        
        // 记录状态变化
        if (this.config.debug) {
            console.log('状态变化:', { oldState, newState });
        }
    }

    /**
     * 启动应用程序
     */
    startApplication() {
        // 设置初始日期
        const initialDate = new Date('2024-01-01');
        this.modules.uiControls.setDate(initialDate);
        
        // 启动自动清理
        this.startAutomaticCleanup();
        
        // 注册服务工作者（如果支持）
        this.registerServiceWorker();
    }

    /**
     * 启动自动清理
     */
    startAutomaticCleanup() {
        // 每小时清理一次过期缓存
        setInterval(() => {
            this.modules.dataManager.cleanupCache();
        }, 60 * 60 * 1000);
    }

    /**
     * 注册服务工作者
     */
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('Service Worker 注册成功:', registration);
                })
                .catch(error => {
                    console.log('Service Worker 注册失败:', error);
                });
        }
    }

    /**
     * 显示加载屏幕
     */
    showLoadingScreen() {
        const loadingHTML = `
            <div id="loading-screen" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #0c1445 0%, #1a1a2e 50%, #16213e 100%);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                color: white;
                font-family: 'Segoe UI', sans-serif;
            ">
                <div style="
                    width: 60px;
                    height: 60px;
                    border: 3px solid rgba(79, 172, 254, 0.3);
                    border-top: 3px solid #4facfe;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 20px;
                "></div>
                <h2 style="margin: 0; font-size: 1.5rem; margin-bottom: 10px;">藏历天文历算可视化工具</h2>
                <p style="margin: 0; opacity: 0.7;">正在初始化...</p>
                <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', loadingHTML);
    }

    /**
     * 隐藏加载屏幕
     */
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.style.opacity = '0';
            loadingScreen.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                loadingScreen.remove();
            }, 500);
        }
    }

    /**
     * 显示兼容性错误
     */
    showCompatibilityError() {
        document.body.innerHTML = `
            <div style="
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background: #1a1a2e;
                color: white;
                font-family: 'Segoe UI', sans-serif;
                text-align: center;
                padding: 20px;
            ">
                <h1 style="color: #ff6b6b; margin-bottom: 20px;">浏览器不兼容</h1>
                <p style="margin-bottom: 20px; max-width: 600px; line-height: 1.6;">
                    您的浏览器不支持运行此应用程序所需的功能。
                    请使用现代浏览器，如 Chrome 90+、Firefox 88+、Safari 14+ 或 Edge 90+。
                </p>
                <button onclick="location.reload()" style="
                    background: #4facfe;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                ">重新尝试</button>
            </div>
        `;
    }

    /**
     * 显示初始化错误
     */
    showInitializationError(error) {
        console.error('初始化错误:', error);
        
        const errorHTML = `
            <div style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 30px;
                border-radius: 10px;
                border: 1px solid #ff6b6b;
                max-width: 500px;
                text-align: center;
                z-index: 10000;
            ">
                <h2 style="color: #ff6b6b; margin-bottom: 15px;">初始化失败</h2>
                <p style="margin-bottom: 20px;">应用程序初始化时发生错误，请刷新页面重试。</p>
                <button onclick="location.reload()" style="
                    background: #4facfe;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-right: 10px;
                ">刷新页面</button>
                <button onclick="this.parentElement.remove()" style="
                    background: transparent;
                    color: #ccc;
                    border: 1px solid #ccc;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                ">关闭</button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', errorHTML);
    }

    /**
     * 获取应用程序状态
     */
    getAppState() {
        return {
            initialized: this.isInitialized,
            modules: Object.keys(this.modules),
            config: this.config,
            performance: this.modules.dataManager?.getPerformanceStats()
        };
    }

    /**
     * 销毁应用程序
     */
    destroy() {
        // 停止所有动画和定时器
        if (this.modules.threeScene) {
            this.modules.threeScene.dispose();
        }
        
        if (this.modules.uiControls) {
            this.modules.uiControls.stopAnimation();
        }
        
        // 清理事件监听器
        if (this.modules.dataManager) {
            this.modules.dataManager.clearCache();
        }
        
        console.log('应用程序已销毁');
    }
}

/**
 * 简单的错误处理器
 */
class ErrorHandler {
    handleError(error) {
        console.error('应用程序错误:', error);
        
        // 这里可以添加错误报告逻辑
        // 例如发送到错误监控服务
    }
}

/**
 * 时间轴控制器
 */
class TimelineController {
    constructor(dataManager, uiControls) {
        this.dataManager = dataManager;
        this.uiControls = uiControls;
        this.isAnimating = false;
        
        this.setupTimelineMarkers();
    }

    setupTimelineMarkers() {
        const markersContainer = document.querySelector('.timeline-markers');
        if (!markersContainer) return;
        
        // 添加季节标记
        const seasons = [
            { name: '春分', day: 80 },
            { name: '夏至', day: 172 },
            { name: '秋分', day: 266 },
            { name: '冬至', day: 355 }
        ];
        
        seasons.forEach(season => {
            const marker = document.createElement('div');
            marker.className = 'timeline-marker';
            marker.style.cssText = `
                position: absolute;
                left: ${(season.day / 365) * 100}%;
                top: -20px;
                font-size: 0.7rem;
                color: #4facfe;
                transform: translateX(-50%);
            `;
            marker.textContent = season.name;
            markersContainer.appendChild(marker);
        });
    }
}

// 当DOM加载完成后启动应用程序
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TibetanAstronomyApp();
});

// 导出主应用类
window.TibetanAstronomyApp = TibetanAstronomyApp;
