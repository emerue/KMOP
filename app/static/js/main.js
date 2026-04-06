/* ============================================================
   KingMac of Property — Main JavaScript
   ============================================================ */

'use strict';

// ── CONSTANTS ──────────────────────────────────────────────────────────────
const SYMBOLS = { NGN: '₦', USD: '$', GBP: '£' };
const SHORTLIST_KEY  = 'km_shortlist';
const CURRENCY_KEY   = 'km_currency';
const RATES_KEY      = 'km_rates';
const RATES_TTL_KEY  = 'km_rates_ts';
const RATES_TTL_MS   = 24 * 60 * 60 * 1000; // 24 hours

// Live rates object — starts with sensible defaults, updated from /api/rates
let RATES = { NGN: 1, USD: 0.00063, GBP: 0.00050 };

/**
 * Load rates: use localStorage cache if < 24h old, otherwise fetch from /api/rates.
 * Fallback to defaults if network is unavailable.
 */
async function loadRates() {
  const cachedTs    = parseInt(localStorage.getItem(RATES_TTL_KEY) || '0', 10);
  const cachedRates = localStorage.getItem(RATES_KEY);
  const isStale     = Date.now() - cachedTs > RATES_TTL_MS;

  if (cachedRates && !isStale) {
    try {
      const parsed = JSON.parse(cachedRates);
      RATES = { NGN: 1, ...parsed };
      return;
    } catch { /* fall through to fetch */ }
  }

  try {
    const res  = await fetch('/api/rates');
    const data = await res.json();
    if (data.rates) {
      RATES = { NGN: 1, ...data.rates };
      localStorage.setItem(RATES_KEY, JSON.stringify(data.rates));
      localStorage.setItem(RATES_TTL_KEY, String(Date.now()));
    }
  } catch {
    // Network unavailable — keep defaults or cached values
    if (cachedRates) {
      try { RATES = { NGN: 1, ...JSON.parse(cachedRates) }; } catch {}
    }
  }
}

// Kick off rate loading immediately, then apply prices once done
loadRates().then(() => {
  const stored = localStorage.getItem(CURRENCY_KEY) || 'NGN';
  if (stored !== 'NGN') updateAllPrices(stored);
});

// ── NAVBAR SCROLL ──────────────────────────────────────────────────────────
(function initNavbar() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;
  function onScroll() {
    navbar.classList.toggle('scrolled', window.scrollY > 40);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

// ── GSAP HERO ANIMATIONS ───────────────────────────────────────────────────
(function initHeroAnimation() {
  if (typeof gsap === 'undefined') return;
  const heroEls = document.querySelectorAll('.animate-hero');
  if (!heroEls.length) return;
  gsap.to(heroEls, {
    opacity: 1,
    y: 0,
    duration: 0.9,
    stagger: 0.18,
    ease: 'power3.out',
    delay: 0.2,
  });
})();

// ── SCROLL REVEAL (Intersection Observer) ─────────────────────────────────
(function initScrollReveal() {
  const els = document.querySelectorAll('.animate-on-scroll');
  if (!els.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const delay = parseFloat(el.dataset.delay || '0');
        el.style.transitionDelay = delay + 's';
        el.classList.add('visible');
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  els.forEach(el => observer.observe(el));
})();

// ── CURRENCY TOGGLE (Alpine.js component + custom events) ─────────────────
function currencyToggle() {
  return {
    currency: localStorage.getItem(CURRENCY_KEY) || 'NGN',
    setCurrency(c) {
      this.currency = c;
      localStorage.setItem(CURRENCY_KEY, c);
      document.dispatchEvent(new CustomEvent('currencyChanged', {
        detail: { currency: c, rate: RATES[c], symbol: SYMBOLS[c] }
      }));
      updateAllPrices(c);
    },
    init() {
      document.addEventListener('currencyChanged', (e) => {
        this.currency = e.detail.currency;
      });
    }
  };
}

function updateAllPrices(currency) {
  const rate   = RATES[currency]   || 1;
  const symbol = SYMBOLS[currency] || '₦';

  document.querySelectorAll('.property-price[data-price-ngn]').forEach(el => {
    const ngn = parseFloat(el.dataset.priceNgn);
    if (isNaN(ngn)) return;
    const converted = Math.round(ngn * rate);
    el.textContent = symbol + ' ' + converted.toLocaleString();
  });
}

// (currency applied after loadRates() resolves — see above)

document.addEventListener('currencyChanged', (e) => {
  updateAllPrices(e.detail.currency);
});

// ── SHORTLIST (localStorage) ───────────────────────────────────────────────
function getShortlist() {
  try { return JSON.parse(localStorage.getItem(SHORTLIST_KEY) || '[]'); }
  catch { return []; }
}
function saveShortlist(list) {
  localStorage.setItem(SHORTLIST_KEY, JSON.stringify(list));
  updateShortlistBadge(list.length);
  document.dispatchEvent(new CustomEvent('shortlistChanged', { detail: list }));
}

function toggleShortlist(e, propId) {
  e.preventDefault();
  e.stopPropagation();

  let list = getShortlist();
  const idx = list.indexOf(propId);
  const wasIn = idx !== -1;

  if (wasIn) list.splice(idx, 1);
  else list.push(propId);

  saveShortlist(list);

  // Update all hearts for this property
  document.querySelectorAll(`[data-property-id="${propId}"]`).forEach(btn => {
    const icon = btn.querySelector('i');
    if (!icon) return;
    if (!wasIn) {
      icon.className = 'fa-solid fa-heart';
      btn.classList.add('saved');
    } else {
      icon.className = 'fa-regular fa-heart';
      btn.classList.remove('saved');
    }
    // Pulse animation
    btn.classList.remove('heart-pulse');
    void btn.offsetWidth;
    btn.classList.add('heart-pulse');
  });

  // Update detail page button text
  const detailBtn = document.getElementById('detailShortlistBtn');
  if (detailBtn && parseInt(detailBtn.dataset.propertyId) === propId) {
    const span = detailBtn.querySelector('span');
    const icon = detailBtn.querySelector('i');
    if (!wasIn) {
      detailBtn.classList.add('saved');
      if (icon) icon.className = 'fa-solid fa-heart';
      if (span) span.textContent = 'Saved';
    } else {
      detailBtn.classList.remove('saved');
      if (icon) icon.className = 'fa-regular fa-heart';
      if (span) span.textContent = 'Save to Shortlist';
    }
  }
}

function updateShortlistBadge(count) {
  const badge = document.getElementById('shortlistBadge');
  if (!badge) return;
  if (count > 0) {
    badge.textContent = count;
    badge.style.display = 'flex';
  } else {
    badge.style.display = 'none';
  }
}

// Init shortlist UI on page load
(function initShortlistUI() {
  const list = getShortlist();
  updateShortlistBadge(list.length);

  // Apply filled hearts for shortlisted properties
  list.forEach(propId => {
    document.querySelectorAll(`[data-property-id="${propId}"]`).forEach(btn => {
      const icon = btn.querySelector('i');
      if (icon) icon.className = 'fa-solid fa-heart';
      btn.classList.add('saved');
    });
  });

  // Detail page shortlist button
  const detailBtn = document.getElementById('detailShortlistBtn');
  if (detailBtn) {
    const id = parseInt(detailBtn.dataset.propertyId);
    if (list.includes(id)) {
      detailBtn.classList.add('saved');
      const icon = detailBtn.querySelector('i');
      const span = detailBtn.querySelector('span');
      if (icon) icon.className = 'fa-solid fa-heart';
      if (span) span.textContent = 'Saved';
    }
  }
})();

// ── NEWSLETTER FORM ────────────────────────────────────────────────────────
(function initNewsletter() {
  const form = document.getElementById('newsletterForm');
  if (!form) return;
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const input = form.querySelector('input[type="email"]');
    const btn   = form.querySelector('button');
    if (!input || !btn) return;

    const originalText = btn.textContent;
    btn.textContent = '…';
    btn.disabled = true;

    const data = new FormData();
    data.append('email', input.value);

    try {
      const res  = await fetch('/newsletter/subscribe', { method: 'POST', body: data });
      const json = await res.json();
      if (json.success) {
        btn.textContent = 'Subscribed ✓';
        input.value = '';
      } else {
        btn.textContent = originalText;
        btn.disabled = false;
        alert(json.message || 'Please try again.');
      }
    } catch {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  });
})();

// ── FILTER SIDEBAR TOGGLE (mobile) ────────────────────────────────────────
(function initFilterSidebar() {
  const toggleBtn = document.querySelector('.filter-sidebar__toggle');
  const sidebar   = document.querySelector('.filter-sidebar');
  if (!toggleBtn || !sidebar) return;
  toggleBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
})();

// ─── WhatsApp Share Card ───────────────────────────────────────────────────

const SHARE_MODAL    = document.getElementById('share-modal');
const SHARE_TEXTAREA = document.getElementById('share-message');

function openShareModal(btn) {
  if (!SHARE_MODAL || !SHARE_TEXTAREA) return;

  const data = {
    title:    btn.dataset.propertyTitle  || '',
    ref:      btn.dataset.propertyRef    || '',
    price:    btn.dataset.propertyPrice  || '',
    period:   btn.dataset.propertyPeriod || '',
    beds:     btn.dataset.propertyBeds   || '',
    baths:    btn.dataset.propertyBaths  || '',
    sqm:      btn.dataset.propertySqm    || '',
    city:     btn.dataset.propertyCity   || '',
    state:    btn.dataset.propertyState  || '',
    slug:     btn.dataset.propertySlug   || '',
    amenities: btn.dataset.amenities     || '',
    siteUrl:  document.body.dataset.siteUrl   || '',
    phone:    document.body.dataset.brandPhone || '',
  };

  let priceLine = data.price;
  if (data.period) priceLine += ' / ' + data.period;

  let statsLine = '';
  if (data.beds  && data.beds  !== '0') statsLine += `🛏 ${data.beds} Beds  `;
  if (data.baths && data.baths !== '0') statsLine += `🚿 ${data.baths} Baths  `;
  if (data.sqm   && data.sqm   !== '0') statsLine += `📐 ${data.sqm} sqm`;
  statsLine = statsLine.trim();

  let amenityLine = '';
  if (data.amenities) amenityLine = `\n✅ ${data.amenities}\n`;

  const message =
`🏡 *${data.title}*

💰 ${priceLine}
${statsLine}
📍 ${data.city}, ${data.state}
🔖 Ref: ${data.ref}
${amenityLine}
View full details & photos 👇
${data.siteUrl}/properties/${data.slug}

📞 Call/WhatsApp: ${data.phone}`;

  SHARE_TEXTAREA.value = message;
  SHARE_MODAL.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeShareModal() {
  if (!SHARE_MODAL) return;
  SHARE_MODAL.classList.remove('active');
  document.body.style.overflow = '';
}

// Wire up once DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (!SHARE_MODAL) return;

  // Copy button
  const copyBtn = document.getElementById('share-copy-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', function() {
      navigator.clipboard.writeText(SHARE_TEXTAREA.value).then(() => {
        this.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
        this.classList.add('copied');
        setTimeout(() => {
          this.innerHTML = '<i class="fa-solid fa-copy"></i> Copy Message';
          this.classList.remove('copied');
        }, 2500);
      });
    });
  }

  // WhatsApp button
  const waBtn = document.getElementById('share-whatsapp-btn');
  if (waBtn) {
    waBtn.addEventListener('click', function() {
      const msg = encodeURIComponent(SHARE_TEXTAREA.value);
      window.open('https://wa.me/?text=' + msg, '_blank');
    });
  }

  // Close on overlay click
  SHARE_MODAL.addEventListener('click', function(e) {
    if (e.target === SHARE_MODAL) closeShareModal();
  });

  // Wire all share trigger buttons
  document.querySelectorAll('[data-action="open-share"]').forEach(btn => {
    btn.addEventListener('click', () => openShareModal(btn));
  });
});
