// Кастомный JavaScript для Django Unfold админки

// Глобальные переменные для экземпляров графиков
let salesChart = null;
let productsChart = null;
let revenueChart = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    initializeCharts();
    initializeNotifications();
    initializeRealTimeUpdates();
    initializeThemeObserver();
});

// Инициализация дашборда
function initializeDashboard() {
    // Анимация карточек при загрузке
    const cards = document.querySelectorAll('.dashboard-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease-out';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Добавление hover эффектов
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Инициализация графиков
function initializeCharts() {
    // Проверяем наличие Chart.js
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js не загружен');
        return;
    }
    
    updateChartDefaults();
    
    // Инициализация графика продаж
    initializeSalesChart();
    
    // Инициализация графика товаров
    initializeProductsChart();
    
    // Инициализация графика выручки
    initializeRevenueChart();
}

// Обновление настроек по умолчанию для графиков
function updateChartDefaults() {
    const isDark = document.documentElement.classList.contains('dark');
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    Chart.defaults.color = isDark ? '#9ca3af' : '#6b7280';
    Chart.defaults.borderColor = isDark ? '#374151' : '#e5e7eb';
}

// Функция для обновления цветов всех графиков при смене темы
function updateChartsTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    
    updateChartDefaults();
    
    // Обновляем цвета для графика продаж
    if (salesChart) {
        salesChart.options.scales.x.ticks.color = isDark ? '#9ca3af' : '#6b7280';
        salesChart.options.scales.y.ticks.color = isDark ? '#9ca3af' : '#6b7280';
        salesChart.options.scales.y.grid.color = isDark ? '#374151' : '#f3f4f6';
        
        // Обновляем цвета линии и фона
        salesChart.data.datasets[0].backgroundColor = isDark ? 'rgba(168, 85, 247, 0.2)' : 'rgba(168, 85, 247, 0.1)';
        salesChart.data.datasets[0].borderColor = '#a855f7';
        salesChart.data.datasets[0].pointBorderColor = isDark ? '#1f2937' : '#ffffff';
        
        // Обновляем tooltip
        salesChart.options.plugins.tooltip.backgroundColor = isDark ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)';
        salesChart.options.plugins.tooltip.titleColor = isDark ? '#ffffff' : '#1f2937';
        salesChart.options.plugins.tooltip.bodyColor = isDark ? '#ffffff' : '#1f2937';
        
        salesChart.update('none');
    }
    
    // Обновляем цвета для графика товаров
    if (productsChart) {
        productsChart.options.plugins.legend.labels.color = isDark ? '#e5e7eb' : '#374151';
        
        // Обновляем цвета секторов для лучшей видимости в темной теме
        if (isDark) {
            productsChart.data.datasets[0].backgroundColor = [
                '#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'
            ];
        } else {
            productsChart.data.datasets[0].backgroundColor = [
                '#a855f7', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'
            ];
        }
        
        // Обновляем tooltip
        productsChart.options.plugins.tooltip.backgroundColor = isDark ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)';
        productsChart.options.plugins.tooltip.titleColor = isDark ? '#ffffff' : '#1f2937';
        productsChart.options.plugins.tooltip.bodyColor = isDark ? '#ffffff' : '#1f2937';
        
        productsChart.update('none');
    }
    
    // Обновляем цвета для графика выручки
    if (revenueChart) {
        revenueChart.options.scales.x.ticks.color = isDark ? '#9ca3af' : '#6b7280';
        revenueChart.options.scales.y.ticks.color = isDark ? '#9ca3af' : '#6b7280';
        revenueChart.options.scales.y.grid.color = isDark ? '#374151' : '#f3f4f6';
        
        // Обновляем цвета столбцов
        revenueChart.data.datasets[0].backgroundColor = isDark ? 'rgba(168, 85, 247, 0.9)' : 'rgba(168, 85, 247, 0.8)';
        revenueChart.data.datasets[0].borderColor = '#a855f7';
        
        // Обновляем tooltip
        revenueChart.options.plugins.tooltip.backgroundColor = isDark ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)';
        revenueChart.options.plugins.tooltip.titleColor = isDark ? '#ffffff' : '#1f2937';
        revenueChart.options.plugins.tooltip.bodyColor = isDark ? '#ffffff' : '#1f2937';
        
        revenueChart.update('none');
    }
}

// Наблюдатель за изменениями темы
function initializeThemeObserver() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                updateChartsTheme();
            }
        });
    });
    
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
    });
}

// График продаж
function initializeSalesChart() {
    const ctx = document.getElementById('salesChart');
    if (!ctx) return;
    
    // Получаем данные с сервера
    fetchSalesData().then(data => {
        salesChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'],
                datasets: [{
                    label: 'Продажи',
                    data: data.sales || [12, 19, 3, 5, 2, 3],
                    borderColor: '#a855f7',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#a855f7',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: document.documentElement.classList.contains('dark') ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)',
                        titleColor: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1f2937',
                        bodyColor: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1f2937',
                        borderColor: '#a855f7',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: document.documentElement.classList.contains('dark') ? '#374151' : '#f3f4f6'
                        },
                        ticks: {
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280'
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    });
}

// График популярных товаров
function initializeProductsChart() {
    const ctx = document.getElementById('productsChart');
    if (!ctx) return;
    
    fetchProductsData().then(data => {
        productsChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || ['Товар 1', 'Товар 2', 'Товар 3', 'Товар 4'],
                datasets: [{
                    data: data.values || [30, 25, 20, 25],
                    backgroundColor: [
                        '#a855f7',
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b',
                        '#ef4444'
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151'
                        }
                    },
                    tooltip: {
                        backgroundColor: document.documentElement.classList.contains('dark') ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)',
                        titleColor: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1f2937',
                        bodyColor: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1f2937',
                        borderColor: '#a855f7',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${percentage}%`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 2000
                }
            }
        });
    });
}

// График выручки
function initializeRevenueChart() {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;
    
    fetchRevenueData().then(data => {
        revenueChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                datasets: [{
                    label: 'Выручка',
                    data: data.revenue || [1200, 1900, 800, 1500, 2000, 1800, 2400],
                    backgroundColor: 'rgba(168, 85, 247, 0.8)',
                    borderColor: '#a855f7',
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: document.documentElement.classList.contains('dark') ? 'rgba(0, 0, 0, 0.9)' : 'rgba(255, 255, 255, 0.95)',
                        titleColor: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1f2937',
                        bodyColor: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1f2937',
                        borderColor: '#a855f7',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                return `Выручка: ₽${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: document.documentElement.classList.contains('dark') ? '#374151' : '#f3f4f6'
                        },
                        ticks: {
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280',
                            callback: function(value) {
                                return '₽' + value.toLocaleString();
                            }
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutBounce'
                }
            }
        });
    });
}

// Функции для получения данных с сервера
async function fetchSalesData() {
    try {
        const response = await fetch('/api/admin/sales-data/');
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.warn('Не удалось загрузить данные продаж:', error);
    }
    // Возвращаем тестовые данные
    return {
        labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн'],
        sales: [12, 19, 3, 5, 2, 3]
    };
}

async function fetchProductsData() {
    try {
        const response = await fetch('/api/admin/products-data/');
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.warn('Не удалось загрузить данные товаров:', error);
    }
    return {
        labels: ['Товар 1', 'Товар 2', 'Товар 3', 'Товар 4'],
        values: [30, 25, 20, 25]
    };
}

async function fetchRevenueData() {
    try {
        const response = await fetch('/api/admin/revenue-data/');
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
        console.warn('Не удалось загрузить данные выручки:', error);
    }
    return {
        labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
        revenue: [1200, 1900, 800, 1500, 2000, 1800, 2400]
    };
}

// Инициализация уведомлений
function initializeNotifications() {
    // Автоматическое скрытие уведомлений
    const notifications = document.querySelectorAll('.notification');
    notifications.forEach(notification => {
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    });
}

// Функция для показа уведомлений
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in forwards';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Обновление данных в реальном времени
function initializeRealTimeUpdates() {
    // Обновляем статистику каждые 30 секунд
    setInterval(updateDashboardStats, 30000);
}

// Обновление статистики дашборда
async function updateDashboardStats() {
    try {
        const response = await fetch('/api/admin/dashboard-stats/');
        if (response.ok) {
            const data = await response.json();
            
            // Обновляем счетчики
            updateCounter('total_users', data.total_users);
            updateCounter('total_products', data.total_products);
            updateCounter('total_orders', data.total_orders);
            updateCounter('total_revenue', data.total_revenue);
        }
    } catch (error) {
        console.warn('Не удалось обновить статистику:', error);
    }
}

// Анимированное обновление счетчика
function updateCounter(elementId, newValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const currentValue = parseInt(element.textContent.replace(/[^0-9]/g, '')) || 0;
    const increment = (newValue - currentValue) / 20;
    let current = currentValue;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= newValue) || (increment < 0 && current <= newValue)) {
            current = newValue;
            clearInterval(timer);
        }
        
        if (elementId === 'total_revenue') {
            element.textContent = '₽ ' + Math.floor(current).toLocaleString();
        } else {
            element.textContent = Math.floor(current).toLocaleString();
        }
    }, 50);
}

// Утилиты
function formatNumber(num) {
    return num.toLocaleString('ru-RU');
}

function formatCurrency(amount) {
    return '₽ ' + amount.toLocaleString('ru-RU');
}

// CSS анимации для slideOut
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);