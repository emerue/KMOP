/* ============================================================
   KingMac of Property — Admin JavaScript
   ============================================================ */

'use strict';

// ── SLUG GENERATOR ─────────────────────────────────────────────────────────
(function initSlugGenerator() {
  const titleInput = document.getElementById('propTitle');
  const slugInput  = document.getElementById('propSlug');
  if (!titleInput || !slugInput) return;

  let manuallyEdited = slugInput.value.length > 0 && document.title.includes('Edit');

  slugInput.addEventListener('input', () => { manuallyEdited = true; });

  titleInput.addEventListener('input', () => {
    if (manuallyEdited) return;
    slugInput.value = slugify(titleInput.value);
  });

  function slugify(text) {
    return text.toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  }
})();

// ── AGENT PHOTO PREVIEW ────────────────────────────────────────────────────
(function initAgentPhotoPreview() {
  const input   = document.getElementById('agentPhotoInput');
  const preview = document.getElementById('agentPhotoPreview');
  if (!input || !preview) return;

  input.addEventListener('change', function () {
    if (this.files && this.files[0]) {
      const reader = new FileReader();
      reader.onload = e => {
        preview.src = e.target.result;
        preview.style.display = 'block';
      };
      reader.readAsDataURL(this.files[0]);
    }
  });
})();

// ── PROPERTY TABLE SEARCH ──────────────────────────────────────────────────
function filterPropertiesTable(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('#propertiesTable tbody tr[data-title]').forEach(row => {
    const title = (row.dataset.title || '').toLowerCase();
    const city  = (row.dataset.city  || '').toLowerCase();
    row.style.display = (title.includes(q) || city.includes(q)) ? '' : 'none';
  });
}

// ── AJAX PUBLISH / FEATURED TOGGLE ────────────────────────────────────────
function toggleProperty(id, type, btn) {
  const endpoint = type === 'publish'
    ? `/admin/properties/${id}/toggle-publish`
    : `/admin/properties/${id}/toggle-featured`;

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content
    || getCsrfFromCookie();

  fetch(endpoint, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
      'Content-Type': 'application/json'
    }
  })
  .then(r => r.json())
  .then(data => {
    const isActive = data.published !== undefined ? data.published : data.featured;
    btn.classList.toggle('active', isActive);
    if (type === 'publish') {
      btn.querySelector('i').className = isActive ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash';
      btn.title = isActive ? 'Published' : 'Unpublished';
    } else {
      btn.title = isActive ? 'Featured' : 'Not Featured';
    }
  })
  .catch(err => console.error('Toggle failed:', err));
}

// ── DELETE CONFIRM MODAL ───────────────────────────────────────────────────
function confirmDelete(url, title) {
  const modal    = document.getElementById('deleteModal');
  const textEl   = document.getElementById('deleteModalText');
  const formEl   = document.getElementById('deleteForm');
  if (!modal || !formEl) return;

  textEl.textContent = `Delete "${title}"? This cannot be undone.`;
  formEl.action = url;
  modal.style.display = 'flex';
}

// Close modal on backdrop click
document.addEventListener('DOMContentLoaded', function () {
  const deleteModal = document.getElementById('deleteModal');
  if (deleteModal) {
    deleteModal.addEventListener('click', function (e) {
      if (e.target === deleteModal) deleteModal.style.display = 'none';
    });
  }

  const inquiryModal = document.getElementById('inquiryModal');
  if (inquiryModal) {
    inquiryModal.addEventListener('click', function (e) {
      if (e.target === inquiryModal) inquiryModal.style.display = 'none';
    });
  }

  // Keyboard ESC to close modals
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.admin-modal').forEach(m => m.style.display = 'none');
    }
  });

  // Mobile sidebar toggle
  const sidebarToggle = document.querySelector('.admin-sidebar-toggle');
  const sidebar       = document.getElementById('adminSidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', function (e) {
      if (sidebar.classList.contains('open')
          && !sidebar.contains(e.target)
          && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }
});

// ── FLYER GENERATOR MODAL ─────────────────────────────────────────────────

let _flyerPropertyId  = null;
let _flyerImageCount  = 0;

function openFlyerModal(btn) {
  const id        = btn.dataset.propertyId;
  const title     = btn.dataset.propertyTitle;
  const type      = btn.dataset.propertyType || '';
  const imgCount  = parseInt(btn.dataset.imageCount || '0', 10);

  _flyerPropertyId = id;
  _flyerImageCount = imgCount;

  const modal     = document.getElementById('flyerModal');
  const titleEl   = document.getElementById('flyerModalTitle');
  const strip     = document.getElementById('flyerImageStrip');
  const warning   = document.getElementById('flyerNoImagesWarning');
  const dlBtn     = document.getElementById('flyerDownloadBtn');

  if (!modal) return;

  if (titleEl) titleEl.textContent = title;

  // Pre-select radio from property type
  const typeMap = { 'For Sale': 'sale', 'For Rent': 'rent', 'Short Let': 'shortlet' };
  const radioVal = typeMap[type] || 'sale';
  modal.querySelectorAll('input[name="flyerType"]').forEach(r => {
    r.checked = (r.value === radioVal);
  });

  // Image strip
  if (strip) {
    strip.innerHTML = '';
    const labels = ['Slide 1', 'Slide 2', 'Slide 3', 'Slide 4'];
    for (let i = 0; i < 4; i++) {
      const div = document.createElement('div');
      div.className = 'flyer-slide-thumb';
      div.innerHTML = i < imgCount
        ? `<div class="flyer-slide-thumb__img"><i class="fa-solid fa-image"></i></div><span>${labels[i]}</span>`
        : `<div class="flyer-slide-thumb__img flyer-slide-thumb__img--empty"><i class="fa-solid fa-image" style="opacity:0.3"></i></div><span style="opacity:0.4">${labels[i]}</span>`;
      strip.appendChild(div);
    }
  }

  if (warning) warning.style.display = imgCount === 0 ? 'block' : 'none';
  if (dlBtn)   dlBtn.disabled = imgCount === 0;

  modal.style.display = 'flex';
}

function closeFlyerModal() {
  const modal = document.getElementById('flyerModal');
  if (modal) modal.style.display = 'none';
}

function downloadFlyer() {
  if (!_flyerPropertyId) return;
  const selected = document.querySelector('input[name="flyerType"]:checked');
  const type = selected ? selected.value : 'sale';

  const btn = document.getElementById('flyerDownloadBtn');
  const original = btn.innerHTML;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating…';
  btn.disabled = true;

  const url = `/admin/properties/${_flyerPropertyId}/flyer?type=${type}`;
  const a = document.createElement('a');
  a.href = url;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  setTimeout(() => {
    btn.innerHTML = original;
    btn.disabled = _flyerImageCount === 0;
  }, 3000);
}

// Wire all flyer buttons on page load
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('[data-action="open-flyer"]').forEach(btn => {
    btn.addEventListener('click', () => openFlyerModal(btn));
  });

  // Also wire share buttons inside admin (they use main.js openShareModal)
  document.querySelectorAll('[data-action="open-share"]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (typeof openShareModal === 'function') openShareModal(btn);
    });
  });
});

// ── CSRF HELPER ────────────────────────────────────────────────────────────
function getCsrfFromCookie() {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : '';
}

// ── INQUIRY MODAL ──────────────────────────────────────────────────────────
// (data is inlined per-page in inquiries.html — function just opens the modal)
function openInquiryModal(id) {
  if (typeof INQUIRIES === 'undefined' || !INQUIRIES[id]) return;
  const inq = INQUIRIES[id];
  document.getElementById('modalName').textContent    = inq.name;
  document.getElementById('modalEmail').textContent   = inq.email;
  document.getElementById('modalPhone').textContent   = inq.phone;
  document.getElementById('modalType').textContent    = inq.type;
  document.getElementById('modalDate').textContent    = inq.date;
  document.getElementById('modalMessage').textContent = inq.message;
  document.getElementById('modalReplyBtn').href = `mailto:${inq.email}?subject=Re: Your KingMac Enquiry`;
  document.getElementById('inquiryModal').style.display = 'flex';
}
