// -*- coding: utf-8 -*-
// app/static/js/main.js
// CloudVault — Complete JavaScript

// ═══════════════════════════════════════
// THEME / DARK MODE
// ═══════════════════════════════════════
const themeToggle = document.getElementById('themeToggle');
const themeIcon   = document.getElementById('themeIcon');
const html        = document.documentElement;
const savedTheme  = localStorage.getItem('cv_theme') || 'dark';

html.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const next = html.getAttribute('data-theme') === 'dark'
                     ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('cv_theme', next);
        updateThemeIcon(next);
    });
}

function updateThemeIcon(theme) {
    if (!themeIcon) return;
    themeIcon.className = theme === 'dark'
                          ? 'fas fa-sun'
                          : 'fas fa-moon';
}

// ═══════════════════════════════════════
// PAGE LOAD
// ═══════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {

    // Animate storage bar
    const fill = document.querySelector('.storage-fill');
    if (fill) {
        const pct = fill.getAttribute('data-percent') || '0';
        setTimeout(() => { fill.style.width = pct + '%'; }, 400);
    }

    // Animate profile storage bar
    const fillLarge = document.querySelector('.storage-fill-large');
    if (fillLarge) {
        const pct = fillLarge.getAttribute('data-percent') || '0';
        setTimeout(() => { fillLarge.style.width = pct + '%'; }, 400);
    }

    // Restore saved view mode
    const savedView = localStorage.getItem('cv_view') || 'grid';
    if (savedView === 'list') setView('list');

    // Load image thumbnails
    loadThumbnails();

    // Animate file cards
    document.querySelectorAll('.file-card').forEach((card, i) => {
        card.style.animationDelay = `${i * 0.05}s`;
    });
});

// ═══════════════════════════════════════
// FLASH MESSAGES — auto dismiss
// ═══════════════════════════════════════
document.querySelectorAll('.flash').forEach((flash, i) => {
    setTimeout(() => {
        flash.style.opacity      = '0';
        flash.style.transform    = 'translateX(110%)';
        flash.style.transition   = 'all 0.4s ease';
        setTimeout(() => flash.remove(), 420);
    }, 4000 + (i * 500));
});

// ═══════════════════════════════════════
// PASSWORD TOGGLE — show/hide password
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
// DELETE CONFIRMATION
// ═══════════════════════════════════════
function confirmDelete(filename) {
    return confirm(`Delete "${filename}"?\nThis cannot be undone.`);
}

// ═══════════════════════════════════════
// SORT FILES
// ═══════════════════════════════════════
function changeSort(value) {
    const url = new URL(window.location.href);
    url.searchParams.set('sort', value);
    window.location.href = url.toString();
}

// ═══════════════════════════════════════
// VIEW TOGGLE — Grid / List
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
// FILE UPLOAD — with progress bar
// ═══════════════════════════════════════
function handleFileSelect(input) {
    if (!input.files.length) return;

    const progress = document.getElementById('uploadProgress');
    const fill     = document.getElementById('uploadFill');
    const text     = document.getElementById('uploadText');

    if (progress) {
        progress.classList.remove('hidden');
        let pct = 0;

        if (text) {
            text.textContent =
                `Uploading ${input.files.length} file(s)...`;
        }

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
// DRAG & DROP UPLOAD
// ═══════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    const dropZone  = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    if (!dropZone || !fileInput) return;

    // Prevent default browser behavior
    ['dragenter','dragover','dragleave','drop'].forEach(ev => {
        dropZone.addEventListener(ev, e => {
            e.preventDefault();
            e.stopPropagation();
        });
        document.body.addEventListener(ev, e => {
            e.preventDefault();
        });
    });

    // Highlight drop zone
    ['dragenter','dragover'].forEach(ev => {
        dropZone.addEventListener(ev, () => {
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave','drop'].forEach(ev => {
        dropZone.addEventListener(ev, () => {
            dropZone.classList.remove('drag-over');
        });
    });

    // Handle file drop
    dropZone.addEventListener('drop', e => {
        const droppedFiles = e.dataTransfer.files;
        if (!droppedFiles.length) return;

        // Transfer dropped files to file input
        const dt = new DataTransfer();
        Array.from(droppedFiles).forEach(f => dt.items.add(f));
        fileInput.files = dt.files;

        // Show progress and submit
        handleFileSelect(fileInput);
    });

    // Click drop zone to open file picker
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });
});

// ═══════════════════════════════════════
// DOWNLOAD — via hidden iframe (silent)
// ═══════════════════════════════════════
let currentPreviewId = null;

function triggerDownload(fileId) {
    if (!fileId) return;

    let frame = document.getElementById('downloadFrame');
    if (!frame) {
        frame = document.createElement('iframe');
        frame.id = 'downloadFrame';
        frame.style.cssText =
            'display:none;width:0;height:0;border:none;position:absolute;';
        document.body.appendChild(frame);
    }

    setTimeout(() => {
        frame.src = `/download/${fileId}?t=${Date.now()}`;
    }, 50);
}

// ═══════════════════════════════════════
// LOAD IMAGE THUMBNAILS
// ═══════════════════════════════════════
async function loadThumbnails() {
    const imgs = document.querySelectorAll('.thumb-img[data-file-id]');

    for (const img of imgs) {
        const fileId = img.getAttribute('data-file-id');
        try {
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
        } catch (e) {
            img.style.display = 'none';
            const fallback = img.nextElementSibling;
            if (fallback) fallback.style.display = 'flex';
        }
    }
}

// ═══════════════════════════════════════
// FILE PREVIEW MODAL
// ═══════════════════════════════════════
const imageTypes = ['jpg','jpeg','png','gif','webp','svg'];
const videoTypes = ['mp4','avi','mov','mkv','webm'];
const audioTypes = ['mp3','wav','flac','ogg'];

function openPreview(fileId, filename) {
    // Prevent default browser behavior
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    currentPreviewId = fileId;

    const modal          = document.getElementById('previewModal');
    const loading        = document.getElementById('previewLoading');
    const fnLabel        = document.getElementById('previewFilename');
    const previewImg     = document.getElementById('previewImg');
    const previewVideo   = document.getElementById('previewVideo');
    const previewAudio   = document.getElementById('previewAudio');
    const previewPdf     = document.getElementById('previewPdf');
    const previewNoSupport = document.getElementById('previewNoSupport');

    if (!modal) {
        console.error('previewModal not found in HTML!');
        return;
    }

    // Reset all preview elements
    [previewImg, previewVideo, previewAudio,
     previewPdf, previewNoSupport].forEach(el => {
        if (el) el.classList.add('hidden');
    });

    if (previewVideo) {
        previewVideo.pause();
        previewVideo.removeAttribute('src');
        previewVideo.load();
    }

    if (fnLabel) fnLabel.textContent = filename;
    if (loading) loading.classList.remove('hidden');
    modal.classList.remove('hidden');

    const ext = filename.split('.').pop().toLowerCase();
    console.log(`Preview: fileId=${fileId}, filename=${filename}, ext=${ext}`);

    if (imageTypes.includes(ext)) {
        // ── Image: serve through Flask directly ──
        if (previewImg) {
            previewImg.onload = () => {
                console.log('Image loaded successfully!');
                if (loading) loading.classList.add('hidden');
                previewImg.classList.remove('hidden');
            };
            previewImg.onerror = (e) => {
                console.error('Image load error:', e);
                if (loading) loading.classList.add('hidden');
                if (previewNoSupport)
                    previewNoSupport.classList.remove('hidden');
            };
            // Set src AFTER setting onload/onerror
            const previewUrl = `/preview/${fileId}`;
            console.log(`Loading image from: ${previewUrl}`);
            previewImg.src = previewUrl;
        }

    } else if (videoTypes.includes(ext) ||
               audioTypes.includes(ext) ||
               ext === 'pdf') {

        // ── Video/Audio/PDF: get presigned URL ──
        const previewUrl = `/preview/${fileId}`;
        console.log(`Fetching preview URL from: ${previewUrl}`);

        fetch(previewUrl, {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        })
        .then(res => {
            console.log(`Response status: ${res.status}`);
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            return res.json();
        })
        .then(data => {
            console.log('Preview data:', data);
            if (loading) loading.classList.add('hidden');

            if (data.error) {
                console.error('Preview error:', data.error);
                if (previewNoSupport)
                    previewNoSupport.classList.remove('hidden');
                return;
            }

            const url = data.url;

            if (videoTypes.includes(ext) && previewVideo) {
                previewVideo.src = url;
                previewVideo.load();
                previewVideo.classList.remove('hidden');

            } else if (audioTypes.includes(ext) && previewAudio) {
                const audioEl = previewAudio.querySelector('audio');
                if (audioEl) {
                    audioEl.src = url;
                    audioEl.load();
                }
                previewAudio.classList.remove('hidden');

            } else if (ext === 'pdf' && previewPdf) {
                previewPdf.src = url;
                previewPdf.classList.remove('hidden');

            } else {
                if (previewNoSupport)
                    previewNoSupport.classList.remove('hidden');
            }
        })
        .catch(err => {
            console.error('Fetch error:', err);
            if (loading) loading.classList.add('hidden');
            if (previewNoSupport)
                previewNoSupport.classList.remove('hidden');
        });

    } else {
        // Unsupported type
        if (loading) loading.classList.add('hidden');
        if (previewNoSupport)
            previewNoSupport.classList.remove('hidden');
    }
}

function closePreview() {
    const modal = document.getElementById('previewModal');
    const video = document.getElementById('previewVideo');
    const audio = document.querySelector('#previewAudio audio');

    // Stop media
    if (video) { video.pause(); video.src = ''; }
    if (audio) { audio.pause(); audio.src = ''; }

    if (modal) modal.classList.add('hidden');
    currentPreviewId = null;
}

// Close preview when clicking outside
document.getElementById('previewModal')
    ?.addEventListener('click', function(e) {
        if (e.target === this) closePreview();
    });

// ═══════════════════════════════════════
// SHARE TOGGLE
// ═══════════════════════════════════════
async function toggleShare(fileId, button) {
    button.disabled      = true;
    button.style.opacity = '0.5';

    try {
        const res  = await fetch(`/share/${fileId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!res.ok) throw new Error('Request failed');

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
    } catch (err) {
        console.error(err);
        showToast('Something went wrong', 'error');
    } finally {
        button.disabled      = false;
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
            // Fallback for older browsers
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
    document.getElementById('shareModal')
        ?.classList.add('hidden');
}

// Also support old name
function closeModal() { closeShareModal(); }

document.getElementById('shareModal')
    ?.addEventListener('click', function(e) {
        if (e.target === this) closeShareModal();
    });

// ═══════════════════════════════════════
// TOAST NOTIFICATIONS
// ═══════════════════════════════════════
function showToast(message, type = 'success') {
    const map = {
        success: { cls: 'flash-success', icon: 'check-circle'       },
        error:   { cls: 'flash-danger',  icon: 'exclamation-circle'  },
        info:    { cls: 'flash-info',    icon: 'info-circle'          },
    };
    const { cls, icon } = map[type] || map.success;

    const toast = document.createElement('div');
    toast.className  = `flash ${cls}`;
    toast.style.cssText = `
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        max-width: 320px;
    `;
    toast.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity    = '0';
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
document.addEventListener('DOMContentLoaded', () => {
    const navHamburger = document.getElementById('navHamburger');
    const navLinksEl   = document.getElementById('navLinks');

    if (!navHamburger || !navLinksEl) return;

    navHamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        navLinksEl.classList.toggle('open');
        const icon = navHamburger.querySelector('i');
        if (icon) {
            icon.className = navLinksEl.classList.contains('open')
                ? 'fas fa-times'
                : 'fas fa-bars';
        }
    });

    // Close when link clicked
    navLinksEl.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navLinksEl.classList.remove('open');
            const icon = navHamburger.querySelector('i');
            if (icon) icon.className = 'fas fa-bars';
        });
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!navLinksEl.contains(e.target) &&
            !navHamburger.contains(e.target)) {
            navLinksEl.classList.remove('open');
            const icon = navHamburger.querySelector('i');
            if (icon) icon.className = 'fas fa-bars';
        }
    });
});

// ═══════════════════════════════════════
// KEYBOARD SHORTCUTS
// ═══════════════════════════════════════
document.addEventListener('keydown', (e) => {

    // Escape — close all modals
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

    // Press '/' to focus search
    if (e.key === '/' &&
        document.activeElement.tagName !== 'INPUT' &&
        document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        document.getElementById('searchInput')?.focus();
    }
});