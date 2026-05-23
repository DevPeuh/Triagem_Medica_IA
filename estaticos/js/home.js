const menuBtn = document.getElementById('menuBtn');
const navMenu = document.getElementById('navMenu');
const navLinks = [...document.querySelectorAll('.nav a[href^="#"]')];

if (menuBtn) {
  menuBtn.addEventListener('click', () => navMenu.classList.toggle('open'));
}

navLinks.forEach((link) => {
  link.addEventListener('click', () => navMenu.classList.remove('open'));
});

const sections = ['inicio', 'como-funciona', 'seguranca', 'ajuda']
  .map((id) => document.getElementById(id))
  .filter(Boolean);

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const id = entry.target.id;
      navLinks.forEach((l) => l.classList.remove('is-active'));
      const active = navLinks.find((l) => l.getAttribute('href') === `#${id}`);
      if (active) active.classList.add('is-active');
    });
  },
  { threshold: 0.42 }
);

sections.forEach((section) => observer.observe(section));

async function sincronizarSessao() {
  try {
    const resp = await fetch('/api/autenticacao/sessao/', { credentials: 'include' });
    if (!resp.ok) return;
    const dados = await resp.json();
    if (!dados.autenticado) return;

    const enterLink = document.querySelector('.js-enter-link');
    if (enterLink) {
      enterLink.textContent = 'Minha Triagem';
      enterLink.href = '/chat-teste/';
    }

    document.querySelectorAll('.js-start-link').forEach((link) => {
      link.href = '/chat-teste/';
      link.innerHTML = 'Ir para Triagem <span>›</span>';
    });
  } catch (_) {
    // Falha silenciosa para não quebrar a home.
  }
}

sincronizarSessao();

if (window.lucide && typeof window.lucide.createIcons === 'function') {
  window.lucide.createIcons();
}