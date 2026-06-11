from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse

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
def novo_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()
            messages.success(request, "Funcionário cadastrado com sucesso!")
            return redirect('servicos:lista_funcionarios')
    else:
        form = FuncionarioForm(user=request.user)
    return render(request, 'servicos/funcionario_form.html', {'form': form, 'editar': False})


@login_required
def editar_funcionario(request, id):
    obj = get_object_or_404(Funcionario, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Funcionário atualizado com sucesso!")
            return redirect('servicos:lista_funcionarios')
    else:
        form = FuncionarioForm(instance=obj, user=request.user)
    return render(request, 'servicos/funcionario_form.html', {'form': form, 'editar': True})


@login_required
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
    })


@login_required
def nova_os(request):
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.save()
            messages.success(request, f"OS {obj.numero} criada com sucesso! Agora adicione os serviços.")
            return redirect('servicos:detalhe_os', id=obj.id)
    else:
        form = OrdemServicoForm(user=request.user)
    return render(request, 'servicos/os_form.html', {'form': form, 'editar': False})


@login_required
def editar_os(request, id):
    obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = OrdemServicoForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "OS atualizada com sucesso!")
            return redirect('servicos:detalhe_os', id=obj.id)
    else:
        form = OrdemServicoForm(instance=obj, user=request.user)
    return render(request, 'servicos/os_form.html', {'form': form, 'editar': True, 'os': obj})


@login_required
def excluir_os(request, id):
    obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    if obj.status == 'FECHADA':
        messages.error(request, "Não é possível excluir uma OS já fechada.")
    else:
        obj.delete()
        messages.success(request, "OS excluída com sucesso.")
    return redirect('servicos:lista_ordens')


@login_required
def salvar_os(request, id):
    """Salva os dados da OS diretamente da tela de detalhe"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)

    if request.method != 'POST':
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if os_obj.status == 'FECHADA' or os_obj.status == 'CANCELADA':
        messages.error(request, "Não é possível editar uma OS fechada ou cancelada.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    cadastro_id = request.POST.get('cadastro_id')
    descricao_geral = request.POST.get('descricao_geral', '')
    data_entrada = request.POST.get('data_entrada')
    data_prevista = request.POST.get('data_prevista') or None
    observacoes = request.POST.get('observacoes', '')

    # Validação básica
    if not cadastro_id or not descricao_geral or not data_entrada:
        messages.error(request, "Cliente, Descrição e Data de Entrada são obrigatórios.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    from django.utils.dateparse import parse_date
    os_obj.cadastro_id = int(cadastro_id)
    os_obj.descricao_geral = descricao_geral
    os_obj.data_entrada = parse_date(data_entrada)
    if data_prevista:
        os_obj.data_prevista = parse_date(data_prevista)
    os_obj.observacoes = observacoes
    os_obj.save()

    messages.success(request, f"OS {os_obj.numero} salva com sucesso!")
    return redirect('servicos:detalhe_os', id=os_obj.id)


@login_required
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
def adicionar_servico_os(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id, empresa=request.user.empresa)
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível adicionar serviços nesta OS.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if request.method == 'POST':
        form = ServicoOSForm(request.POST)
        if form.is_valid():
            servico = form.save(commit=False)
            servico.ordem_servico = os_obj
            servico.save()
            messages.success(request, "Serviço adicionado com sucesso!")
    return redirect('servicos:detalhe_os', id=os_obj.id)


@login_required
def editar_servico_os(request, id):
    servico = get_object_or_404(ServicoOS, id=id, ordem_servico__empresa=request.user.empresa)
    os_obj = servico.ordem_servico
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível editar serviços nesta OS.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if request.method == 'POST':
        form = ServicoOSForm(request.POST, instance=servico)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço atualizado!")
    return redirect('servicos:detalhe_os', id=os_obj.id)


@login_required
def excluir_servico_os(request, id):
    servico = get_object_or_404(ServicoOS, id=id, ordem_servico__empresa=request.user.empresa)
    os_obj = servico.ordem_servico
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível remover serviços desta OS.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    servico.delete()
    messages.success(request, "Serviço removido.")
    return redirect('servicos:detalhe_os', id=os_obj.id)


@login_required
def adicionar_funcionario_os(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id, empresa=request.user.empresa)
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível adicionar funcionários nesta OS.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if request.method == 'POST':
        form = FuncionarioOSForm(request.POST, empresa=request.user.empresa)
        if form.is_valid():
            func_os = form.save(commit=False)
            func_os.ordem_servico = os_obj
            func_os.save()
            messages.success(request, "Funcionário adicionado à OS!")
    return redirect('servicos:detalhe_os', id=os_obj.id)


@login_required
def editar_funcionario_os(request, id):
    func_os = get_object_or_404(FuncionarioOS, id=id, ordem_servico__empresa=request.user.empresa)
    os_obj = func_os.ordem_servico
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível editar funcionários nesta OS.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if request.method == 'POST':
        form = FuncionarioOSForm(request.POST, instance=func_os, empresa=request.user.empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Participação atualizada!")
    return redirect('servicos:detalhe_os', id=os_obj.id)


@login_required
def excluir_funcionario_os(request, id):
    func_os = get_object_or_404(FuncionarioOS, id=id, ordem_servico__empresa=request.user.empresa)
    os_obj = func_os.ordem_servico
    if os_obj.status not in ('ABERTA', 'CONCLUIDA'):
        messages.error(request, "Não é possível remover funcionários desta OS.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    func_os.delete()
    messages.success(request, "Funcionário removido da OS.")
    return redirect('servicos:detalhe_os', id=os_obj.id)


# ==========================================================
# 4. WORKFLOW DE STATUS
# ==========================================================
@login_required
def concluir_os(request, id):
    """Marca OS como CONCLUIDA"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    if request.method != 'POST':
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if os_obj.status != 'ABERTA':
        messages.error(request, "Somente OS em aberto podem ser concluídas.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if not os_obj.servicos.exists():
        messages.error(request, "Adicione pelo menos um serviço antes de concluir.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    os_obj.status = 'CONCLUIDA'
    os_obj.data_conclusao = date.today()
    os_obj.save()
    messages.success(request, f"OS {os_obj.numero} marcada como CONCLUÍDA! Agora o financeiro pode fechar.")
    return redirect('servicos:detalhe_os', id=os_obj.id)


@login_required
def cancelar_os(request, id):
    """Cancela uma OS"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    if request.method != 'POST':
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if os_obj.status == 'FECHADA':
        messages.error(request, "Não é possível cancelar uma OS já fechada.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    os_obj.status = 'CANCELADA'
    os_obj.save()
    messages.warning(request, f"OS {os_obj.numero} CANCELADA.")
    return redirect('servicos:detalhe_os', id=os_obj.id)


@login_required
def fechar_os(request, id):
    """Fecha a OS e gera o financeiro (Contas a Receber ou Baixa no Caixa)"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)

    if request.method != 'POST':
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if os_obj.status != 'CONCLUIDA':
        messages.error(request, "Somente OS CONCLUÍDAS podem ser fechadas.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    # Validações
    valor_total = os_obj.valor_total
    remuneracao_total = os_obj.remuneracao_total

    if valor_total == 0:
        messages.error(request, "A OS não possui serviços com valor. Adicione serviços antes de fechar.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

    if remuneracao_total != valor_total:
        messages.error(
            request,
            f"A remuneração (R$ {remuneracao_total:.2f}) não confere com o valor total (R$ {valor_total:.2f}). "
            f"Ajuste antes de fechar."
        )
        return redirect('servicos:detalhe_os', id=os_obj.id)

    forma = request.POST.get('forma_pagamento', 'A_VISTA')
    forma_pagamento_id = request.POST.get('forma_pagamento_id', None)
    qtd_parcelas = int(request.POST.get('qtd_parcelas', 1))
    caixa_id = request.POST.get('caixa_id', None)

    # Buscar a forma de pagamento selecionada
    forma_pagamento_obj = None
    if forma_pagamento_id:
        try:
            forma_pagamento_obj = FormaPagamento.objects.get(
                id=int(forma_pagamento_id), empresa=request.user.empresa
            )
        except (FormaPagamento.DoesNotExist, ValueError):
            pass

    if forma == 'A_PRAZO' and qtd_parcelas < 1:
        messages.error(request, "Para pagamento a prazo, informe pelo menos 1 parcela.")
        return redirect('servicos:detalhe_os', id=os_obj.id)

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
        return redirect('servicos:detalhe_os', id=os_obj.id)

    # Gerar financeiro
    if forma == 'A_VISTA':
        # Gera 1 Conta e baixa imediatamente
        conta = Conta.objects.create(
            empresa=request.user.empresa,
            descricao=f"OS {os_obj.numero} — {os_obj.descricao_geral[:100]}",
            plano_de_contas=plano_de_contas,
            cadastro=os_obj.cadastro,
            valor=valor_total,
            data_vencimento=date.today(),
            status='PENDENTE',
            documento=os_obj.numero,
        )

        # Só gera lançamento no caixa se a forma afeta_caixa (ex: Dinheiro)
        if forma_pagamento_obj and forma_pagamento_obj.afeta_caixa:
            if caixa_id:
                caixa = get_object_or_404(Caixa, id=caixa_id, empresa=request.user.empresa)
            else:
                caixa = Caixa.objects.filter(empresa=request.user.empresa).first()
                if not caixa:
                    messages.error(request, "Nenhum caixa/banco encontrado. Cadastre um em Financeiro > Caixas.")
                    return redirect('servicos:detalhe_os', id=os_obj.id)

            Lancamento.objects.create(
                empresa=request.user.empresa,
                caixa=caixa,
                plano_de_contas=plano_de_contas,
                conta_origem=conta,
                data_lancamento=date.today(),
                descricao=f"Recebimento OS {os_obj.numero} — {forma_pagamento_obj.nome}",
                valor=valor_total,
                tipo='C',
            )
            conta.status = 'PAGA'
            conta.save()
            messages.success(request, f"OS {os_obj.numero} FECHADA! Pagamento ({forma_pagamento_obj.nome}) registrado no caixa '{caixa.nome}'.")
        else:
            conta.status = 'PAGA'
            conta.save()
            nome_forma = forma_pagamento_obj.nome if forma_pagamento_obj else 'A Vista'
            messages.success(request, f"OS {os_obj.numero} FECHADA! Pagamento via {nome_forma} (sem movimentação de caixa).")

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

    return redirect('servicos:detalhe_os', id=os_obj.id)


# ==========================================================
# 5. CRUD DE METAS
# ==========================================================
@login_required
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
def nova_meta(request):
    if request.method == 'POST':
        form = MetaFuncionarioForm(request.POST, user=request.user)
        if form.is_valid():
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
def editar_meta(request, id):
    obj = get_object_or_404(MetaFuncionario, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = MetaFuncionarioForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Meta atualizada com sucesso!")
            return redirect('servicos:lista_metas')
    else:
        form = MetaFuncionarioForm(instance=obj, user=request.user)
    return render(request, 'servicos/meta_form.html', {'form': form, 'editar': True})


@login_required
def excluir_meta(request, id):
    obj = get_object_or_404(MetaFuncionario, id=id, empresa=request.user.empresa)
    obj.delete()
    messages.success(request, "Meta excluída com sucesso.")
    return redirect('servicos:lista_metas')


# ==========================================================
# 6. RELATÓRIOS
# ==========================================================
@login_required
def relatorio_mensal(request, ano, mes):
    """Relatório mensal: meta vs realizado por funcionário"""
    funcionarios = Funcionario.objects.filter(empresa=request.user.empresa, ativo=True)
    dados = []

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
        percentual = (realizado / meta_valor * 100) if meta_valor > 0 else 0
        avaliacao = meta_obj.calcular_avaliacao(realizado) if meta_obj else 'SEM_META'

        dados.append({
            'funcionario': func,
            'meta_valor': meta_valor,
            'realizado': realizado,
            'percentual': percentual,
            'avaliacao': avaliacao,
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
    })


@login_required
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
def imprimir_os(request, id):
    """Gera impressão da OS com dados do cliente, serviços e pagamento"""
    os_obj = get_object_or_404(OrdemServico, id=id, empresa=request.user.empresa)
    servicos = os_obj.servicos.all()
    valor_total = os_obj.valor_total
    valor_parcela = valor_total / os_obj.qtd_parcelas if os_obj.qtd_parcelas else valor_total

    return render(request, 'servicos/os_impressao.html', {
        'os': os_obj,
        'servicos': servicos,
        'valor_total': valor_total,
        'valor_parcela': valor_parcela,
    })


# ==========================================================
# 9. CRUD DE ORÇAMENTOS
# ==========================================================
@login_required
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
        'form': form, 'titulo': f'Editar {orcamento.numero}', 'orcamento': orcamento
    })


@login_required
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
def excluir_orcamento(request, id):
    orcamento = get_object_or_404(Orcamento, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        numero = orcamento.numero
        orcamento.delete()
        messages.success(request, f'Orçamento {numero} excluído com sucesso!')
        return redirect('servicos:lista_orcamentos')
    return redirect('servicos:detalhe_orcamento', id=id)


@login_required
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
def lista_formas_pagamento(request):
    formas = FormaPagamento.objects.filter(empresa=request.user.empresa)
    return render(request, 'servicos/formapagamento_list.html', {'formas': formas})


@login_required
def nova_forma_pagamento(request):
    if request.method == 'POST':
        form = FormaPagamentoForm(request.POST)
        if form.is_valid():
            fp = form.save(commit=False)
            fp.empresa = request.user.empresa
            fp.save()
            messages.success(request, f'Forma de pagamento "{fp.nome}" criada com sucesso!')
            return redirect('servicos:lista_formas_pagamento')
    else:
        form = FormaPagamentoForm()
    return render(request, 'servicos/formapagamento_form.html', {'form': form, 'titulo': 'Nova Forma de Pagamento'})


@login_required
def editar_forma_pagamento(request, id):
    fp = get_object_or_404(FormaPagamento, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = FormaPagamentoForm(request.POST, instance=fp)
        if form.is_valid():
            form.save()
            messages.success(request, f'Forma de pagamento "{fp.nome}" atualizada com sucesso!')
            return redirect('servicos:lista_formas_pagamento')
    else:
        form = FormaPagamentoForm(instance=fp)
    return render(request, 'servicos/formapagamento_form.html', {
        'form': form, 'titulo': f'Editar {fp.nome}', 'forma': fp
    })


@login_required
def excluir_forma_pagamento(request, id):
    fp = get_object_or_404(FormaPagamento, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        nome = fp.nome
        fp.delete()
        messages.success(request, f'Forma de pagamento "{nome}" excluída com sucesso!')
        return redirect('servicos:lista_formas_pagamento')
    return redirect('servicos:lista_formas_pagamento')
