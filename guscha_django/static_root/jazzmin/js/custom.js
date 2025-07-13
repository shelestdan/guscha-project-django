// Modern Jazzmin Admin Panel JavaScript
document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Add fade-in animation to all cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fadeIn');
    });

    // Enhanced table sorting
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                sortTable(table, index);
            });
        });
    });

    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('[type="submit"]');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
            }
        });
    });

    // Enhanced tooltips
    const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', showTooltip);
        tooltip.addEventListener('mouseleave', hideTooltip);
    });

    // Search functionality enhancement
    const searchInputs = document.querySelectorAll('.form-control-sidebar, .search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function(e) {
            performSearch(e.target.value);
        }, 300));
    });

    // Dark mode toggle (if needed)
    const darkModeToggle = document.querySelector('#dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add chart initialization
    initializeCharts();

    // Add notification system
    initializeNotifications();
});

// Table sorting function
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isAscending = table.dataset.sortOrder !== 'asc';
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return isAscending ? aValue - bValue : bValue - aValue;
        }
        
        return isAscending ? 
            aValue.localeCompare(bValue) : 
            bValue.localeCompare(aValue);
    });
    
    table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
    
    rows.forEach(row => tbody.appendChild(row));
}

// Debounce function for search
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

// Search function
function performSearch(query) {
    console.log('Searching for:', query);
    // Implement your search logic here
}

// Tooltip functions
function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = e.target.getAttribute('title');
    tooltip.style.position = 'absolute';
    tooltip.style.top = e.pageY + 10 + 'px';
    tooltip.style.left = e.pageX + 10 + 'px';
    document.body.appendChild(tooltip);
    e.target.dataset.tooltipId = tooltip.id = 'tooltip-' + Date.now();
}

function hideTooltip(e) {
    const tooltipId = e.target.dataset.tooltipId;
    const tooltip = document.getElementById(tooltipId);
    if (tooltip) {
        tooltip.remove();
    }
}

// Dark mode toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Chart initialization
function initializeCharts() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        return;
    }

    // Sales chart
    const salesChartCanvas = document.getElementById('salesChart');
    if (salesChartCanvas) {
        const ctx = salesChartCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'],
                datasets: [{
                    label: 'Продажи',
                    data: [12000, 19000, 15000, 25000, 22000, 30000],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₽' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    // Orders chart
    const ordersChartCanvas = document.getElementById('ordersChart');
    if (ordersChartCanvas) {
        const ctx = ordersChartCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                datasets: [{
                    label: 'Заказы',
                    data: [65, 59, 80, 81, 56, 55, 40],
                    backgroundColor: '#3b82f6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

// Notification system
function initializeNotifications() {
    // Create notification container
    const notificationContainer = document.createElement('div');
    notificationContainer.id = 'notification-container';
    notificationContainer.style.position = 'fixed';
    notificationContainer.style.top = '20px';
    notificationContainer.style.right = '20px';
    notificationContainer.style.zIndex = '9999';
    document.body.appendChild(notificationContainer);
}

// Show notification function
window.showNotification = function(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} fadeIn`;
    notification.style.cssText = `
        background: white;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        min-width: 300px;
    `;

    const icon = document.createElement('i');
    icon.className = 'fas ';
    switch(type) {
        case 'success':
            icon.className += 'fa-check-circle';
            icon.style.color = '#10b981';
            break;
        case 'error':
            icon.className += 'fa-exclamation-circle';
            icon.style.color = '#ef4444';
            break;
        case 'warning':
            icon.className += 'fa-exclamation-triangle';
            icon.style.color = '#f59e0b';
            break;
        default:
            icon.className += 'fa-info-circle';
            icon.style.color = '#3b82f6';
    }

    notification.innerHTML = `${icon.outerHTML}<span>${message}</span>`;
    
    const container = document.getElementById('notification-container');
    container.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, duration);
};

// Add real-time updates simulation
setInterval(() => {
    // Update random stats
    const statNumbers = document.querySelectorAll('.info-box-number, .small-box h3');
    statNumbers.forEach(stat => {
        if (Math.random() > 0.8) {
            const currentValue = parseInt(stat.textContent.replace(/\D/g, ''));
            const change = Math.floor(Math.random() * 10) - 5;
            const newValue = Math.max(0, currentValue + change);
            animateValue(stat, currentValue, newValue, 500);
        }
    });
}, 5000);

// Animate number changes
function animateValue(element, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();
    
    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentValue = Math.floor(start + range * progress);
        
        element.textContent = currentValue.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }
    
    requestAnimationFrame(updateValue);
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.form-control-sidebar, .search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Ctrl/Cmd + S for save (in forms)
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const activeForm = document.querySelector('form:focus-within');
        if (activeForm) {
            activeForm.dispatchEvent(new Event('submit'));
        }
    }
});

// Custom styling for select2 if present
if (typeof $.fn.select2 !== 'undefined') {
    $('.select2').select2({
        theme: 'bootstrap4',
        width: '100%'
    });
}

// Initialize date pickers if present
if (typeof $.fn.daterangepicker !== 'undefined') {
    $('.date-range-picker').daterangepicker({
        locale: {
            format: 'DD.MM.YYYY'
        }
    });
}

// Add CSV export functionality
window.exportTableToCSV = function(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => 
            '"' + col.textContent.trim().replace(/"/g, '""') + '"'
        );
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename || 'export.csv';
    link.click();
};
