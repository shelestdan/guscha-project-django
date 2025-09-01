from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def csp_nonce(context):
    """Возвращает CSP nonce для использования в script и style тегах"""
    request = context.get('request')
    if request and hasattr(request, 'csp_nonce'):
        return request.csp_nonce
    return ''

@register.simple_tag(takes_context=True)
def script_nonce(context):
    """Возвращает атрибут nonce для script тегов"""
    request = context.get('request')
    if request and hasattr(request, 'csp_nonce'):
        return mark_safe(f'nonce="{request.csp_nonce}"')
    return ''

@register.simple_tag(takes_context=True)
def style_nonce(context):
    """Возвращает атрибут nonce для style тегов"""
    request = context.get('request')
    if request and hasattr(request, 'csp_nonce'):
        return mark_safe(f'nonce="{request.csp_nonce}"')
    return ''