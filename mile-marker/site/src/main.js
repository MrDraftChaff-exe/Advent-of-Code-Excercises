import './style.css';
import { brand, products } from './catalog.js';

const app = document.querySelector('#app');

app.innerHTML = `
  <div class="atmosphere" aria-hidden="true"></div>

  <header class="top">
    <a class="logo" href="#">${brand.name}</a>
    <nav>
      <a href="#kits">Kits</a>
      <a class="nav-cta" href="#kits">Get a kit</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <p class="brand-mark">${brand.name}</p>
      <h1>${brand.tagline}</h1>
      <p class="lede">
        Printable plans for Columbus weekends, move-ins, and stadium days —
        built once, used whenever you need them.
      </p>
      <div class="cta-row">
        <a class="btn primary" href="#kits">Browse kits</a>
        <a class="btn ghost" href="#how">How it works</a>
      </div>
    </section>

    <section id="how" class="how">
      <h2>One job: remove the scramble.</h2>
      <p>
        Each kit is a short, printable field guide. Download, print or save offline,
        check boxes as you go.
      </p>
    </section>

    <section id="kits" class="kits">
      <h2>Kits</h2>
      <div class="kit-list">
        ${products
          .map(
            (p, i) => `
          <article class="kit" style="--i:${i}">
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
    <p><strong>${brand.name}</strong> · ${brand.city}</p>
    <p class="fine">Digital downloads. Personal use. Not affiliated with the City of Columbus or any university.</p>
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
