from django import template
from django.utils import timezone
from django.utils.html import format_html

register = template.Library()

@register.filter
def time_remaining_display(reservation):
    """Отображает оставшееся время резервирования"""
    if reservation.status != 'active':
        return '-'
    
    now = timezone.now()
    if reservation.expires_at <= now:
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">Истекло</span>'
        )
    
    remaining = reservation.expires_at - now
    minutes = int(remaining.total_seconds() // 60)
    seconds = int(remaining.total_seconds() % 60)
    
    if minutes > 0:
        time_str = f'{minutes}м {seconds}с'
    else:
        time_str = f'{seconds}с'
    
    color = '#dc3545' if minutes < 5 else '#ffc107' if minutes < 15 else '#28a745'
    return format_html(
        '<span style="color: {}; font-weight: bold;">{}</span>',
        color, time_str
    )