/**
 * Three.js 3D天球可视化场景管理器
 * 实现3D天球坐标系统，天体渲染和交互控制
 */

class ThreeScene {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        // 天体对象
        this.celestialObjects = {
            sun: null,
            moon: null,
            earth: null,
            stars: [],
            constellations: []
        };
        
        // 场景参数
        this.sceneRadius = 100;
        this.animationId = null;
        this.isAnimating = false;
        
        // 当前视角模式
        this.viewMode = 'geocentric'; // geocentric, heliocentric, lunarcentric
        this.displayMode = '3d'; // 3d, 2d, starmap
        
        this.init();
    }

    /**
     * 初始化3D场景
     */
    init() {
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.createControls();
        this.createLights();
        this.createCelestialSphere();
        this.createCelestialObjects();
        this.createStarField();
        
        this.animate();
        this.handleResize();
    }

    /**
     * 创建场景
     */
    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000011);
        
        // 添加雾效果
        this.scene.fog = new THREE.Fog(0x000011, this.sceneRadius * 0.8, this.sceneRadius * 2);
    }

    /**
     * 创建相机
     */
    createCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, this.sceneRadius * 10);
        this.camera.position.set(0, 0, this.sceneRadius * 0.5);
        this.camera.lookAt(0, 0, 0);
    }

    /**
     * 创建渲染器
     */
    createRenderer() {
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true, 
            alpha: true,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        this.container.appendChild(this.renderer.domElement);
    }

    /**
     * 创建控制器
     */
    createControls() {
        // 检查OrbitControls是否可用
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.enableZoom = true;
            this.controls.enablePan = true;
            this.controls.maxDistance = this.sceneRadius * 2;
            this.controls.minDistance = this.sceneRadius * 0.1;
        } else {
            console.warn('OrbitControls not available, using basic mouse controls');
            this.setupBasicControls();
        }
    }

    /**
     * 设置基础控制器（备用方案）
     */
    setupBasicControls() {
        let isMouseDown = false;
        let mouseX = 0, mouseY = 0;

        this.renderer.domElement.addEventListener('mousedown', (event) => {
            isMouseDown = true;
            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        this.renderer.domElement.addEventListener('mouseup', () => {
            isMouseDown = false;
        });

        this.renderer.domElement.addEventListener('mousemove', (event) => {
            if (!isMouseDown) return;

            const deltaX = event.clientX - mouseX;
            const deltaY = event.clientY - mouseY;

            // 简单的相机旋转
            this.camera.position.x = this.sceneRadius * Math.cos(deltaX * 0.01);
            this.camera.position.z = this.sceneRadius * Math.sin(deltaX * 0.01);
            this.camera.position.y += deltaY * 0.1;

            this.camera.lookAt(0, 0, 0);

            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        // 滚轮缩放
        this.renderer.domElement.addEventListener('wheel', (event) => {
            const scale = event.deltaY > 0 ? 1.1 : 0.9;
            this.camera.position.multiplyScalar(scale);
            this.camera.lookAt(0, 0, 0);
            event.preventDefault();
        });
    }

    /**
     * 创建光源
     */
    createLights() {
        // 环境光
        const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
        this.scene.add(ambientLight);
        
        // 太阳光（方向光）
        const sunLight = new THREE.DirectionalLight(0xffffff, 1);
        sunLight.position.set(50, 0, 0);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 2048;
        sunLight.shadow.mapSize.height = 2048;
        this.scene.add(sunLight);
        
        // 点光源（用于月亮反射光）
        const moonLight = new THREE.PointLight(0x8888ff, 0.2, this.sceneRadius);
        moonLight.position.set(-30, 0, 0);
        this.scene.add(moonLight);
    }

    /**
     * 创建天球
     */
    createCelestialSphere() {
        const geometry = new THREE.SphereGeometry(this.sceneRadius, 64, 32);
        const material = new THREE.MeshBasicMaterial({
            color: 0x000033,
            transparent: true,
            opacity: 0.1,
            side: THREE.BackSide,
            wireframe: true
        });
        
        const celestialSphere = new THREE.Mesh(geometry, material);
        this.scene.add(celestialSphere);
        
        // 添加赤道和黄道
        this.createCoordinateGrids();
    }

    /**
     * 创建坐标网格
     */
    createCoordinateGrids() {
        // 赤道
        const equatorGeometry = new THREE.RingGeometry(this.sceneRadius * 0.98, this.sceneRadius * 1.02, 64);
        const equatorMaterial = new THREE.MeshBasicMaterial({
            color: 0x00ff00,
            transparent: true,
            opacity: 0.3,
            side: THREE.DoubleSide
        });
        const equator = new THREE.Mesh(equatorGeometry, equatorMaterial);
        equator.rotation.x = Math.PI / 2;
        this.scene.add(equator);
        
        // 黄道
        const eclipticGeometry = new THREE.RingGeometry(this.sceneRadius * 0.96, this.sceneRadius * 1.04, 64);
        const eclipticMaterial = new THREE.MeshBasicMaterial({
            color: 0xffff00,
            transparent: true,
            opacity: 0.3,
            side: THREE.DoubleSide
        });
        const ecliptic = new THREE.Mesh(eclipticGeometry, eclipticMaterial);
        ecliptic.rotation.x = Math.PI / 2;
        ecliptic.rotation.z = 23.5 * Math.PI / 180; // 黄赤交角
        this.scene.add(ecliptic);
    }

    /**
     * 创建天体对象
     */
    createCelestialObjects() {
        // 地球
        const earthGeometry = new THREE.SphereGeometry(2, 32, 16);
        const earthMaterial = new THREE.MeshPhongMaterial({
            color: 0x4488ff,
            shininess: 100
        });
        this.celestialObjects.earth = new THREE.Mesh(earthGeometry, earthMaterial);
        this.celestialObjects.earth.position.set(0, 0, 0);
        this.celestialObjects.earth.castShadow = true;
        this.celestialObjects.earth.receiveShadow = true;
        this.scene.add(this.celestialObjects.earth);
        
        // 太阳
        const sunGeometry = new THREE.SphereGeometry(5, 32, 16);
        const sunMaterial = new THREE.MeshBasicMaterial({
            color: 0xffff00,
            emissive: 0xffaa00,
            emissiveIntensity: 0.5
        });
        this.celestialObjects.sun = new THREE.Mesh(sunGeometry, sunMaterial);
        this.celestialObjects.sun.position.set(50, 0, 0);
        this.scene.add(this.celestialObjects.sun);
        
        // 太阳光晕效果
        const sunGlowGeometry = new THREE.SphereGeometry(8, 32, 16);
        const sunGlowMaterial = new THREE.MeshBasicMaterial({
            color: 0xffff00,
            transparent: true,
            opacity: 0.2
        });
        const sunGlow = new THREE.Mesh(sunGlowGeometry, sunGlowMaterial);
        this.celestialObjects.sun.add(sunGlow);
        
        // 月亮
        const moonGeometry = new THREE.SphereGeometry(1, 32, 16);
        const moonMaterial = new THREE.MeshPhongMaterial({
            color: 0xcccccc,
            shininess: 10
        });
        this.celestialObjects.moon = new THREE.Mesh(moonGeometry, moonMaterial);
        this.celestialObjects.moon.position.set(-30, 0, 0);
        this.celestialObjects.moon.castShadow = true;
        this.celestialObjects.moon.receiveShadow = true;
        this.scene.add(this.celestialObjects.moon);
    }

    /**
     * 创建星空背景
     */
    createStarField() {
        const starGeometry = new THREE.BufferGeometry();
        const starCount = 2000;
        const positions = new Float32Array(starCount * 3);
        const colors = new Float32Array(starCount * 3);
        
        for (let i = 0; i < starCount; i++) {
            // 在天球表面随机分布星星
            const phi = Math.random() * Math.PI * 2;
            const theta = Math.random() * Math.PI;
            const radius = this.sceneRadius * 0.95;
            
            positions[i * 3] = radius * Math.sin(theta) * Math.cos(phi);
            positions[i * 3 + 1] = radius * Math.sin(theta) * Math.sin(phi);
            positions[i * 3 + 2] = radius * Math.cos(theta);
            
            // 随机星星颜色
            const starColor = new THREE.Color();
            starColor.setHSL(Math.random() * 0.2 + 0.5, 0.5, Math.random() * 0.5 + 0.5);
            colors[i * 3] = starColor.r;
            colors[i * 3 + 1] = starColor.g;
            colors[i * 3 + 2] = starColor.b;
        }
        
        starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        starGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        
        const starMaterial = new THREE.PointsMaterial({
            size: 2,
            vertexColors: true,
            transparent: true,
            opacity: 0.8
        });
        
        const stars = new THREE.Points(starGeometry, starMaterial);
        this.scene.add(stars);
        this.celestialObjects.stars.push(stars);
    }

    /**
     * 更新天体位置
     * @param {Object} astronomyData 天文计算数据
     */
    updateCelestialPositions(astronomyData) {
        if (!astronomyData) return;
        
        // 更新太阳位置
        if (astronomyData.sun && this.celestialObjects.sun) {
            const sunPos = this.sphericalToCartesian(
                astronomyData.sun.rightAscension,
                astronomyData.sun.declination,
                this.sceneRadius * 0.5
            );
            this.celestialObjects.sun.position.copy(sunPos);
        }
        
        // 更新月亮位置
        if (astronomyData.moon && this.celestialObjects.moon) {
            const moonPos = this.sphericalToCartesian(
                astronomyData.moon.rightAscension,
                astronomyData.moon.declination,
                this.sceneRadius * 0.3
            );
            this.celestialObjects.moon.position.copy(moonPos);
            
            // 根据月相调整月亮材质
            const illumination = astronomyData.moon.illumination || 0.5;
            this.celestialObjects.moon.material.emissive.setScalar(illumination * 0.1);
        }
    }

    /**
     * 球坐标转笛卡尔坐标
     * @param {number} ra 赤经（度）
     * @param {number} dec 赤纬（度）
     * @param {number} distance 距离
     * @returns {THREE.Vector3} 笛卡尔坐标
     */
    sphericalToCartesian(ra, dec, distance) {
        const raRad = ra * Math.PI / 180;
        const decRad = dec * Math.PI / 180;
        
        const x = distance * Math.cos(decRad) * Math.cos(raRad);
        const y = distance * Math.cos(decRad) * Math.sin(raRad);
        const z = distance * Math.sin(decRad);
        
        return new THREE.Vector3(x, y, z);
    }

    /**
     * 切换视角模式
     * @param {string} mode 视角模式
     */
    setViewMode(mode) {
        this.viewMode = mode;
        
        switch (mode) {
            case 'geocentric':
                this.camera.position.set(0, 0, this.sceneRadius * 0.5);
                if (this.controls && this.controls.target) {
                    this.controls.target.set(0, 0, 0);
                }
                break;
            case 'heliocentric':
                if (this.celestialObjects.sun) {
                    const sunPos = this.celestialObjects.sun.position;
                    this.camera.position.set(sunPos.x, sunPos.y, sunPos.z + 20);
                    if (this.controls && this.controls.target) {
                        this.controls.target.copy(sunPos);
                    }
                }
                break;
            case 'lunarcentric':
                if (this.celestialObjects.moon) {
                    const moonPos = this.celestialObjects.moon.position;
                    this.camera.position.set(moonPos.x, moonPos.y, moonPos.z + 10);
                    if (this.controls && this.controls.target) {
                        this.controls.target.copy(moonPos);
                    }
                }
                break;
        }

        if (this.controls && this.controls.update) {
            this.controls.update();
        }
    }

    /**
     * 切换显示模式
     * @param {string} mode 显示模式
     */
    setDisplayMode(mode) {
        this.displayMode = mode;
        
        switch (mode) {
            case '3d':
                this.camera.fov = 75;
                break;
            case '2d':
                this.camera.fov = 45;
                break;
            case 'starmap':
                this.camera.fov = 90;
                break;
        }
        
        this.camera.updateProjectionMatrix();
    }

    /**
     * 重置视角
     */
    resetView() {
        this.camera.position.set(0, 0, this.sceneRadius * 0.5);
        if (this.controls && this.controls.target) {
            this.controls.target.set(0, 0, 0);
        }
        if (this.controls && this.controls.update) {
            this.controls.update();
        }
    }

    /**
     * 动画循环
     */
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());

        // 更新控制器（如果存在）
        if (this.controls && this.controls.update) {
            this.controls.update();
        }
        
        // 地球自转
        if (this.celestialObjects.earth) {
            this.celestialObjects.earth.rotation.y += 0.01;
        }
        
        // 星空缓慢旋转
        this.celestialObjects.stars.forEach(starField => {
            starField.rotation.y += 0.0001;
        });
        
        // 渲染场景
        this.renderer.render(this.scene, this.camera);
    }

    /**
     * 处理窗口大小变化
     */
    handleResize() {
        window.addEventListener('resize', () => {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            
            this.renderer.setSize(width, height);
        });
    }

    /**
     * 销毁场景
     */
    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.controls && this.controls.dispose) {
            this.controls.dispose();
        }
    }

    /**
     * 获取场景统计信息
     */
    getSceneInfo() {
        return {
            objects: this.scene.children.length,
            triangles: this.renderer.info.render.triangles,
            calls: this.renderer.info.render.calls,
            memory: this.renderer.info.memory
        };
    }
}

// 导出类供其他模块使用
window.ThreeScene = ThreeScene;
