// AutoHire - Main JavaScript File
```
'''
Author:     Shakeeb Shaikh
LinkedIn:  https://www.linkedin.com/in/shakeeb-shaikh-02b32b282/=
            
GitHub:     https://github.com/ShakeebSk
'''

```
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeNavbar();
    initializeAnimations();
    initializeFormValidation();
    initializeTooltips();
    initializeProgressBars();
    initializeCounters();
    initializeFileUpload();
    initializeLoadingStates();
});

// Navbar functionality
function initializeNavbar() {
    const navbar = document.querySelector('.navbar');
    
    // Change navbar background on scroll
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Animation functionality
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.feature-card, .step-card, .stats-card').forEach(el => {
        observer.observe(el);
    });
    
    // Animate counters
    const animateCounters = () => {
        document.querySelectorAll('[data-counter]').forEach(counter => {
            const target = parseInt(counter.getAttribute('data-counter'));
            const current = parseInt(counter.innerText) || 0;
            const increment = target / 100;
            
            if (current < target) {
                counter.innerText = Math.ceil(current + increment);
                setTimeout(animateCounters, 20);
            } else {
                counter.innerText = target;
            }
        });
    };
    
    // Trigger counter animation when visible
    const counterObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounters();
                counterObserver.unobserve(entry.target);
            }
        });
    });
    
    document.querySelectorAll('[data-counter]').forEach(counter => {
        counterObserver.observe(counter);
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });
}

// Field validation helper
function validateField(field) {
    const isValid = field.checkValidity();
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        
        if (feedback) {
            if (field.validity.valueMissing) {
                feedback.textContent = `${field.getAttribute('data-field-name') || 'This field'} is required.`;
            } else if (field.validity.typeMismatch) {
                feedback.textContent = 'Please enter a valid format.';
            } else if (field.validity.tooShort) {
                feedback.textContent = `Minimum ${field.minLength} characters required.`;
            } else if (field.validity.patternMismatch) {
                feedback.textContent = field.getAttribute('data-pattern-error') || 'Invalid format.';
            }
        }
    }
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Progress bars animation
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    const progressObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const progressBar = entry.target;
                const targetWidth = progressBar.getAttribute('data-progress') || progressBar.style.width;
                
                progressBar.style.width = '0%';
                setTimeout(() => {
                    progressBar.style.width = targetWidth;
                }, 200);
                
                progressObserver.unobserve(progressBar);
            }
        });
    });
    
    progressBars.forEach(bar => {
        progressObserver.observe(bar);
    });
}

// Initialize counters
function initializeCounters() {
    function animateCounter(element, target, duration = 2000) {
        let start = 0;
        const range = target - start;
        const startTime = performance.now();
        
        function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(progress * range + start);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target;
            }
        }
        
        requestAnimationFrame(updateCounter);
    }
    
    const counterObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-count'));
                animateCounter(counter, target);
                counterObserver.unobserve(counter);
            }
        });
    });
    
    document.querySelectorAll('[data-count]').forEach(counter => {
        counterObserver.observe(counter);
    });
}

// File upload functionality
function initializeFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const label = input.nextElementSibling;
        const originalText = label ? label.textContent : 'Choose file';
        
        input.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : originalText;
            if (label) {
                label.textContent = fileName;
            }
            
            // Add visual feedback
            if (this.files[0]) {
                this.classList.add('file-selected');
                if (label) label.classList.add('file-selected');
            } else {
                this.classList.remove('file-selected');
                if (label) label.classList.remove('file-selected');
            }
        });
    });
}

// Loading states
function initializeLoadingStates() {
    // Add loading state to buttons on form submit
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                showLoadingState(submitBtn);
            }
        });
    });
}

// Show loading state for buttons
function showLoadingState(button, text = 'Loading...') {
    const originalText = button.innerHTML;
    const originalDisabled = button.disabled;
    
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        ${text}
    `;
    button.disabled = true;
    
    // Store original state for restoration
    button.dataset.originalText = originalText;
    button.dataset.originalDisabled = originalDisabled;
}

// Hide loading state
function hideLoadingState(button) {
    const originalText = button.dataset.originalText;
    const originalDisabled = button.dataset.originalDisabled === 'true';
    
    if (originalText) {
        button.innerHTML = originalText;
        button.disabled = originalDisabled;
        
        delete button.dataset.originalText;
        delete button.dataset.originalDisabled;
    }
}

// AJAX helper function
function makeAjaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const config = { ...defaultOptions, ...options };
    
    return fetch(url, config)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '100px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Copy to clipboard functionality
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success', 3000);
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification('Copied to clipboard!', 'success', 3000);
    } catch (err) {
        showNotification('Failed to copy to clipboard', 'danger', 3000);
    }
    
    document.body.removeChild(textArea);
}

// Debounce helper function
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

// Throttle helper function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Format date
function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    const config = { ...defaultOptions, ...options };
    return new Date(date).toLocaleDateString('en-US', config);
}

// Validate email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Local storage helpers
const Storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Storage set error:', e);
            return false;
        }
    },
    
    get: function(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.error('Storage get error:', e);
            return null;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Storage remove error:', e);
            return false;
        }
    }
};

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // You can send error reports to your server here
});

// Export functions for use in other scripts
window.AutoHire = {
    showLoadingState,
    hideLoadingState,
    makeAjaxRequest,
    showNotification,
    copyToClipboard,
    debounce,
    throttle,
    formatNumber,
    formatDate,
    isValidEmail,
    Storage
};
