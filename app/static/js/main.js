// app/static/js/main.js
// CloudVault - Complete JavaScript v2

// ═══════════════════════════════════════
// DARK MODE
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
// FLASH MESSAGES — auto dismiss
// ═══════════════════════════════════════
document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
        flash.style.opacity = '0';
        flash.style.transform = 'translateX(110%)';
        flash.style.transition = 'all 0.4s ease';
        setTimeout(() => flash.remove(), 420);
    }, 5000);
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
// SORT FILES
// ═══════════════════════════════════════
function sortFiles(value) {
    const url = new URL(window.location.href);
    url.searchParams.set('sort', value);
    window.location.href = url.toString();
}

// ═══════════════════════════════════════
// VIEW TOGGLE (Grid / List)
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

// Restore saved view on load
document.addEventListener('DOMContentLoaded', () => {
    const savedView = localStorage.getItem('cv_view') || 'grid';
    if (savedView === 'list') setView('list');

    // Animate storage bar
    const fill = document.querySelector('.storage-fill');
    if (fill) {
        const pct = fill.getAttribute('data-percent') || '0';
        setTimeout(() => { fill.style.width = pct + '%'; }, 400);
    }
});

// ═══════════════════════════════════════
// FILE UPLOAD — with progress simulation
// ═══════════════════════════════════════
function handleFileSelect(input) {
    if (!input.files.length) return;

    const progress = document.getElementById('uploadProgress');
    const fill     = document.getElementById('uploadFill');
    const text     = document.getElementById('uploadText');

    if (progress) {
        progress.classList.remove('hidden');
        let pct = 0;
        const names = Array.from(input.files).map(f => f.name).join(', ');
        text.textContent = `Uploading ${input.files.length} file(s)...`;

        const interval = setInterval(() => {
            pct = Math.min(pct + Math.random() * 15, 90);
            if (fill) fill.style.width = pct + '%';
        }, 200);

        // Actually submit the form
        const form = document.getElementById('uploadForm');
        if (form) {
            // Small delay so progress bar is visible
            setTimeout(() => {
                clearInterval(interval);
                if (fill) fill.style.width = '100%';
                if (text) text.textContent = 'Processing...';
                form.submit();
            }, 800);
        }
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
        dropZone.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); });
        document.body.addEventListener(ev, e => e.preventDefault());
    });

    ['dragenter','dragover'].forEach(ev =>
        dropZone.addEventListener(ev, () => dropZone.classList.add('drag-over'))
    );
    ['dragleave','drop'].forEach(ev =>
        dropZone.addEventListener(ev, () => dropZone.classList.remove('drag-over'))
    );

    dropZone.addEventListener('drop', e => {
        const droppedFiles = e.dataTransfer.files;
        if (!droppedFiles.length) return;
        const dt = new DataTransfer();
        Array.from(droppedFiles).forEach(f => dt.items.add(f));
        fileInput.files = dt.files;
        handleFileSelect(fileInput);
    });

    dropZone.addEventListener('click', () => fileInput.click());
}

// ═══════════════════════════════════════
// SHARE TOGGLE
// ═══════════════════════════════════════
async function toggleShare(fileId, button) {
    button.disabled = true;
    button.style.opacity = '0.5';

    try {
        const res = await fetch(`/share/${fileId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!res.ok) throw new Error('Request failed');

        const data = await res.json();
        const box  = document.getElementById(`share-${fileId}`);
        const inp  = box?.querySelector('.share-input');

        if (data.shared) {
            button.classList.add('active');
            button.title = 'Unshare';
            if (inp) inp.value = data.share_url;
            if (box) box.classList.remove('hidden');
            showShareModal(data.share_url);
        } else {
            button.classList.remove('active');
            button.title = 'Share';
            if (inp) inp.value = '';
            if (box) box.classList.add('hidden');
            showToast('File is now private', 'info');
        }
    } catch (err) {
        console.error(err);
        showToast('Something went wrong', 'error');
    } finally {
        button.disabled = false;
        button.style.opacity = '1';
    }
}

// ═══════════════════════════════════════
// COPY LINKS
// ═══════════════════════════════════════
function copyShareLink(fileId) {
    const box = document.getElementById(`share-${fileId}`);
    const inp = box?.querySelector('.share-input');
    if (!inp?.value) return;
    copyText(inp.value);
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
// MODAL
// ═══════════════════════════════════════
function showShareModal(url) {
    const modal = document.getElementById('shareModal');
    const inp   = document.getElementById('modalShareLink');
    if (!modal) return;
    if (inp) inp.value = url;
    modal.classList.remove('hidden');
}
function closeModal() {
    document.getElementById('shareModal')?.classList.add('hidden');
}
document.getElementById('shareModal')?.addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});

// ═══════════════════════════════════════
// TOAST NOTIFICATIONS
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
    toast.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;';
    toast.innerHTML = `<i class="fas fa-${icon}"></i>${message}`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.4s';
        setTimeout(() => toast.remove(), 420);
    }, 3000);
}