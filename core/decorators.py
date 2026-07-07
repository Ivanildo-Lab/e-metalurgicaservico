from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


# Módulos na ordem de prioridade para redirecionamento
MODULOS_ORDEM = [
    ('web', 'dashboard', 'Painel'),
    ('servicos', 'servicos:lista_ordens', 'Serviços'),
    ('cadastros', 'lista_clientes', 'Cadastros'),
    ('financeiro', 'financeiro:fluxo_caixa', 'Financeiro'),
    ('core', 'configuracoes', 'Configurações'),
]


def primeiro_modulo_acessivel(user):
    """Retorna a URL do primeiro módulo que o usuário tem permissão."""
    if user.is_superuser:
        return None
    for app_label, url_name, _ in MODULOS_ORDEM:
        perm = f'{app_label}.acesso_modulo'
        if user.has_perm(perm):
            return url_name
    return None


def permission_required_module(module_label):
    """
    Decorator que verifica se o usuário tem acesso a um módulo.
    Redireciona para o primeiro módulo acessível se não tiver permissão.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            perm = f'{module_label}.acesso_modulo'
            if not request.user.has_perm(perm):
                url = primeiro_modulo_acessivel(request.user)
                if url:
                    messages.warning(request, 'Você não tem acesso a este módulo. Redirecionando...')
                    return redirect(url)
                messages.error(request, 'Acesso negado. Nenhum módulo disponível para seu perfil.')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
