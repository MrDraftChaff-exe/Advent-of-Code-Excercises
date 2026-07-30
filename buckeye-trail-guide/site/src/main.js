import './style.css';
import { brand, products } from './catalog.js';

const app = document.querySelector('#app');

app.innerHTML = `
  <div class="atmosphere" aria-hidden="true"></div>

  <header class="top">
    <a class="logo" href="#">
      <img class="logo-mark" src="/gumroad-avatar.png" width="40" height="40" alt="" />
      ${brand.name}
    </a>
    <nav>
      <a href="#kits">Guides</a>
      <a class="nav-cta" href="#kits">Browse guides</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <img class="hero-mark" src="/gumroad-avatar.png" width="120" height="120" alt="${brand.name}" />
      <p class="brand-mark">${brand.name}</p>
      <h1>${brand.tagline}</h1>
      <p class="lede">${brand.description}</p>
      <div class="cta-row">
        <a class="btn primary" href="#kits">Browse guides</a>
        <a class="btn ghost" href="#how">How it works</a>
      </div>
    </section>

    <section id="how" class="how">
      <h2>One job: make the next step obvious.</h2>
      <p>
        Each guide is a short, practical download — checklists, plans, and worksheets
        spanning personal life, professional life, and anything that makes the next step easier.
      </p>
    </section>

    <section id="kits" class="kits">
      <h2>Guides</h2>
      <div class="kit-list">
        ${products
          .map(
            (p, i) => `
          <article class="kit" style="--i:${i}">
            <img class="kit-cover" src="${p.cover}" alt="" width="160" height="120" />
            <div class="kit-copy">
              <p class="kit-price">$${p.price}</p>
              <h3>${p.title}</h3>
              <p class="kit-sub">${p.subtitle}</p>
              <p>${p.blurb}</p>
            </div>
            <a class="btn primary" href="${p.gumroad}">Buy — $${p.price}</a>
          </article>`
          )
          .join('')}
      </div>
    </section>
  </main>

  <footer class="foot">
    <p><strong>${brand.name}</strong> · Curated by ${brand.curator} · ${brand.city}</p>
    <p class="fine">Digital downloads for personal use. Not affiliated with The Ohio State University or the City of Columbus.</p>
  </footer>
`;

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) e.target.classList.add('in');
    });
  },
  { threshold: 0.15 }
);

document.querySelectorAll('.kit, .how').forEach((el) => observer.observe(el));
