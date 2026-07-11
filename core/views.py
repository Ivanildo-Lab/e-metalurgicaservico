from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import permission_required_module
from django.contrib import messages
from .models import ParametroSistema
from .forms import ParametroForm

@login_required
@permission_required_module('core')
def configuracoes_sistema(request):
    empresa = request.user.empresa
    
    # 1. Garante que os parâmetros padrão existam para esta empresa
    parametros_padrao = [
        'CAIXA_PADRAO_ID', 
        'TAXA_JUROS_MENSAL', 
        'PLANO_CONTAS_MENSALIDADE_ID',
        'PLANO_CONTAS_JUROS_ID'
    ]
    
    for chave in parametros_padrao:
        ParametroSistema.objects.get_or_create(
            empresa=empresa, 
            chave=chave,
            defaults={'valor': '0', 'descricao': 'Configuração automática'}
        )

    # 2. Lista todos
    parametros = ParametroSistema.objects.filter(empresa=empresa)
    
    return render(request, 'core/configuracoes.html', {'parametros': parametros})

@login_required
@permission_required_module('core')
def editar_parametro(request, id):
    parametro = get_object_or_404(ParametroSistema, id=id, empresa=request.user.empresa)
    
    if request.method == 'POST':
        form = ParametroForm(request.POST, instance=parametro)
        if form.is_valid():
            form.save()
            messages.success(request, "Parâmetro atualizado com sucesso!")
            return redirect('configuracoes')
    else:
        form = ParametroForm(instance=parametro)
        
    return render(request, 'core/parametro_form.html', {'form': form, 'parametro': parametro})
