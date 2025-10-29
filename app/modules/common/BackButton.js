// BackButton.js: 返回模块主页按钮
(function(global){
  function renderBackButton(containerSelector, href){
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const btn = document.createElement('a');
    btn.className = 'btn';
    btn.textContent = '返回模块主页';
    btn.href = href || '/modern-astronomy/';
    container.appendChild(btn);
  }
  global.BackButton = { renderBackButton };
})(window);