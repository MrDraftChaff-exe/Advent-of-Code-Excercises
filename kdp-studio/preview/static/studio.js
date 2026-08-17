(() => {
  const state = {
    slug: null,
    product: null,
    pageIndex: 0,
  };

  const $ = (id) => document.getElementById(id);

  function activateTab(name) {
    document.querySelectorAll(".tab").forEach((t) => {
      t.classList.toggle("active", t.dataset.tab === name);
    });
    document.querySelectorAll(".panel").forEach((p) => {
      p.classList.toggle("active", p.id === `panel-${name}`);
    });
  }

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => activateTab(tab.dataset.tab));
  });

  async function loadProductList() {
    const res = await fetch("/api/products");
    const data = await res.json();
    const select = $("productSelect");
    select.innerHTML = "";
    for (const p of data.products) {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.title} (${p.status})`;
      select.appendChild(opt);
    }
    if (!state.slug && data.products[0]) {
      state.slug = data.products[0].id;
    }
    if (state.slug) select.value = state.slug;
  }

  function renderOverview(p) {
    const m = p.meta;
    $("ovTitle").textContent = m.title || "—";
    $("ovSubtitle").textContent = m.subtitle || "";
    const rows = [
      ["Type", m.type],
      ["Trim", m.trim],
      ["Designs", m.designs],
      ["Interior pages", m.page_count_interior ?? "—"],
      ["List price", m.list_price_usd != null ? `$${m.list_price_usd}` : "—"],
      ["Status", m.status],
      ["AI assisted", m.ai_assisted ? "yes" : "no"],
    ];
    $("ovMeta").innerHTML = rows
      .map(([k, v]) => `<dt>${k}</dt><dd>${v ?? "—"}</dd>`)
      .join("");
    const errs = p.validation || [];
    const el = $("ovValidation");
    if (errs.length) {
      el.className = "status bad";
      el.textContent = `Validation: ${errs.join("; ")}`;
    } else {
      el.className = "status ok";
      el.textContent = "Validation: OK";
    }
    const cover = $("ovCover");
    const empty = $("ovCoverEmpty");
    if (p.assets.cover_png) {
      cover.src = `/api/products/${state.slug}/cover.png?t=${Date.now()}`;
      cover.hidden = false;
      empty.hidden = true;
    } else {
      cover.hidden = true;
      empty.hidden = false;
    }
  }

  function showPage() {
    const pages = state.product?.pages || [];
    if (!pages.length) {
      $("pageLabel").textContent = "No pages";
      $("pageImage").removeAttribute("src");
      return;
    }
    state.pageIndex = Math.max(0, Math.min(state.pageIndex, pages.length - 1));
    const name = pages[state.pageIndex];
    $("pageLabel").textContent = `Design ${state.pageIndex + 1} / ${pages.length} · ${name}`;
    $("pageImage").src = `/api/products/${state.slug}/pages/${name}?t=${Date.now()}`;
  }

  function renderCover(p) {
    $("coverDims").textContent = p.cover_dimensions
      ? JSON.stringify(p.cover_dimensions, null, 2)
      : "No cover dimensions yet.";
    const img = $("coverFull");
    if (p.assets.cover_png) {
      img.src = `/api/products/${state.slug}/cover.png?t=${Date.now()}`;
      img.hidden = false;
    } else {
      img.hidden = true;
    }
  }

  function renderListing(p) {
    $("listingMd").textContent = p.listing_md || "(no listing draft)";
    $("briefMd").textContent = p.brief_md || "(no brief)";
  }

  function renderPricing(p) {
    const pricing = p.pricing;
    const box = $("priceSummary");
    const tbody = $("compsTable").querySelector("tbody");
    tbody.innerHTML = "";
    if (!pricing) {
      box.innerHTML = "<p>No pricing research yet. Run Research comps.</p>";
      $("priceQuery").value = (p.meta.keywords || []).slice(0, 3).join(" ");
      return;
    }
    $("priceQuery").value = pricing.query || "";
    const r = pricing.recommendation || {};
    box.innerHTML = `
      <p><strong>Recommended list price: $${r.list_price_usd}</strong>
      · basis ${r.basis || "—"} · source ${pricing.source || "—"}</p>
      <p class="muted">Comps ${r.comp_count ?? 0}
        (min $${r.comp_min ?? "—"} / median $${r.comp_median ?? "—"} / max $${r.comp_max ?? "—"})
        · print est. $${r.print_cost_estimate_usd}
        · ~50% royalty est. $${r.royalty_50_estimate_usd}</p>
      ${pricing.fetch?.error ? `<p class="muted">Live fetch note: ${pricing.fetch.error}</p>` : ""}
    `;
    for (const c of pricing.comps || []) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${c.title || c.asin}</td><td>$${c.price_usd}</td><td>${c.source}</td>`;
      tbody.appendChild(tr);
    }
  }

  function renderPublish(p) {
    $("publishFields").textContent = p.publish_fields
      ? JSON.stringify(p.publish_fields, null, 2)
      : "Build a publish package to see KDP fields checklist.";
    const pdf = $("pdfLink");
    if (p.assets.interior_pdf) {
      pdf.href = `/api/products/${state.slug}/interior.pdf`;
      pdf.style.display = "";
    } else {
      pdf.removeAttribute("href");
      pdf.style.display = "none";
    }
  }

  async function loadProduct(slug) {
    state.slug = slug;
    const res = await fetch(`/api/products/${slug}`);
    if (!res.ok) throw new Error("Failed to load product");
    state.product = await res.json();
    state.pageIndex = 0;
    renderOverview(state.product);
    showPage();
    renderCover(state.product);
    renderListing(state.product);
    renderPricing(state.product);
    renderPublish(state.product);
  }

  $("productSelect").addEventListener("change", (e) => loadProduct(e.target.value));
  $("refreshBtn").addEventListener("click", async () => {
    await loadProductList();
    if (state.slug) await loadProduct(state.slug);
  });
  $("prevPage").addEventListener("click", () => {
    state.pageIndex -= 1;
    showPage();
  });
  $("nextPage").addEventListener("click", () => {
    state.pageIndex += 1;
    showPage();
  });

  $("researchBtn").addEventListener("click", async () => {
    const strategy = $("priceStrategy").value;
    const query = $("priceQuery").value.trim();
    const params = new URLSearchParams({ strategy, apply: "false" });
    if (query) params.set("query", query);
    const res = await fetch(`/api/products/${state.slug}/research-price?${params}`, { method: "POST" });
    const data = await res.json();
    state.product.pricing = data;
    renderPricing(state.product);
  });

  $("applyPriceBtn").addEventListener("click", async () => {
    const strategy = $("priceStrategy").value;
    const query = $("priceQuery").value.trim();
    const params = new URLSearchParams({ strategy, apply: "true" });
    if (query) params.set("query", query);
    const res = await fetch(`/api/products/${state.slug}/research-price?${params}`, { method: "POST" });
    const data = await res.json();
    await loadProduct(state.slug);
    state.product.pricing = data;
    renderPricing(state.product);
  });

  $("packageBtn").addEventListener("click", async () => {
    const res = await fetch(`/api/products/${state.slug}/publish-package`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json();
      $("publishFields").textContent = JSON.stringify(err, null, 2);
      return;
    }
    await loadProduct(state.slug);
  });

  (async () => {
    await loadProductList();
    if (state.slug) await loadProduct(state.slug);
  })();
})();
