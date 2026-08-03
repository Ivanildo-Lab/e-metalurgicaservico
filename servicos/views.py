from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import permission_required_module
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.http import JsonResponse
from cadastros.models import Cadastro

from core.models import ParametroSistema
from financeiro.models import Conta, Lancamento, Caixa, PlanoDeContas

from .models import (
    Funcionario, OrdemServico, ServicoOS, FuncionarioOS,
    MetaFuncionario, Orcamento, ServicoOrcamento, FormaPagamento
)
from .forms import (
    FuncionarioForm, OrdemServicoForm, ServicoOSForm, FuncionarioOSForm,
    FecharOSForm, MetaFuncionarioForm, OrcamentoForm, ServicoOrcamentoForm,
    FormaPagamentoForm,
)


# ==========================================================
# 1. CRUD DE FUNCIONÁRIOS
# ==========================================================
@login_required
@permission_required_module('servicos')
def lista_funcionarios(request):
    q = request.GET.get('q', '')
    status_filtro = request.GET.get('status', '')
    funcionarios = Funcionario.objects.filter(empresa=request.user.empresa)
    if q:
        funcionarios = funcionarios.filter(nome__icontains=q)
    if status_filtro == 'ATIVO':
        funcionarios = funcionarios.filter(ativo=True)
    elif status_filtro == 'INATIVO':
        funcionarios = funcionarios.filter(ativo=False)
    return render(request, 'servicos/funcionario_list.html', {
        'funcionarios': funcionarios,
        'q': q,
        'status_filtro': status_filtro,
    })


@login_required
@permission_required_module('servicos')
def novo_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, user=request.user)
        if form.is_valid():
            nome = form.cleaned_data['nome'].strip()
            if Funcionario.objects.filter(empresa=request.user.empresa, nome__iexact=nome).exists():
                messages.error(request, f'Já existe um funcionário "{nome}" cadastrado para esta empresa.')
            else:
                obj = form.save(commit=False)
                obj.empresa = request.user.empresa
                obj.save()
                messages.success(request, "Funcionário cadastrado com sucesso!")
                return redirect('servicos:lista_funcionarios')
    else:
        form = FuncionarioForm(user=request.user)
    return render(request, 'servicos/funcionario_form.html', {'form': form, 'editar': False})


@login_required
@permission_required_module('servicos')
def editar_funcionario(request, id):
    obj = get_object_or_404(Funcionario, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            nome = form.cleaned_data['nome'].strip()
            if Funcionario.objects.filter(empresa=request.user.empresa, nome__iexact=nome).exclude(id=obj.id).exists():
                messages.error(request, f'Já existe um funcionário "{nome}" cadastrado para esta empresa.')
            else:
                form.save()
                messages.success(request, "Funcionário atualizado com sucesso!")
                return redirect('servicos:lista_funcionarios')
    else:
        form = FuncionarioForm(instance=obj, user=request.user)
    return render(request, 'servicos/funcionario_form.html', {'form': form, 'editar': True})


@login_required
@permission_required_module('servicos')
def excluir_funcionario(request, id):
    obj = get_object_or_404(Funcionario, id=id, empresa=request.user.empresa)
    if obj.funcionarioos_set.exists():
        messages.error(request, "Não é possível excluir este funcionário pois ele possui vinculo com Ordens de Serviço.")
    else:
        obj.delete()
        messages.success(request, "Funcionário excluído com sucesso.")
    return redirect('servicos:lista_funcionarios')


# ==========================================================
# 2. CRUD DE ORDENS DE SERVIÇO
# ==========================================================
@login_required
@permission_required_module('servicos')
def lista_ordens(request):
    q = request.GET.get('q', '')
    status_filtro = request.GET.get('status', '')
    periodo_inicio = request.GET.get('data_inicio', '')
    periodo_fim = request.GET.get('data_fim', '')

    ordens = OrdemServico.objects.filter(empresa=request.user.empresa).select_related('cadastro')

    if q:
        ordens = ordens.filter(
            Q(numero__icontains=q) |
            Q(cadastro__nome__icontains=q) |
            Q(descricao_geral__icontains=q)
        )
    if status_filtro:
        ordens = ordens.filter(status=status_filtro)
    if periodo_inicio:
        ordens = ordens.filter(data_entrada__gte=periodo_inicio)
    if periodo_fim:
        ordens = ordens.filter(data_entrada__lte=periodo_fim)

    # Resumo para os cards
    total_os = OrdemServico.objects.filter(empresa=request.user.empresa).count()
    abertas = OrdemServico.objects.filter(empresa=request.user.empresa, status='ABERTA').count()
    concluidas = OrdemServico.objects.filter(empresa=request.user.empresa, status='CONCLUIDA').count()
    fechadas_mes = OrdemServico.objects.filter(
        empresa=request.user.empresa, status='FECHADA',
        data_conclusao__month=date.today().month,
        data_conclusao__year=date.today().year,
    ).count()

    # Caixa padrão para modal rápido
    caixa_padrao_id = None
    try:
        param_caixa = ParametroSistema.objects.get(
            empresa=request.user.empresa, chave='CAIXA_PADRAO_ID'
        )
        caixa_padrao_id = int(param_caixa.valor)
    except (ParametroSistema.DoesNotExist, ValueError):
        pass

    return render(request, 'servicos/os_list.html', {
        'ordens': ordens,
        'q': q,
        'status_filtro': status_filtro,
        'periodo_inicio': periodo_inicio,
        'periodo_fim': periodo_fim,
        'total_os': total_os,
        'abertas': abertas,
        'concluidas': concluidas,
        'fechadas_mes': fechadas_mes,
        'formas_pagamento_rapido': FormaPagamento.objects.filter(empresa=request.user.empresa, ativo=True),
        'caixas_rapido': Caixa.objects.filter(empresa=request.user.empresa),
        'caixa_padrao_id_rapido': caixa_padrao_id,
    })


@login_required
@permission_required_module('servicos')
def nova_os(request):
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()
            messages.success(request, f"OS {obj.numero} criada com sucesso! Agora adicione os serviços.")
            return redirect('servicos:editar_os', id=obj.id)
    else:
        form = OrdemServicoForm(user=request.user, initial={
            'data_entrada': date.today(),
            'data_prevista': date.today(),
        })
    return render(request, 'servicos/os_form.html', {'form': form, 'editar': False})


@login_required
@permission_required_module('servicos')
def editar_os(request, id):
    obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "OS atualizada com sucesso!")
            return redirect('servicos:editar_os', id=obj.id)
    else:
        form = OrdemServicoForm(instance=obj, user=request.user)

    servicos = obj.servicos.all()
    funcionarios_os = obj.funcionarios.all().select_related('funcionario')
    form_servico = ServicoOSForm()
    form_funcionario = FuncionarioOSForm(empresa=request.user.empresa)
    valor_total = obj.valor_total
    remuneracao_total = obj.remuneracao_total
    diferenca = valor_total - remuneracao_total
    pode_concluir = servicos.exists() and obj.status == 'ABERTA'
    pode_fechar = (
        obj.status == 'CONCLUIDA' and
        servicos.exists() and
        funcionarios_os.exists() and
        diferenca == 0
    )
    caixas = Caixa.objects.filter(empresa=request.user.empresa) if pode_fechar else []
    caixa_padrao_id = None
    try:
        param_caixa = ParametroSistema.objects.get(
            empresa=request.user.empresa, chave='CAIXA_PADRAO_ID'
        )
        caixa_padrao_id = int(param_caixa.valor)
    except (ParametroSistema.DoesNotExist, ValueError):
        pass
    formas_pagamento = FormaPagamento.objects.filter(
        empresa=request.user.empresa, ativo=True
    ) if pode_fechar else []

    return render(request, 'servicos/os_form.html', {
        'form': form,
        'editar': True,
        'os': obj,
        'cadastro_nome': obj.cadastro.nome if obj.cadastro else '',
        'cadastro_doc': obj.cadastro.cpf_cnpj if obj.cadastro else '',
        'servicos': servicos,
        'funcionarios_os': funcionarios_os,
        'form_servico': form_servico,
        'form_funcionario': form_funcionario,
        'valor_total': valor_total,
        'remuneracao_total': remuneracao_total,
        'diferenca': diferenca,
        'pode_concluir': pode_concluir,
        'pode_fechar': pode_fechar,
        'caixas': caixas,
        'caixa_padrao_id': caixa_padrao_id,
        'formas_pagamento': formas_pagamento,
    })


@login_required
@permission_required_module('servicos')
def excluir_os(request, id):
    obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    if obj.status == 'FECHADA':
        messages.error(request, "Não é possível excluir uma OS já fechada.")
    else:
        obj.delete()
        messages.success(request, "OS excluída com sucesso.")
    return redirect('servicos:lista_ordens')


@login_required
@permission_required_module('servicos')
def salvar_os(request, id):
    """Salva os dados da OS diretamente da tela de detalhe"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)

    if request.method != 'POST':
        return redirect('servicos:editar_os', id=os_obj.id)

    if os_obj.status == 'FECHADA' or os_obj.status == 'CANCELADA':
        messages.error(request, "Não é possível editar uma OS fechada ou cancelada.")
        return redirect('servicos:editar_os', id=os_obj.id)

    cadastro_id = request.POST.get('cadastro_id')
    descricao_geral = request.POST.get('descricao_geral', '')
    data_entrada = request.POST.get('data_entrada')
    data_prevista = request.POST.get('data_prevista') or None
    observacoes = request.POST.get('observacoes', '')
    desconto = request.POST.get('desconto', '0')

    # Validação básica
    if not cadastro_id or not descricao_geral or not data_entrada:
        messages.error(request, "Cliente, Descrição e Data de Entrada são obrigatórios.")
        return redirect('servicos:editar_os', id=os_obj.id)

    from django.utils.dateparse import parse_date
    from decimal import Decimal, InvalidOperation
    try:
        os_obj.cadastro_id = int(cadastro_id)
        os_obj.descricao_geral = descricao_geral
        
        # Parse data_entrada - deve ser sempre fornecida
        parsed_entrada = parse_date(data_entrada)
        if not parsed_entrada:
            raise ValueError("Formato de data_entrada inválido")
        os_obj.data_entrada = parsed_entrada
        
        # Parse data_prevista - opcional
        if data_prevista:
            parsed_prevista = parse_date(data_prevista)
            if parsed_prevista:
                os_obj.data_prevista = parsed_prevista
        else:
            os_obj.data_prevista = None
            
        os_obj.observacoes = observacoes
        
        # Parse desconto como Decimal
        try:
            os_obj.desconto = Decimal(desconto)
        except (InvalidOperation, TypeError):
            os_obj.desconto = Decimal('0')
        
        os_obj.save()

        messages.success(request, f"OS {os_obj.numero} salva com sucesso!")
    except (ValueError, TypeError) as e:
        messages.error(request, f"Erro ao salvar: {str(e)}")
    
    return redirect('servicos:editar_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def detalhe_os(request, id):
    """Tela principal da OS — exibe serviços, funcionários e permite ações"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    servicos = os_obj.servicos.all()
    funcionarios_os = os_obj.funcionarios.all().select_related('funcionario')

    form_servico = ServicoOSForm()
    form_funcionario = FuncionarioOSForm(empresa=request.user.empresa)

    valor_total = os_obj.valor_total
    remuneracao_total = os_obj.remuneracao_total
    diferenca = valor_total - remuneracao_total

    # Verificar se pode concluir (pelo menos 1 serviço)
    pode_concluir = servicos.exists() and os_obj.status == 'ABERTA'
    pode_fechar = (
        os_obj.status == 'CONCLUIDA' and
        servicos.exists() and
        funcionarios_os.exists() and
        diferenca == 0
    )

    # Caixas disponíveis para o modal de fechamento
    caixas = Caixa.objects.filter(empresa=request.user.empresa) if pode_fechar else []

    # Buscar caixa padrão dos parâmetros
    caixa_padrao_id = None
    try:
        param_caixa = ParametroSistema.objects.get(
            empresa=request.user.empresa, chave='CAIXA_PADRAO_ID'
        )
        caixa_padrao_id = int(param_caixa.valor)
    except (ParametroSistema.DoesNotExist, ValueError):
        pass

    # Formas de pagamento ativas
    formas_pagamento = FormaPagamento.objects.filter(
        empresa=request.user.empresa, ativo=True
    ) if pode_fechar else []

    # Clientes para o select de edição inline
    from cadastros.models import Cadastro
    clientes = Cadastro.objects.filter(
        empresa=request.user.empresa
    ).filter(Q(papel='CLI') | Q(papel='AMB')).order_by('nome')

    return render(request, 'servicos/os_detalhe.html', {
        'os': os_obj,
        'servicos': servicos,
        'funcionarios_os': funcionarios_os,
        'form_servico': form_servico,
        'form_funcionario': form_funcionario,
        'valor_total': valor_total,
        'remuneracao_total': remuneracao_total,
        'diferenca': diferenca,
        'pode_concluir': pode_concluir,
        'pode_fechar': pode_fechar,
        'caixas': caixas,
        'caixa_padrao_id': caixa_padrao_id,
        'formas_pagamento': formas_pagamento,
        'clientes': clientes,
    })


# ==========================================================
# 3. AÇÕES INLINE NA OS (Serviços e Funcionários)
# ==========================================================
@login_required
@permission_required_module('servicos')
def adicionar_servico_os(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id, empresa=request.user.empresa)
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível adicionar serviços nesta OS.")
        return redirect('servicos:editar_os', id=os_obj.id)

    if request.method == 'POST':
        form = ServicoOSForm(request.POST)
        if form.is_valid():
            servico = form.save(commit=False)
            servico.ordem_servico = os_obj
            servico.save()
            messages.success(request, "Serviço adicionado com sucesso!")
    return redirect('servicos:editar_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def editar_servico_os(request, id):
    servico = get_object_or_404(ServicoOS, id=id, ordem_servico__empresa=request.user.empresa)
    os_obj = servico.ordem_servico
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível editar serviços nesta OS.")
        return redirect('servicos:editar_os', id=os_obj.id)

    if request.method == 'POST':
        form = ServicoOSForm(request.POST, instance=servico)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço atualizado!")
    return redirect('servicos:editar_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def excluir_servico_os(request, id):
    servico = get_object_or_404(ServicoOS, id=id, ordem_servico__empresa=request.user.empresa)
    os_obj = servico.ordem_servico
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível remover serviços desta OS.")
        return redirect('servicos:editar_os', id=os_obj.id)

    servico.delete()
    messages.success(request, "Serviço removido.")
    return redirect('servicos:editar_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def adicionar_funcionario_os(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id, empresa=request.user.empresa)
    if os_obj.status not in ('ABERTA', 'CONCLUIDA', 'FECHADA'):
        messages.error(request, "Não é possível adicionar funcionários nesta OS.")
        return redirect('servicos:editar_os', id=os_obj.id)

    if request.method == 'POST':
        form = FuncionarioOSForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            funcionario = form.cleaned_data['funcionario']
            if FuncionarioOS.objects.filter(ordem_servico=os_obj, funcionario=funcionario).exists():
                messages.error(request, f'O funcionário "{funcionario.nome}" já está vinculado a esta OS.')
            else:
                func_os = form.save(commit=False)
                func_os.ordem_servico = os_obj
                func_os.save()
                messages.success(request, "Funcionário adicionado à OS!")
    return redirect('servicos:editar_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def editar_funcionario_os(request, id):
    func_os = get_object_or_404(FuncionarioOS, id=id, ordem_servico__empresa=request.user.empresa)
    os_obj = func_os.ordem_servico
    if os_obj.status not in ('ABERTA', 'CONCLUIDA', 'FECHADA'):
        messages.error(request, "Não é possível editar funcionários nesta OS.")
        return redirect('servicos:editar_os', id=os_obj.id)

    if request.method == 'POST':
        form = FuncionarioOSForm(request.POST, instance=func_os, empresa=request.user.empresa)
        if form.is_valid():
            funcionario = form.cleaned_data['funcionario']
            if FuncionarioOS.objects.filter(ordem_servico=os_obj, funcionario=funcionario).exclude(id=func_os.id).exists():
                messages.error(request, f'O funcionário "{funcionario.nome}" já está vinculado a esta OS.')
            else:
                form.save()
                messages.success(request, "Participação atualizada!")
    return redirect('servicos:editar_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def excluir_funcionario_os(request, id):
    func_os = get_object_or_404(FuncionarioOS, id=id, ordem_servico__empresa=request.user.empresa)
    os_obj = func_os.ordem_servico
    if os_obj.status not in ('ABERTA', 'CONCLUIDA', 'FECHADA'):
        messages.error(request, "Não é possível remover funcionários desta OS.")
        return redirect('servicos:editar_os', id=os_obj.id)

    func_os.delete()
    messages.success(request, "Funcionário removido da OS.")
    return redirect('servicos:editar_os', id=os_obj.id)


# ==========================================================
# 4. WORKFLOW DE STATUS
# ==========================================================
@login_required
@permission_required_module('servicos')
def concluir_os(request, id):
    """Marca OS como CONCLUIDA"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    if request.method != 'POST':
        return redirect('servicos:editar_os', id=os_obj.id)

    if os_obj.status != 'ABERTA':
        messages.error(request, "Somente OS em aberto podem ser concluídas.")
        return redirect('servicos:editar_os', id=os_obj.id)

    if not os_obj.servicos.exists():
        messages.error(request, "Adicione pelo menos um serviço antes de concluir.")
        return redirect('servicos:editar_os', id=os_obj.id)

    os_obj.status = 'CONCLUIDA'
    os_obj.data_conclusao = date.today()
    os_obj.save()
    messages.success(request, f"OS {os_obj.numero} marcada como CONCLUÍDA! Agora o financeiro pode fechar.")
    return redirect('servicos:editar_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def cancelar_os(request, id):
    """Cancela uma OS"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    if request.method != 'POST':
        return redirect('servicos:editar_os', id=os_obj.id)

    if os_obj.status == 'FECHADA':
        messages.error(request, "Não é possível cancelar uma OS já fechada.")
        return redirect('servicos:editar_os', id=os_obj.id)

    os_obj.status = 'CANCELADA'
    os_obj.save()
    messages.warning(request, f"OS {os_obj.numero} CANCELADA.")
    return redirect('servicos:editar_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def fechar_os(request, id):
    """Fecha a OS e gera o financeiro (Contas a Receber ou Baixa no Caixa)"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)

    if request.method != 'POST':
        return redirect('servicos:editar_os', id=os_obj.id)

    if os_obj.status != 'CONCLUIDA':
        messages.error(request, "Somente OS CONCLUÍDAS podem ser fechadas.")
        return redirect('servicos:editar_os', id=os_obj.id)

    # Validações
    valor_total = os_obj.valor_total
    remuneracao_total = os_obj.remuneracao_total

    if valor_total == 0:
        messages.error(request, "A OS não possui serviços com valor. Adicione serviços antes de fechar.")
        return redirect('servicos:editar_os', id=os_obj.id)

    if remuneracao_total != valor_total:
        messages.error(
            request,
            f"A remuneração (R$ {remuneracao_total:.2f}) não confere com o valor total (R$ {valor_total:.2f}). "
            f"Ajuste antes de fechar."
        )
        return redirect('servicos:editar_os', id=os_obj.id)

    forma = request.POST.get('forma_pagamento', 'A_VISTA')
    qtd_parcelas = int(request.POST.get('qtd_parcelas', 1))
    desconto_text = request.POST.get('desconto', '0').replace('R$', '').replace(' ', '').strip()
    if ',' in desconto_text and '.' in desconto_text:
        if desconto_text.rfind(',') > desconto_text.rfind('.'):
            desconto_text = desconto_text.replace('.', '').replace(',', '.')
        else:
            desconto_text = desconto_text.replace(',', '')
    elif ',' in desconto_text:
        desconto_text = desconto_text.replace(',', '.')
    desconto = Decimal(desconto_text or '0')

    def _parse_decimal(valor):
        if valor is None:
            return Decimal('0')
        texto = str(valor).strip()
        if not texto:
            return Decimal('0')
        texto = texto.replace('R$', '').replace(' ', '')
        if ',' in texto and '.' in texto:
            if texto.rfind(',') > texto.rfind('.'):
                texto = texto.replace('.', '').replace(',', '.')
            else:
                texto = texto.replace(',', '')
        elif ',' in texto:
            texto = texto.replace(',', '.')
        return Decimal(texto)

    pagamentos = []
    forma_pagamento_ids = request.POST.getlist('pagamento_forma_id[]') or request.POST.getlist('pagamento_forma_id')
    valores_pagamento = request.POST.getlist('pagamento_valor[]') or request.POST.getlist('pagamento_valor')
    caixas_pagamento = request.POST.getlist('pagamento_caixa_id[]') or request.POST.getlist('pagamento_caixa_id')

    linhas_pagamento = []
    max_len = max(len(forma_pagamento_ids), len(valores_pagamento), len(caixas_pagamento))
    for idx in range(max_len):
        forma_id = forma_pagamento_ids[idx] if idx < len(forma_pagamento_ids) else ''
        valor_text = valores_pagamento[idx] if idx < len(valores_pagamento) else ''
        caixa_id = caixas_pagamento[idx] if idx < len(caixas_pagamento) else ''

        if not str(forma_id).strip() and not str(valor_text).strip() and not str(caixa_id).strip():
            continue

        linhas_pagamento.append({
            'forma_id': forma_id,
            'valor_text': valor_text,
            'caixa_id': caixa_id,
        })

    if forma == 'A_PRAZO':
        pagamentos = []
    elif linhas_pagamento:
        for idx, linha in enumerate(linhas_pagamento):
            forma_id = linha['forma_id']
            if not forma_id:
                messages.error(request, "Selecione uma forma de pagamento para cada linha informada.")
                return redirect('servicos:editar_os', id=os_obj.id)
            try:
                forma_pagamento_obj = FormaPagamento.objects.get(id=int(forma_id), empresa=request.user.empresa)
            except (FormaPagamento.DoesNotExist, ValueError):
                messages.error(request, f"Forma de pagamento inválida na linha {idx + 1}.")
                return redirect('servicos:editar_os', id=os_obj.id)

            valor = _parse_decimal(linha['valor_text'])
            if valor <= 0:
                messages.error(request, f"Informe um valor maior que zero para a forma {forma_pagamento_obj.nome}.")
                return redirect('servicos:editar_os', id=os_obj.id)

            caixa_id = linha['caixa_id'] or None
            pagamentos.append({
                'forma_pagamento_obj': forma_pagamento_obj,
                'valor': valor,
                'caixa_id': caixa_id,
            })

        total_split = sum((p['valor'] for p in pagamentos), Decimal('0'))
        if total_split.quantize(Decimal('0.01')) != valor_total.quantize(Decimal('0.01')):
            messages.error(request, f"A soma das formas de pagamento ({total_split:.2f}) não bate com o valor total da OS ({valor_total:.2f}).")
            return redirect('servicos:editar_os', id=os_obj.id)
    else:
        forma_pagamento_id = request.POST.get('forma_pagamento_id', None)
        caixa_id = request.POST.get('caixa_id', None)
        forma_pagamento_obj = None
        if forma_pagamento_id:
            try:
                forma_pagamento_obj = FormaPagamento.objects.get(
                    id=int(forma_pagamento_id), empresa=request.user.empresa
                )
            except (FormaPagamento.DoesNotExist, ValueError):
                pass
        pagamentos.append({
            'forma_pagamento_obj': forma_pagamento_obj,
            'valor': valor_total,
            'caixa_id': caixa_id,
        })

    # Aplicar desconto
    if desconto > 0:
        if desconto > valor_total:
            messages.error(request, f"O desconto (R$ {desconto:.2f}) não pode ser maior que o valor total (R$ {valor_total:.2f}).")
            return redirect('servicos:editar_os', id=os_obj.id)
        os_obj.desconto = desconto
        os_obj.save(update_fields=['desconto'])
        valor_total = os_obj.valor_total  # Recalcular com desconto

    if forma == 'A_PRAZO' and qtd_parcelas < 1:
        messages.error(request, "Para pagamento a prazo, informe pelo menos 1 parcela.")
        return redirect('servicos:editar_os', id=os_obj.id)

    # Buscar Plano de Contas padrão para serviços
    try:
        param_plano = ParametroSistema.objects.get(
            empresa=request.user.empresa, chave='PLANO_CONTAS_SERVICOS_ID'
        )
        plano_de_contas = PlanoDeContas.objects.get(
            id=int(param_plano.valor), empresa=request.user.empresa
        )
    except (ParametroSistema.DoesNotExist, PlanoDeContas.DoesNotExist, ValueError):
        messages.error(
            request,
            "Configure o Plano de Contas padrão para Serviços em Configurações > Parâmetros do Sistema "
            "(chave: PLANO_CONTAS_SERVICOS_ID)."
        )
        return redirect('servicos:editar_os', id=os_obj.id)

    # Ajustar data_conclusao: se conclusão no mês seguinte ao de entrada, usar último dia do mês de entrada
    hoje = date.today()
    data_entrada = os_obj.data_entrada
    if hoje.month != data_entrada.month or hoje.year != data_entrada.year:
        # Conclusão em mês diferente da entrada - usar último dia do mês de entrada
        import calendar
        ultimo_dia = calendar.monthrange(data_entrada.year, data_entrada.month)[1]
        data_conclusao_ref = date(data_entrada.year, data_entrada.month, ultimo_dia)
    else:
        data_conclusao_ref = hoje

    # Atualizar data de conclusão
    os_obj.data_conclusao = data_conclusao_ref
    os_obj.save(update_fields=['data_conclusao'])

    # Gerar financeiro
    if forma == 'A_VISTA':
        with transaction.atomic():
            for index, pagamento in enumerate(pagamentos, start=1):
                forma_pagamento_obj = pagamento['forma_pagamento_obj']
                valor_parcela = pagamento['valor']
                caixa_id = pagamento['caixa_id']

                if forma_pagamento_obj and forma_pagamento_obj.afeta_caixa:
                    if caixa_id:
                        caixa = get_object_or_404(Caixa, id=caixa_id, empresa=request.user.empresa)
                    else:
                        caixa = Caixa.objects.filter(empresa=request.user.empresa).first()
                        if not caixa:
                            messages.error(request, "Nenhum caixa/banco encontrado. Cadastre um em Financeiro > Caixas.")
                            return redirect('servicos:editar_os', id=os_obj.id)

                    Lancamento.objects.create(
                        empresa=request.user.empresa,
                        caixa=caixa,
                        plano_de_contas=plano_de_contas,
                        forma_pagamento=forma_pagamento_obj,
                        data_lancamento=date.today(),
                        descricao=f"Recebimento OS {os_obj.numero} — {os_obj.descricao_geral[:100]} — {forma_pagamento_obj.nome}",
                        valor=valor_parcela,
                        tipo='C',
                    )

            if len(pagamentos) == 1:
                nome_forma = pagamentos[0]['forma_pagamento_obj'].nome if pagamentos[0]['forma_pagamento_obj'] else 'A Vista'
                messages.success(request, f"OS {os_obj.numero} FECHADA! Pagamento via {nome_forma} registrado no caixa.")
            else:
                nomes = ', '.join(
                    p['forma_pagamento_obj'].nome if p['forma_pagamento_obj'] else 'Sem forma' for p in pagamentos
                )
                messages.success(request, f"OS {os_obj.numero} FECHADA! {len(pagamentos)} forma(s) de pagamento registradas no caixa: {nomes}.")

    elif forma == 'A_PRAZO':
        # Gera N Contas pendentes
        valor_parcela = valor_total / qtd_parcelas
        for i in range(1, qtd_parcelas + 1):
            from financeiro.views import add_months
            vencimento = add_months(os_obj.data_entrada, i)
            Conta.objects.create(
                empresa=request.user.empresa,
                descricao=f"OS {os_obj.numero} — Parcela {i}/{qtd_parcelas}",
                plano_de_contas=plano_de_contas,
                cadastro=os_obj.cadastro,
                valor=valor_parcela,
                data_vencimento=vencimento,
                status='PENDENTE',
                documento=f"{os_obj.numero}-{i}/{qtd_parcelas}",
            )
        messages.success(
            request,
            f"OS {os_obj.numero} FECHADA! {qtd_parcelas} parcela(s) gerada(s) no Contas a Receber."
        )

    # Atualizar status da OS
    os_obj.status = 'FECHADA'
    os_obj.forma_pagamento = forma
    os_obj.qtd_parcelas = qtd_parcelas
    os_obj.save()

    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('servicos:imprimir_os', id=os_obj.id)


@login_required
@permission_required_module('servicos')
def desfechar_os(request, id):
    """Estorna o fechamento de uma OS: remove contas e lançamentos vinculados, volta status para CONCLUIDA"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)

    if request.method != 'POST':
        return redirect('servicos:editar_os', id=os_obj.id)

    if os_obj.status != 'FECHADA':
        messages.error(request, "Somente OS FECHADAS podem ter o fechamento estornado.")
        return redirect('servicos:editar_os', id=os_obj.id)

    with transaction.atomic():
        # 1. Deletar contas vinculadas (A_PRAZO ou A_VISTA legado)
        contas_vinculadas = Conta.objects.filter(
            empresa=request.user.empresa,
            descricao__icontains=f"OS {os_obj.numero}"
        )

        if contas_vinculadas.exists():
            contas_pagas = contas_vinculadas.filter(status__in=['PAGA', 'PARCIAL'])
            if contas_pagas.exists():
                nomes = ', '.join(c.descricao[:50] for c in contas_pagas)
                messages.error(
                    request,
                    f"Não é possível estornar. As seguintes contas já foram baixadas: {nomes}. "
                    f"Exclua as baixas primeiro no Financeiro > Fluxo de Caixa."
                )
                return redirect('servicos:editar_os', id=os_obj.id)

            Lancamento.objects.filter(conta_origem__in=contas_vinculadas).delete()
            contas_vinculadas.delete()

        # 2. Deletar lançamentos diretos do caixa (A_VISTA sem Conta)
        Lancamento.objects.filter(
            empresa=request.user.empresa,
            descricao__icontains=f"Recebimento OS {os_obj.numero}"
        ).delete()

    # Reverter desconto se foi aplicado
    if os_obj.desconto and os_obj.desconto > 0:
        os_obj.desconto = Decimal('0')

    # Voltar status para CONCLUIDA e limpar dados de fechamento
    os_obj.status = 'CONCLUIDA'
    os_obj.forma_pagamento = ''
    os_obj.qtd_parcelas = 0
    os_obj.data_conclusao = None
    os_obj.save()

    messages.success(request, f"OS {os_obj.numero} - Fechamento ESTORNADO com sucesso! Agora pode ser fechada novamente.")
    return redirect('servicos:editar_os', id=os_obj.id)


# ==========================================================
# 5. CRUD DE METAS
# ==========================================================
@login_required
@permission_required_module('servicos')
def lista_metas(request):
    mes_atual = int(request.GET.get('mes', date.today().month))
    ano_atual = int(request.GET.get('ano', date.today().year))

    metas = MetaFuncionario.objects.filter(
        empresa=request.user.empresa, mes=mes_atual, ano=ano_atual
    ).select_related('funcionario')

    # Calcular realizado para cada meta
    dados_metas = []
    for meta in metas:
        realizado = FuncionarioOS.objects.filter(
            funcionario=meta.funcionario,
            ordem_servico__status='FECHADA',
            ordem_servico__data_conclusao__month=mes_atual,
            ordem_servico__data_conclusao__year=ano_atual,
            ordem_servico__empresa=request.user.empresa,
        ).aggregate(total=Sum('valor_remuneracao'))['total'] or 0

        percentual = (realizado / meta.meta_valor * 100) if meta.meta_valor > 0 else 0
        avaliacao = meta.calcular_avaliacao(realizado)

        dados_metas.append({
            'meta': meta,
            'realizado': realizado,
            'percentual': percentual,
            'avaliacao': avaliacao,
        })

    return render(request, 'servicos/meta_list.html', {
        'dados_metas': dados_metas,
        'mes_atual': mes_atual,
        'ano_atual': ano_atual,
    })


@login_required
@permission_required_module('servicos')
def nova_meta(request):
    if request.method == 'POST':
        form = MetaFuncionarioForm(request.POST, user=request.user)
        if form.is_valid():
            funcionario = form.cleaned_data['funcionario']
            mes = form.cleaned_data['mes']
            ano = form.cleaned_data['ano']
            # Verificar duplicidade
            if MetaFuncionario.objects.filter(
                empresa=request.user.empresa,
                funcionario=funcionario,
                mes=mes,
                ano=ano
            ).exists():
                messages.error(
                    request,
                    f"Já existe uma meta para {funcionario.nome} em {mes}/{ano}. "
                    f"Edite a meta existente ou exclua antes de criar uma nova."
                )
            else:
                obj = form.save(commit=False)
                obj.empresa = request.user.empresa
                obj.save()
                messages.success(request, "Meta cadastrada com sucesso!")
                return redirect('servicos:lista_metas')
    else:
        form = MetaFuncionarioForm(user=request.user, initial={
            'mes': date.today().month,
            'ano': date.today().year,
        })
    return render(request, 'servicos/meta_form.html', {'form': form, 'editar': False})


@login_required
@permission_required_module('servicos')
def editar_meta(request, id):
    obj = get_object_or_404(MetaFuncionario, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = MetaFuncionarioForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            funcionario = form.cleaned_data['funcionario']
            mes = form.cleaned_data['mes']
            ano = form.cleaned_data['ano']
            if MetaFuncionario.objects.filter(
                empresa=request.user.empresa, funcionario=funcionario, mes=mes, ano=ano
            ).exclude(id=obj.id).exists():
                messages.error(request, f'Já existe uma meta para o funcionário "{funcionario.nome}" no período {mes}/{ano}.')
            else:
                form.save()
                messages.success(request, "Meta atualizada com sucesso!")
                return redirect('servicos:lista_metas')
    else:
        form = MetaFuncionarioForm(instance=obj, user=request.user)
    return render(request, 'servicos/meta_form.html', {'form': form, 'editar': True})


@login_required
@permission_required_module('servicos')
def excluir_meta(request, id):
    obj = get_object_or_404(MetaFuncionario, id=id, empresa=request.user.empresa)
    obj.delete()
    messages.success(request, "Meta excluída com sucesso.")
    return redirect('servicos:lista_metas')


# ==========================================================
# 6. RELATÓRIOS
# ==========================================================
@login_required
@permission_required_module('servicos')
def relatorio_mensal(request, ano, mes):
    """Relatório mensal: meta vs realizado por funcionário com bônus"""
    funcionarios = Funcionario.objects.filter(empresa=request.user.empresa, ativo=True)
    dados = []
    total_bonus = 0

    for func in funcionarios:
        meta_obj = MetaFuncionario.objects.filter(
            funcionario=func, mes=mes, ano=ano, empresa=request.user.empresa
        ).first()

        realizado = FuncionarioOS.objects.filter(
            funcionario=func,
            ordem_servico__status='FECHADA',
            ordem_servico__data_conclusao__month=mes,
            ordem_servico__data_conclusao__year=ano,
            ordem_servico__empresa=request.user.empresa,
        ).aggregate(total=Sum('valor_remuneracao'))['total'] or 0

        meta_valor = meta_obj.meta_valor if meta_obj else 0
        if meta_obj:
            resultado = meta_obj.calcular_avaliacao(realizado)
            percentual = resultado['percentual']
            avaliacao = resultado['classificacao']
            bonus = resultado['bonus']
        else:
            percentual = 0
            avaliacao = 'SEM_META'
            bonus = 0

        total_bonus += bonus

        dados.append({
            'funcionario': func,
            'meta_valor': meta_valor,
            'realizado': realizado,
            'percentual': percentual,
            'avaliacao': avaliacao,
            'bonus': bonus,
        })

    # Dados para gráfico
    labels = [d['funcionario'].nome for d in dados]
    metas_data = [float(d['meta_valor']) for d in dados]
    realizado_data = [float(d['realizado']) for d in dados]

    # Resumo empresa
    meta_empresa = sum(d['meta_valor'] for d in dados)
    realizado_empresa = sum(d['realizado'] for d in dados)

    return render(request, 'servicos/relatorio_mensal.html', {
        'dados': dados,
        'ano': ano,
        'mes': mes,
        'labels': labels,
        'metas_data': metas_data,
        'realizado_data': realizado_data,
        'meta_empresa': meta_empresa,
        'realizado_empresa': realizado_empresa,
        'total_bonus': total_bonus,
    })


@login_required
@permission_required_module('servicos')
def relatorio_anual(request, ano):
    """Relatório anual: evolução mês a mês da empresa"""
    meses_nomes = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    dados_meses = []
    for mes in range(1, 13):
        # Meta total da empresa no mês
        meta_mes = MetaFuncionario.objects.filter(
            empresa=request.user.empresa, mes=mes, ano=ano
        ).aggregate(total=Sum('meta_valor'))['total'] or 0

        # Realizado total da empresa no mês
        realizado_mes = FuncionarioOS.objects.filter(
            ordem_servico__status='FECHADA',
            ordem_servico__data_conclusao__month=mes,
            ordem_servico__data_conclusao__year=ano,
            ordem_servico__empresa=request.user.empresa,
        ).aggregate(total=Sum('valor_remuneracao'))['total'] or 0

        dados_meses.append({
            'mes': mes,
            'nome': meses_nomes[mes - 1],
            'meta': meta_mes,
            'realizado': realizado_mes,
        })

    # Dados para gráfico
    labels = [d['nome'] for d in dados_meses]
    metas_data = [float(d['meta']) for d in dados_meses]
    realizado_data = [float(d['realizado']) for d in dados_meses]

    # Totais anuais
    meta_anual = sum(d['meta'] for d in dados_meses)
    realizado_anual = sum(d['realizado'] for d in dados_meses)

    return render(request, 'servicos/relatorio_anual.html', {
        'dados_meses': dados_meses,
        'ano': ano,
        'labels': labels,
        'metas_data': metas_data,
        'realizado_data': realizado_data,
        'meta_anual': meta_anual,
        'realizado_anual': realizado_anual,
    })


@login_required
@permission_required_module('servicos')
def imprimir_os(request, id):
    """Gera impressão da OS com dados do cliente, serviços e pagamento"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    servicos = os_obj.servicos.all()
    funcionarios = os_obj.funcionarios.all()
    valor_bruto = os_obj.valor_bruto
    valor_total = os_obj.valor_total
    valor_parcela = valor_total / os_obj.qtd_parcelas if os_obj.qtd_parcelas else valor_total

    historico_pagamentos = Lancamento.objects.filter(
        empresa=request.user.empresa
    ).filter(
        Q(conta_origem__documento__startswith=os_obj.numero) |
        Q(descricao__icontains=f'OS {os_obj.numero}')
    ).select_related('caixa', 'conta_origem').order_by('data_lancamento', 'id')

    parcelas = Conta.objects.filter(
        empresa=request.user.empresa,
        descricao__icontains=f'OS {os_obj.numero}'
    ).order_by('data_vencimento')

    return render(request, 'servicos/os_impressao.html', {
        'os': os_obj,
        'servicos': servicos,
        'funcionarios': funcionarios,
        'valor_bruto': valor_bruto,
        'valor_total': valor_total,
        'valor_parcela': valor_parcela,
        'historico_pagamentos': historico_pagamentos,
        'parcelas': parcelas,
    })


# ==========================================================
# 9. CRUD DE ORÇAMENTOS
# ==========================================================
@login_required
@permission_required_module('servicos')
def lista_orcamentos(request):
    q = request.GET.get('q', '')
    orcamentos = Orcamento.objects.filter(empresa=request.user.empresa)
    if q:
        orcamentos = orcamentos.filter(
            Q(numero__icontains=q) | Q(cadastro__nome__icontains=q)
        )
    orcamentos = orcamentos[:50]

    return render(request, 'servicos/orcamento_list.html', {
        'orcamentos': orcamentos,
        'q': q,
    })


@login_required
@permission_required_module('servicos')
def novo_orcamento(request):
    if request.method == 'POST':
        form = OrcamentoForm(request.POST, user=request.user)
        if form.is_valid():
            orcamento = form.save(commit=False)
            orcamento.empresa = request.user.empresa
            orcamento.save()
            messages.success(request, f'Orçamento {orcamento.numero} criado com sucesso!')
            return redirect('servicos:detalhe_orcamento', id=orcamento.id)
    else:
        from datetime import date as _date
        form = OrcamentoForm(user=request.user, initial={'data': _date.today()})
    return render(request, 'servicos/orcamento_form.html', {'form': form, 'titulo': 'Novo Orçamento'})


@login_required
@permission_required_module('servicos')
def editar_orcamento(request, id):
    orcamento = get_object_or_404(Orcamento, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = OrcamentoForm(request.POST, instance=orcamento, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Orçamento {orcamento.numero} atualizado com sucesso!')
            return redirect('servicos:detalhe_orcamento', id=orcamento.id)
    else:
        form = OrcamentoForm(instance=orcamento, user=request.user)
    return render(request, 'servicos/orcamento_form.html', {
        'form': form,
        'titulo': f'Editar {orcamento.numero}',
        'orcamento': orcamento,
        'cadastro_nome': orcamento.cadastro.nome if orcamento.cadastro else '',
        'cadastro_doc': orcamento.cadastro.cpf_cnpj if orcamento.cadastro else '',
    })


@login_required
@permission_required_module('servicos')
def detalhe_orcamento(request, id):
    orcamento = get_object_or_404(Orcamento, id=id, empresa=request.user.empresa)
    servicos = orcamento.servicos.all()
    valor_total = orcamento.valor_total
    return render(request, 'servicos/orcamento_detalhe.html', {
        'orcamento': orcamento,
        'servicos': servicos,
        'valor_total': valor_total,
    })


@login_required
@permission_required_module('servicos')
def excluir_orcamento(request, id):
    orcamento = get_object_or_404(Orcamento, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        numero = orcamento.numero
        orcamento.delete()
        messages.success(request, f'Orçamento {numero} excluído com sucesso!')
        return redirect('servicos:lista_orcamentos')
    return redirect('servicos:detalhe_orcamento', id=id)


@login_required
@permission_required_module('servicos')
def adicionar_servico_orcamento(request, os_id):
    """Adiciona serviço via AJAX"""
    orcamento = get_object_or_404(Orcamento, id=os_id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = ServicoOrcamentoForm(request.POST)
        if form.is_valid():
            servico = form.save(commit=False)
            servico.orcamento = orcamento
            servico.save()
            return JsonResponse({
                'sucesso': True,
                'id': servico.id,
                'descricao': servico.descricao,
                'valor': float(servico.valor),
                'valor_total': float(orcamento.valor_total),
            })
    return JsonResponse({'sucesso': False, 'erro': 'Dados inválidos'}, status=400)


@login_required
@permission_required_module('servicos')
def editar_servico_orcamento(request, id):
    """Edita serviço via AJAX"""
    servico = get_object_or_404(ServicoOrcamento, id=id, orcamento__empresa=request.user.empresa)
    if request.method == 'POST':
        form = ServicoOrcamentoForm(request.POST, instance=servico)
        if form.is_valid():
            form.save()
            orcamento = servico.orcamento
            return JsonResponse({
                'sucesso': True,
                'descricao': servico.descricao,
                'valor': float(servico.valor),
                'valor_total': float(orcamento.valor_total),
            })
    return JsonResponse({'sucesso': False, 'erro': 'Dados inválidos'}, status=400)


@login_required
@permission_required_module('servicos')
def excluir_servico_orcamento(request, id):
    """Exclui serviço via AJAX"""
    servico = get_object_or_404(ServicoOrcamento, id=id, orcamento__empresa=request.user.empresa)
    if request.method == 'POST':
        orcamento = servico.orcamento
        servico.delete()
        return JsonResponse({
            'sucesso': True,
            'valor_total': float(orcamento.valor_total),
        })
    return JsonResponse({'sucesso': False, 'erro': 'Método não permitido'}, status=400)


@login_required
@permission_required_module('servicos')
def imprimir_orcamento(request, id):
    """Gera impressão do Orçamento"""
    orcamento = get_object_or_404(Orcamento, id=id, empresa=request.user.empresa)
    servicos = orcamento.servicos.all()
    valor_total = orcamento.valor_total

    return render(request, 'servicos/orcamento_impressao.html', {
        'orcamento': orcamento,
        'servicos': servicos,
        'valor_total': valor_total,
    })


# ==========================================================
# 10. CRUD DE FORMAS DE PAGAMENTO
# ==========================================================
@login_required
@permission_required_module('servicos')
def lista_formas_pagamento(request):
    formas = FormaPagamento.objects.filter(empresa=request.user.empresa)
    return render(request, 'servicos/formapagamento_list.html', {'formas': formas})


@login_required
@permission_required_module('servicos')
def nova_forma_pagamento(request):
    if request.method == 'POST':
        form = FormaPagamentoForm(request.POST)
        if form.is_valid():
            nome = form.cleaned_data['nome'].strip()
            if FormaPagamento.objects.filter(empresa=request.user.empresa, nome__iexact=nome).exists():
                messages.error(request, f'Já existe uma forma de pagamento "{nome}" cadastrada para esta empresa.')
            else:
                fp = form.save(commit=False)
                fp.empresa = request.user.empresa
                fp.save()
                messages.success(request, f'Forma de pagamento "{fp.nome}" criada com sucesso!')
                return redirect('servicos:lista_formas_pagamento')
    else:
        form = FormaPagamentoForm()
    return render(request, 'servicos/formapagamento_form.html', {'form': form, 'titulo': 'Nova Forma de Pagamento'})


@login_required
@permission_required_module('servicos')
def editar_forma_pagamento(request, id):
    fp = get_object_or_404(FormaPagamento, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = FormaPagamentoForm(request.POST, instance=fp)
        if form.is_valid():
            nome = form.cleaned_data['nome'].strip()
            if FormaPagamento.objects.filter(empresa=request.user.empresa, nome__iexact=nome).exclude(id=fp.id).exists():
                messages.error(request, f'Já existe uma forma de pagamento "{nome}" cadastrada para esta empresa.')
            else:
                form.save()
                messages.success(request, f'Forma de pagamento "{fp.nome}" atualizada com sucesso!')
                return redirect('servicos:lista_formas_pagamento')
    else:
        form = FormaPagamentoForm(instance=fp)
    return render(request, 'servicos/formapagamento_form.html', {
        'form': form, 'titulo': f'Editar {fp.nome}', 'forma': fp
    })


@login_required
@permission_required_module('servicos')
def excluir_forma_pagamento(request, id):
    fp = get_object_or_404(FormaPagamento, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        nome = fp.nome
        fp.delete()
        messages.success(request, f'Forma de pagamento "{nome}" excluída com sucesso!')
        return redirect('servicos:lista_formas_pagamento')
    return redirect('servicos:lista_formas_pagamento')


# ==========================================================
# 11. API BUSCA DE CLIENTES (AJAX)
# ==========================================================
@login_required
@permission_required_module('servicos')
def buscar_clientes(request):
    """Busca clientes por nome, CPF/CNPJ ou telefone — retorna JSON"""
    q = request.GET.get('q', '').strip()
    cliente_id = request.GET.get('id', None)

    # Busca por ID (para campos com valor prévio)
    if cliente_id:
        try:
            c = Cadastro.objects.get(id=int(cliente_id), empresa=request.user.empresa)
            return JsonResponse({'resultados': [{
                'id': c.id,
                'nome': c.nome,
                'documento': c.cpf_cnpj or '',
                'telefone': c.celular or c.telefone_fixo or '',
                'cidade': f'{c.cidade}/{c.uf}' if c.cidade else '',
            }]})
        except (Cadastro.DoesNotExist, ValueError):
            return JsonResponse({'resultados': []})

    if len(q) < 2:
        return JsonResponse({'resultados': []})

    clientes = Cadastro.objects.filter(
        empresa=request.user.empresa,
        papel__in=['CLI', 'AMB'],
        situacao='ATIVO',
    ).filter(
        Q(nome__icontains=q) |
        Q(cpf_cnpj__icontains=q) |
        Q(celular__icontains=q) |
        Q(telefone_fixo__icontains=q)
    ).order_by('nome')[:20]

    resultados = []
    for c in clientes:
        resultados.append({
            'id': c.id,
            'nome': c.nome,
            'documento': c.cpf_cnpj or '',
            'telefone': c.celular or c.telefone_fixo or '',
            'cidade': f'{c.cidade}/{c.uf}' if c.cidade else '',
        })

    return JsonResponse({'resultados': resultados})
