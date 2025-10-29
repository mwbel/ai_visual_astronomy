// 主题切换与搜索过滤的轻量脚本
(function() {
  const toggleBtn = document.getElementById('toggleTheme');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const isDark = document.body.classList.contains('theme-dark');
      document.body.classList.toggle('theme-dark', !isDark);
      document.body.classList.toggle('theme-light', isDark);
    });
  }

  const searchInput = document.getElementById('searchInput');
  const cardsContainer = document.getElementById('cards');
  if (searchInput && cardsContainer) {
    const cards = Array.from(cardsContainer.querySelectorAll('.card'));
    const normalize = s => (s || '').toLowerCase().trim();
    searchInput.addEventListener('input', (e) => {
      const q = normalize(e.target.value);
      cards.forEach(card => {
        const title = normalize(card.querySelector('.card-title')?.textContent);
        const desc = normalize(card.querySelector('.card-desc')?.textContent);
        const kw = normalize(card.getAttribute('data-keywords'));
        const hit = !q || title.includes(q) || desc.includes(q) || kw.includes(q);
        card.style.display = hit ? '' : 'none';
      });
    });
  }
})();