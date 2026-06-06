from django.utils import timezone


def global_context(request):
    """Context processor que injeta variáveis globais em todos os templates"""
    now = timezone.now()
    return {
        'current_year': now.year,
        'current_month': now.month,
    }
