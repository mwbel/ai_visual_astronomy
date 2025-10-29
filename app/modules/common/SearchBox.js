// SearchBox.js: 模块主页术语卡片过滤
(function(global){
  function initSearchBox(inputSelector, cardsContainerSelector){
    const input = document.querySelector(inputSelector);
    const container = document.querySelector(cardsContainerSelector);
    if (!input || !container) return;
    const cards = Array.from(container.querySelectorAll('.card'));
    const normalize = s => (s||'').toLowerCase();
    input.addEventListener('input', e => {
      const q = normalize(e.target.value.trim());
      cards.forEach(card => {
        const title = normalize(card.querySelector('.card-title')?.textContent);
        const desc = normalize(card.querySelector('.card-desc')?.textContent);
        const kw = normalize(card.getAttribute('data-keywords'));
        const hit = !q || title.includes(q) || desc.includes(q) || kw.includes(q);
        card.style.display = hit ? '' : 'none';
      });
    });
  }
  global.SearchBox = { initSearchBox };
})(window);