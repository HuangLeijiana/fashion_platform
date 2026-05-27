const liquidTargetSelector = [
    '.hero-badge',
    '.stat-card',
    '.flow-card',
    '.feature-card',
    '.card',
    '.clothing-card',
    '.product-card',
    '.filter-toolbar',
    '.search-box',
    '.advanced-search-panel .card',
    '.dropdown-menu',
    '.modal-content',
    '.auth-wrapper',
    '.btn',
    '.nav-link',
    '.dropdown-item'
].join(', ');

function liquidMotionAllowed() {
    return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function liquidPointerAllowed() {
    return window.matchMedia('(hover: hover) and (pointer: fine)').matches;
}

function resetLiquidState(element) {
    if (!element) return;
    element.style.setProperty('--liquid-glow-x', '50%');
    element.style.setProperty('--liquid-glow-y', '26%');
    element.style.setProperty('--liquid-tilt-x', '0deg');
    element.style.setProperty('--liquid-tilt-y', '0deg');
    element.style.setProperty('--liquid-scale', '1');
    element.style.setProperty('--liquid-lift', '0px');
}

function bindLiquidSurface(element) {
    if (!element || element.dataset.liquidReady === 'true') return;

    const isInteractive = element.matches('.btn, .nav-link, .dropdown-item');
    element.dataset.liquidReady = 'true';
    element.classList.add(isInteractive ? 'liquid-interactive' : 'liquid-surface');
    resetLiquidState(element);

    if (!liquidMotionAllowed() || !liquidPointerAllowed()) return;

    let frameId = null;

    const updateFromPointer = function(event) {
        const rect = element.getBoundingClientRect();
        if (!rect.width || !rect.height) return;

        const x = Math.min(Math.max(event.clientX - rect.left, 0), rect.width);
        const y = Math.min(Math.max(event.clientY - rect.top, 0), rect.height);
        const ratioX = x / rect.width;
        const ratioY = y / rect.height;

        if (frameId) cancelAnimationFrame(frameId);

        frameId = requestAnimationFrame(function() {
            const tiltX = ((0.5 - ratioY) * (isInteractive ? 5 : 7)).toFixed(2) + 'deg';
            const tiltY = ((ratioX - 0.5) * (isInteractive ? 7 : 9)).toFixed(2) + 'deg';

            element.style.setProperty('--liquid-glow-x', (ratioX * 100).toFixed(2) + '%');
            element.style.setProperty('--liquid-glow-y', (ratioY * 100).toFixed(2) + '%');
            element.style.setProperty('--liquid-tilt-x', tiltX);
            element.style.setProperty('--liquid-tilt-y', tiltY);
            element.style.setProperty('--liquid-scale', isInteractive ? '1.02' : '1.012');
            if (!isInteractive) {
                element.style.setProperty('--liquid-lift', '-6px');
            }
        });
    };

    const resetPointerState = function() {
        if (frameId) cancelAnimationFrame(frameId);
        frameId = requestAnimationFrame(function() {
            resetLiquidState(element);
        });
    };

    element.addEventListener('pointerenter', updateFromPointer, { passive: true });
    element.addEventListener('pointermove', updateFromPointer, { passive: true });
    element.addEventListener('pointerleave', resetPointerState, { passive: true });
    element.addEventListener('pointercancel', resetPointerState, { passive: true });
    element.addEventListener('pointerdown', function() {
        element.style.setProperty('--liquid-scale', isInteractive ? '0.985' : '0.996');
    }, { passive: true });
    element.addEventListener('pointerup', function() {
        element.style.setProperty('--liquid-scale', isInteractive ? '1.02' : '1.012');
    }, { passive: true });
}

function setupLiquidGlass(root) {
    const scope = root || document;
    const targets = [];

    if (scope.nodeType === 1 && scope.matches && scope.matches(liquidTargetSelector)) {
        targets.push(scope);
    }

    if (scope.querySelectorAll) {
        scope.querySelectorAll(liquidTargetSelector).forEach(function(element) {
            targets.push(element);
        });
    }

    targets.forEach(bindLiquidSurface);
}

function observeLiquidGlass() {
    if (!document.body || document.body.dataset.liquidObserved === 'true') return;

    document.body.dataset.liquidObserved = 'true';

    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) {
                    setupLiquidGlass(node);
                }
            });
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

window.setupLiquidGlass = setupLiquidGlass;

document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('.navbar');
    const animatedCards = document.querySelectorAll('.feature-card, .benefit-item, .card, .clothing-item');

    // ===== 导航渐变随滚动轻微变化 =====
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 80) {
                navbar.style.background = 'linear-gradient(180deg, rgba(255, 255, 255, 0.84) 0%, rgba(255, 255, 255, 0.62) 100%), linear-gradient(135deg, rgba(255, 255, 255, 0.52) 0%, rgba(255, 255, 255, 0.34) 100%)';
                navbar.style.backdropFilter = 'saturate(190%) blur(28px)';
                navbar.style.webkitBackdropFilter = 'saturate(190%) blur(28px)';
                navbar.style.boxShadow = '0 0 0 0.5px rgba(255, 255, 255, 0.68), 0 14px 30px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.78), inset 0 -1px 0 rgba(255, 255, 255, 0.16)';
            } else {
                navbar.style.background = 'linear-gradient(180deg, rgba(255, 255, 255, 0.68) 0%, rgba(255, 255, 255, 0.44) 100%), linear-gradient(135deg, rgba(255, 255, 255, 0.46) 0%, rgba(255, 255, 255, 0.30) 100%)';
                navbar.style.backdropFilter = 'saturate(185%) blur(24px)';
                navbar.style.webkitBackdropFilter = 'saturate(185%) blur(24px)';
                navbar.style.boxShadow = '0 0 0 0.5px rgba(255, 255, 255, 0.64), 0 12px 28px rgba(15, 23, 42, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.72), inset 0 -1px 0 rgba(255, 255, 255, 0.18)';
            }
        });
    }

    // ===== 卡片入场动画 =====
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0) scale(1)';
                window.setTimeout(function() {
                    entry.target.style.removeProperty('transform');
                }, 760);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px'
    });

    animatedCards.forEach(function(el, index) {
        el.style.opacity = '0';
        el.style.transform = 'translateY(26px) scale(0.98)';
        el.style.transition = 'opacity 0.72s ease, transform 0.72s cubic-bezier(.22,1,.36,1)';
        el.style.transitionDelay = (index % 6) * 0.06 + 's';
        observer.observe(el);
    });

    // ===== 锚点丝滑滚动 =====
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            var targetId = this.getAttribute('href');
            if (!targetId || targetId === '#') return;
            var target = document.querySelector(targetId);
            if (!target) return;
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    setupLiquidGlass(document);
    observeLiquidGlass();
});

// ===== 兼容旧页面的搜索范围函数 =====
function setSearchScope(scope) {
    try {
        const input = document.getElementById('searchInput');
        const wardrobeSwitch = document.getElementById('wardrobeOnly');
        if (scope === 'wardrobe') {
            if (wardrobeSwitch) wardrobeSwitch.checked = true;
            localStorage.setItem('search_scope', 'wardrobe');
        } else {
            if (wardrobeSwitch) wardrobeSwitch.checked = false;
            localStorage.setItem('search_scope', 'all');
        }
        if (input) input.focus();
    } catch (e) {
        console.warn('setSearchScope error:', e);
    }
}
window.setSearchScope = setSearchScope;

function _addClothingItem(data) {
    console.log('添加商品:', data);
}
window._addClothingItem = _addClothingItem;

if (window._clothingQueue && window._clothingQueue.length) {
    window._clothingQueue.forEach(function(data) {
        _addClothingItem(data);
    });
    window._clothingQueue = [];
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';

    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(function() {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

function deleteClothingItem(itemId, itemName) {
    if (!confirm('确定要删除“' + itemName + '”吗？此操作不可撤销。')) return;

    const deleteBtn = document.querySelector('.delete-btn[data-item-id="' + itemId + '"]');
    if (!deleteBtn) return;

    const originalText = deleteBtn.innerHTML;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 删除中...';
    deleteBtn.disabled = true;

    fetch('/wardrobe/delete/' + itemId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.success) {
            const itemElement = document.querySelector('.clothing-item[data-item-id="' + itemId + '"]');
            if (itemElement) {
                itemElement.style.opacity = '0';
                itemElement.style.transform = 'translateY(12px)';
                setTimeout(function() {
                    itemElement.remove();
                    showAlert('删除成功', 'success');
                }, 320);
            }
        } else {
            showAlert(data.message || '删除失败', 'danger');
            deleteBtn.innerHTML = originalText;
            deleteBtn.disabled = false;
        }
    })
    .catch(function(error) {
        console.error('删除错误:', error);
        showAlert('网络错误，请重试', 'danger');
        deleteBtn.innerHTML = originalText;
        deleteBtn.disabled = false;
    });
}

document.addEventListener('click', function(e) {
    const button = e.target.closest('.delete-btn');
    if (!button) return;
    deleteClothingItem(button.getAttribute('data-item-id'), button.getAttribute('data-item-name'));
});
