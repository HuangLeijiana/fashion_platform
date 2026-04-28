document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.querySelector('.navbar');
    const animatedCards = document.querySelectorAll('.feature-card, .benefit-item, .card, .clothing-item');

    // ===== 导航渐变随滚动轻微变化 =====
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 80) {
                navbar.style.background = 'rgba(255, 255, 255, 0.88)';
                navbar.style.backdropFilter = 'blur(14px)';
            } else {
                navbar.style.background = 'rgba(255, 255, 255, 0.72)';
                navbar.style.backdropFilter = 'blur(10px)';
            }
        });
    }

    // ===== 卡片入场动画 =====
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0) scale(1)';
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