// -*- coding: utf-8 -*-
// app/static/js/main.js — CloudVault Final

// ═══════════════════════════════════════
// THEME
// ═══════════════════════════════════════
const themeToggle = document.getElementById('themeToggle');
const themeIcon   = document.getElementById('themeIcon');
const html        = document.documentElement;
const savedTheme  = localStorage.getItem('cv_theme') || 'dark';
html.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('cv_theme', next);
        updateThemeIcon(next);
    });
}
function updateThemeIcon(theme) {
    if (!themeIcon) return;
    themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

// ═══════════════════════════════════════
// PAGE LOAD
// ═══════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    // Storage bar animation
    const fill = document.querySelector('.storage-fill');
    if (fill) {
        const pct = fill.getAttribute('data-percent') || '0';
        setTimeout(() => { fill.style.width = pct + '%'; }, 400);
    }
    // Profile storage bar
    const fillLarge = document.querySelector('.storage-fill-large');
    if (fillLarge) {
        const pct = fillLarge.getAttribute('data-percent') || '0';
        setTimeout(() => { fillLarge.style.width = pct + '%'; }, 400);
    }
    // Restore view
    const savedView = localStorage.getItem('cv_view') || 'grid';
    if (savedView === 'list') setView('list');
    // Load thumbnails
    loadThumbnails();
    // Animate cards
    document.querySelectorAll('.file-card').forEach((card, i) => {
        card.style.animationDelay = `${i * 0.05}s`;
    });
});

// ═══════════════════════════════════════
// FLASH MESSAGES
// ═══════════════════════════════════════
document.querySelectorAll('.flash').forEach((flash, i) => {
    setTimeout(() => {
        flash.style.opacity = '0';
        flash.style.transform = 'translateX(110%)';
        flash.style.transition = 'all 0.4s ease';
        setTimeout(() => flash.remove(), 420);
    }, 4000 + (i * 500));
});

// ═══════════════════════════════════════
// PASSWORD TOGGLE
// ═══════════════════════════════════════
function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    const icon  = document.getElementById(fieldId + '-eye');
    if (!field) return;
    if (field.type === 'password') {
        field.type = 'text';
        if (icon) icon.className = 'fas fa-eye-slash';
    } else {
        field.type = 'password';
        if (icon) icon.className = 'fas fa-eye';
    }
}

// ═══════════════════════════════════════
// DELETE CONFIRM
// ═══════════════════════════════════════
function confirmDelete(filename) {
    return confirm(`Delete "${filename}"?\nThis cannot be undone.`);
}

// ═══════════════════════════════════════
// DOWNLOAD — via iframe (silent)
// triggerDownload = called by download button ONLY
// ═══════════════════════════════════════
function triggerDownload(fileId) {
    // Completely isolated from preview
    // Uses hidden iframe — zero flash, zero new tab
    let frame = document.getElementById('downloadFrame');
    if (!frame) {
        frame = document.createElement('iframe');
        frame.id = 'downloadFrame';
        frame.style.cssText = 'display:none;width:0;height:0;border:none;position:absolute;';
        document.body.appendChild(frame);
    }
    // Small delay prevents any accidental double-trigger
    setTimeout(() => {
        frame.src = `/download/${fileId}?t=${Date.now()}`;
    }, 50);
}

// ═══════════════════════════════════════
// SORT
// ═══════════════════════════════════════
function changeSort(value) {
    const url = new URL(window.location.href);
    url.searchParams.set('sort', value);
    window.location.href = url.toString();
}

// ═══════════════════════════════════════
// VIEW TOGGLE
// ═══════════════════════════════════════
function setView(type) {
    const grid    = document.getElementById('filesGrid');
    const gridBtn = document.getElementById('gridViewBtn');
    const listBtn = document.getElementById('listViewBtn');
    if (!grid) return;
    if (type === 'list') {
        grid.classList.add('list-view');
        listBtn?.classList.add('active');
        gridBtn?.classList.remove('active');
        localStorage.setItem('cv_view', 'list');
    } else {
        grid.classList.remove('list-view');
        gridBtn?.classList.add('active');
        listBtn?.classList.remove('active');
        localStorage.setItem('cv_view', 'grid');
    }
}

// ═══════════════════════════════════════
// FILE UPLOAD
// ═══════════════════════════════════════
function handleFileSelect(input) {
    if (!input.files.length) return;
    const progress = document.getElementById('uploadProgress');
    const fill     = document.getElementById('uploadFill');
    const text     = document.getElementById('uploadText');
    if (progress) {
        progress.classList.remove('hidden');
        let pct = 0;
        if (text) text.textContent = `Uploading ${input.files.length} file(s)...`;
        const interval = setInterval(() => {
            pct = Math.min(pct + Math.random() * 15, 90);
            if (fill) fill.style.width = pct + '%';
        }, 200);
        setTimeout(() => {
            clearInterval(interval);
            if (fill) fill.style.width = '100%';
            if (text) text.textContent = 'Processing...';
            document.getElementById('uploadForm')?.submit();
        }, 800);
    } else {
        document.getElementById('uploadForm')?.submit();
    }
}

// ═══════════════════════════════════════
// DRAG & DROP
// ═══════════════════════════════════════
const dropZone  = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

if (dropZone && fileInput) {
    ['dragenter','dragover','dragleave','drop'].forEach(ev => {
        dropZone.addEventListener(ev, e => {
            e.preventDefault(); e.stopPropagation();
        });
        document.body.addEventListener(ev, e => e.preventDefault());
    });
    ['dragenter','dragover'].forEach(ev =>
        dropZone.addEventListener(ev, () =>
            dropZone.classList.add('drag-over'))
    );
    ['dragleave','drop'].forEach(ev =>
        dropZone.addEventListener(ev, () =>
            dropZone.classList.remove('drag-over'))
    );
    dropZone.addEventListener('drop', e => {
        const dropped = e.dataTransfer.files;
        if (!dropped.length) return;
        const dt = new DataTransfer();
        Array.from(dropped).forEach(f => dt.items.add(f));
        fileInput.files = dt.files;
        handleFileSelect(fileInput);
    });
    dropZone.addEventListener('click', () => fileInput.click());
}

// ═══════════════════════════════════════
// LOAD THUMBNAILS
// ═══════════════════════════════════════
// ═══════════════════════════════════════
// LOAD THUMBNAILS
// Uses /preview/ route directly as img src
// No JSON, no presigned URL, zero flash!
// ═══════════════════════════════════════
function loadThumbnails() {
    const imgs = document.querySelectorAll(
        '.thumb-img[data-file-id]'
    );
    imgs.forEach(img => {
        const fileId = img.getAttribute('data-file-id');
        // Set src directly — Flask serves image inline
        img.src = `/preview/${fileId}`;
        img.onload = () => {
            img.style.display = 'block';
            const fallback = img.nextElementSibling;
            if (fallback) fallback.style.display = 'none';
        };
        img.onerror = () => {
            img.style.display = 'none';
            const fallback = img.nextElementSibling;
            if (fallback) fallback.style.display = 'flex';
        };
    });
}

// ═══════════════════════════════════════
// IMAGE PREVIEW MODAL
// preview and download are 100% isolated
// openPreview NEVER calls triggerDownload
// ═══════════════════════════════════════
// ═══════════════════════════════════════
// IMAGE PREVIEW MODAL
// Uses /preview/ route as img src directly
// No presigned URL = zero download flash!
// ═══════════════════════════════════════
function openPreview(fileId, filename) {
    const modal     = document.getElementById('previewModal');
    const img       = document.getElementById('previewImg');
    const loading   = document.getElementById('previewLoading');
    const noSupport = document.getElementById('previewNoSupport');
    const fnLabel   = document.getElementById('previewFilename');
    const dlBtn     = document.getElementById('previewDownloadBtn');

    if (!modal) return;

    // Setup
    if (fnLabel)   fnLabel.textContent = filename;
    if (img)     { img.src = ''; img.classList.add('hidden'); }
    if (noSupport) noSupport.classList.add('hidden');
    if (loading)   loading.classList.remove('hidden');

    // Download button in modal
    if (dlBtn) {
        dlBtn.removeAttribute('href');
        dlBtn.onclick = (e) => {
            e.preventDefault();
            triggerDownload(fileId);
        };
    }

    // Show modal
    modal.classList.remove('hidden');

    // Set image src to our Flask proxy route
    // /preview/<id> returns image with inline headers
    // This NEVER triggers download bar!
    if (img) {
        img.onload = () => {
            if (loading) loading.classList.add('hidden');
            img.classList.remove('hidden');
        };
        img.onerror = () => {
            if (loading)   loading.classList.add('hidden');
            if (noSupport) noSupport.classList.remove('hidden');
        };
        // Direct image URL — no JSON fetch needed
        img.src = `/preview/${fileId}`;
    }
}

function closePreview() {
    const modal = document.getElementById('previewModal');
    const img   = document.getElementById('previewImg');
    if (modal) modal.classList.add('hidden');
    if (img)   img.src = '';
}

document.getElementById('previewModal')?.addEventListener('click', function(e) {
    if (e.target === this) closePreview();
});

// ═══════════════════════════════════════
// SHARE TOGGLE
// ═══════════════════════════════════════
async function toggleShare(fileId, button) {
    button.disabled = true;
    button.style.opacity = '0.5';
    try {
        const res  = await fetch(`/share/${fileId}`, { method: 'POST' });
        const data = await res.json();
        const box  = document.getElementById(`share-${fileId}`);
        const inp  = box?.querySelector('.share-input');
        if (data.shared) {
            button.classList.add('shared-active');
            button.title = 'Unshare';
            if (inp) inp.value = data.share_url;
            if (box) box.classList.remove('hidden');
            showShareModal(data.share_url);
        } else {
            button.classList.remove('shared-active');
            button.title = 'Share';
            if (inp) inp.value = '';
            if (box) box.classList.add('hidden');
            showToast('File is now private', 'info');
        }
    } catch {
        showToast('Something went wrong', 'error');
    } finally {
        button.disabled = false;
        button.style.opacity = '1';
    }
}

// ═══════════════════════════════════════
// COPY
// ═══════════════════════════════════════
function copyShareLink(fileId) {
    const inp = document.querySelector(`#share-${fileId} .share-input`);
    if (inp?.value) copyText(inp.value);
}
function copyModalLink() {
    const inp = document.getElementById('modalShareLink');
    if (inp) copyText(inp.value);
}
function copyText(text) {
    navigator.clipboard.writeText(text)
        .then(() => showToast('✅ Link copied!'))
        .catch(() => {
            const ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            showToast('✅ Link copied!');
        });
}

// ═══════════════════════════════════════
// SHARE MODAL
// ═══════════════════════════════════════
function showShareModal(url) {
    const modal = document.getElementById('shareModal');
    const inp   = document.getElementById('modalShareLink');
    if (!modal) return;
    if (inp) inp.value = url;
    modal.classList.remove('hidden');
}
function closeShareModal() {
    document.getElementById('shareModal')?.classList.add('hidden');
}
function closeModal() { closeShareModal(); }
document.getElementById('shareModal')?.addEventListener('click', function(e) {
    if (e.target === this) closeShareModal();
});

// ═══════════════════════════════════════
// TOAST
// ═══════════════════════════════════════
function showToast(message, type = 'success') {
    const map = {
        success: { cls: 'flash-success', icon: 'check-circle' },
        error:   { cls: 'flash-danger',  icon: 'exclamation-circle' },
        info:    { cls: 'flash-info',    icon: 'info-circle' },
    };
    const { cls, icon } = map[type] || map.success;
    const toast = document.createElement('div');
    toast.className = `flash ${cls}`;
    toast.style.cssText = `
        position:fixed; bottom:1.5rem; right:1.5rem;
        z-index:9999; animation:slideIn 0.3s ease; max-width:320px;
    `;
    toast.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.4s';
        setTimeout(() => toast.remove(), 420);
    }, 3000);
}

// ═══════════════════════════════════════
// MOBILE SIDEBAR
// ═══════════════════════════════════════
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (!sidebar) return;
    const isOpen = sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('open', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
}

// ═══════════════════════════════════════
// NAVBAR HAMBURGER
// ═══════════════════════════════════════
const navHamburger = document.getElementById('navHamburger');
const navLinksEl   = document.getElementById('navLinks');
if (navHamburger && navLinksEl) {
    navHamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        navLinksEl.classList.toggle('open');
        const icon = navHamburger.querySelector('i');
        if (icon) icon.className = navLinksEl.classList.contains('open')
            ? 'fas fa-times' : 'fas fa-bars';
    });
    navLinksEl.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navLinksEl.classList.remove('open');
            const icon = navHamburger.querySelector('i');
            if (icon) icon.className = 'fas fa-bars';
        });
    });
    document.addEventListener('click', (e) => {
        if (!navLinksEl.contains(e.target) &&
            !navHamburger.contains(e.target)) {
            navLinksEl.classList.remove('open');
            const icon = navHamburger.querySelector('i');
            if (icon) icon.className = 'fas fa-bars';
        }
    });
}

// ═══════════════════════════════════════
// KEYBOARD SHORTCUTS
// ═══════════════════════════════════════
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closePreview();
        closeShareModal();
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        if (sidebar?.classList.contains('open')) {
            sidebar.classList.remove('open');
            overlay?.classList.remove('open');
            document.body.style.overflow = '';
        }
    }
    if (e.key === '/' &&
        document.activeElement.tagName !== 'INPUT' &&
        document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        document.getElementById('searchInput')?.focus();
    }
});