// 初始化场景
const scene = new THREE.Scene();

// 初始化场景
const scene = new THREE.Scene();

// 初始化相机
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 20; // 将相机拉得更远一些，以便更好地观察整个太阳系

// 初始化渲染器
const renderer = new THREE.WebGLRenderer({ antialias: true }); // 开启抗锯齿
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('app').appendChild(renderer.domElement);

// 添加 OrbitControls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; // 启用阻尼（惯性），使动画更平滑
controls.dampingFactor = 0.25;
controls.screenSpacePanning = false;
controls.maxPolarAngle = Math.PI / 2; // 限制垂直旋转角度，防止翻转

// 添加光源
const ambientLight = new THREE.AmbientLight(0x333333); // 环境光
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0xffffff, 2, 100); // 点光源，模拟太阳发光
pointLight.position.set(0, 0, 0); // 太阳在原点，光源也放在原点
scene.add(pointLight);

// 添加太阳
const sunGeometry = new THREE.SphereGeometry(1, 32, 32); // 半径1，分段数32
const sunMaterial = new THREE.MeshBasicMaterial({ color: 0xffff00 }); // 黄色
const sun = new THREE.Mesh(sunGeometry, sunMaterial);
scene.add(sun);

// 行星数据 (简化数据，实际应从后端获取或更精确计算)
const planetsData = [
    { name: '水星', radius: 0.2, color: 0x888888, orbitRadius: 3, orbitSpeed: 0.04 }, // 调整半径和轨道半径
    { name: '金星', radius: 0.3, color: 0xddccaa, orbitRadius: 5, orbitSpeed: 0.015 },
    { name: '地球', radius: 0.35, color: 0x0000ff, orbitRadius: 7, orbitSpeed: 0.01 },
    { name: '火星', radius: 0.25, color: 0xff0000, orbitRadius: 9, orbitSpeed: 0.008 },
];

const planets = [];

planetsData.forEach(data => {
    const geometry = new THREE.SphereGeometry(data.radius, 32, 32);
    const material = new THREE.MeshStandardMaterial({ color: data.color }); // 使用标准材质以响应光源
    const planet = new THREE.Mesh(geometry, material);
    planet.position.x = data.orbitRadius; // 初始位置
    scene.add(planet);
    planets.push({ mesh: planet, data: data, angle: 0 }); // 存储行星网格、数据和当前角度
});

// Raycaster 用于检测点击
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

// 信息面板元素
const infoPanel = document.getElementById('info-panel');
const planetName = document.getElementById('planet-name');
const planetRadius = document.getElementById('planet-radius');
const planetColor = document.getElementById('planet-color');
const planetOrbitRadius = document.getElementById('planet-orbit-radius');

// 动画循环
function animate() {
    requestAnimationFrame(animate);

    controls.update(); // 更新控制器

    // 太阳不旋转，或者可以添加自转
    // sun.rotation.y += 0.001; 

    // 更新行星位置
    planets.forEach(planet => {
        planet.angle += planet.data.orbitSpeed;
        planet.mesh.position.x = planet.data.orbitRadius * Math.cos(planet.angle);
        planet.mesh.position.z = planet.data.orbitRadius * Math.sin(planet.angle);
    });

    renderer.render(scene, camera);
}

animate();

// 窗口大小调整处理
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// 鼠标点击事件处理
window.addEventListener('click', (event) => {
    // 将鼠标坐标归一化到 [-1, 1] 范围
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    // 通过相机和鼠标位置更新 Raycaster
    raycaster.setFromCamera(mouse, camera);

    // 计算物体和射线的交点
    const intersects = raycaster.intersectObjects(planets.map(p => p.mesh));

    if (intersects.length > 0) {
        // 找到了被点击的行星
        const clickedPlanetMesh = intersects[0].object;
        const clickedPlanet = planets.find(p => p.mesh === clickedPlanetMesh);

        if (clickedPlanet) {
            planetName.textContent = clickedPlanet.data.name;
            planetRadius.textContent = clickedPlanet.data.radius;
            planetColor.textContent = '#' + clickedPlanet.data.color.toString(16);
            planetOrbitRadius.textContent = clickedPlanet.data.orbitRadius;
            infoPanel.style.display = 'block'; // 显示信息面板
        }
    } else {
        infoPanel.style.display = 'none'; // 隐藏信息面板
    }
});
