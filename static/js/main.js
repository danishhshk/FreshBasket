/**
 * FreshBasket Main JavaScript
 * Handles client-side interactions and UI enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeCart();
    initializeAlerts();
});

/**
 * Initialize cart functionality
 */
function initializeCart() {
    updateCartCount();
}

/**
 * Update cart item count display
 */
function updateCartCount() {
    // This would be dynamically updated from the backend
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        // Fetch cart count from server or use session data
        // For now, it's handled server-side
    }
}

/**
 * Initialize alert auto-dismiss
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Auto-dismiss alerts after 5 seconds
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 300ms ease';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });
}

/**
 * Format currency to USD
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Handle form submission with validation
 */
function validateCheckoutForm(form) {
    const address = form.querySelector('[name="shipping_address"]');
    
    if (!address || !address.value.trim()) {
        alert('Please enter a shipping address');
        return false;
    }
    
    return true;
}

/**
 * Smooth scroll to element
 */
function smoothScroll(target) {
    const element = document.querySelector(target);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Add loading state to button
 */
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = 'Loading...';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText;
    }
}

/**
 * Debounce function for search
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Handle search with debounce
 */
const handleSearch = debounce(function(searchTerm) {
    // Auto-submit search form after user stops typing for 500ms
    if (searchTerm.length > 0) {
        const form = document.querySelector('.search-form');
        if (form) {
            form.submit();
        }
    }
}, 500);

/**
 * Initialize search listeners
 */
document.querySelectorAll('.search-form input').forEach(input => {
    input.addEventListener('input', function() {
        handleSearch(this.value);
    });
});

/**
 * Prevent double submission
 */
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitButton = this.querySelector('[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
        }
    });
});

/**
 * Handle responsive navigation toggle
 */
function toggleNavMenu() {
    const menu = document.querySelector('.navbar-menu');
    if (menu) {
        menu.classList.toggle('active');
    }
}

/**
 * Lazy load images
 */
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading
if ('IntersectionObserver' in window) {
    lazyLoadImages();
}

/**
 * Format date to readable format
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/**
 * Handle quantity input validation
 */
document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('change', function() {
        const min = parseInt(this.min) || 1;
        const max = parseInt(this.max) || Infinity;
        const value = parseInt(this.value) || min;
        
        if (value < min) this.value = min;
        if (value > max) this.value = max;
    });
});

/**
 * Export functions for inline scripts
 */
window.FreshBasket = {
    formatCurrency,
    isValidEmail,
    validateCheckoutForm,
    smoothScroll,
    setButtonLoading,
    debounce
};
