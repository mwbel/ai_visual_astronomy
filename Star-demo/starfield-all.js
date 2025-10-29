/**
 * 在指定 three.js 场景中添加星空效果
 * @param {THREE.Scene} scene - three.js 场景对象
 * @param {number} [starsCount=2000] - 星星数量，可选
 * @param {number} [spaceSize=100] - 星星分布空间大小，可选
 */
function addStarField(scene, starsCount = 2000, spaceSize = 100) {
  const starsGeometry = new THREE.BufferGeometry();
  const positions = new Float32Array(starsCount * 3);

  for (let i = 0; i < starsCount * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * spaceSize; // x
    positions[i + 1] = (Math.random() - 0.5) * spaceSize; // y
    positions[i + 2] = (Math.random() - 0.5) * spaceSize; // z
  }

  starsGeometry.setAttribute(
    "position",
    new THREE.BufferAttribute(positions, 3)
  );

  const starsMaterial = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 0.1,
    transparent: true,
    opacity: 0.9,
    sizeAttenuation: true,
  });

  const starField = new THREE.Points(starsGeometry, starsMaterial);
  scene.add(starField);
}

// 引入 three.js 后可直接运行本文件
window.onload = function () {
  // 创建场景
  const scene = new THREE.Scene();

  // 创建相机
  const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
  );
  camera.position.set(0, 0, 10);

  // 创建渲染器
  const renderer = new THREE.WebGLRenderer();
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);

  // 添加轨道控制器（需要引入 OrbitControls.js）
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  // 调用星空效果
  addStarField(scene);

  // 渲染循环
  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  // 响应窗口大小变化
  window.addEventListener("resize", function () {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
};