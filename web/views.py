from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta
from cadastros.models import Cadastro
from financeiro.models import Lancamento, Conta
from servicos.models import OrdemServico

# ==========================================
# LANDING PAGE (Tela Inicial)
# ==========================================
def home(request):
    """Tela de entrada (antes do login ou home do sistema)"""
    return render(request, 'web/home.html')


# ==========================================
# DASHBOARD (Painel Principal)
# ==========================================
@login_required
def dashboard(request):
    empresa = request.user.empresa
    hoje = timezone.now().date()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # 1. DADOS DE CADASTROS
    # Filtra apenas quem é Cliente (CLI) ou Ambos (AMB)
    qs_clientes = Cadastro.objects.filter(
        empresa=empresa
    ).filter(Q(papel='CLI') | Q(papel='AMB'))

    total_clientes = qs_clientes.count()
    ativos = qs_clientes.filter(situacao='ATIVO').count()
    
    # 2. DADOS FINANCEIROS (REALIZADO / FLUXO)
    # Soma apenas o que foi BAIXADO/PAGO neste mês
    
    # Receitas (Créditos)
    receita_mensal = Lancamento.objects.filter(
        empresa=empresa,
        tipo='C', 
        data_lancamento__month=mes_atual,
        data_lancamento__year=ano_atual
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    # Despesas (Débitos) - Vem negativo do banco
    despesa_mensal_raw = Lancamento.objects.filter(
        empresa=empresa,
        tipo='D', 
        data_lancamento__month=mes_atual,
        data_lancamento__year=ano_atual
    ).aggregate(Sum('valor'))['valor__sum'] or 0

    # Saldo Real (Soma direta pois despesa é negativa)
    saldo_mes = receita_mensal + despesa_mensal_raw

    # 3. LISTAS DE ALERTA
    ultimos_pagamentos = Lancamento.objects.filter(
        empresa=empresa, 
        tipo='C'
    ).order_by('-data_lancamento')[:5]

    contas_atrasadas = Conta.objects.filter(
        empresa=empresa,
        plano_de_contas__tipo='R', # Só queremos saber de receber
        status='PENDENTE',
        data_vencimento__lt=hoje
    ).order_by('data_vencimento')[:5]

    # 4. DADOS DE ORDENS DE SERVIÇO
    os_total = OrdemServico.objects.filter(empresa=empresa).count()
    os_abertas = OrdemServico.objects.filter(empresa=empresa, status='ABERTA').count()
    os_concluidas = OrdemServico.objects.filter(empresa=empresa, status='CONCLUIDA').count()
    os_fechadas_mes = OrdemServico.objects.filter(
        empresa=empresa, status='FECHADA',
        data_conclusao__month=mes_atual, data_conclusao__year=ano_atual
    ).count()
    os_canceladas = OrdemServico.objects.filter(empresa=empresa, status='CANCELADA').count()

    # Gráfico de OS por status (dados para doughnut/pie)
    os_status_labels = ['Abertas', 'Concluídas', 'Fechadas', 'Canceladas']
    os_status_dados = [os_abertas, os_concluidas, os_fechadas_mes, os_canceladas]

    # Últimas 6 meses de OS fechadas (para gráfico de barras)
    os_meses_labels = []
    os_meses_dados = []
    for i in range(5, -1, -1):
        data_ref = hoje.replace(day=1) - timedelta(days=i*30)
        mes_ref = data_ref.month
        ano_ref = data_ref.year
        os_meses_labels.append(f"{mes_ref:02d}/{ano_ref}")
        qtd = OrdemServico.objects.filter(
            empresa=empresa, status='FECHADA',
            data_conclusao__month=mes_ref, data_conclusao__year=ano_ref
        ).count()
        os_meses_dados.append(qtd)

    # 5. DADOS PARA O GRÁFICO (Últimos 6 meses)
    labels_grafico = []
    dados_receita = []
    dados_despesa = []
    
    for i in range(5, -1, -1):
        data_ref = hoje.replace(day=1) - timedelta(days=i*30)
        mes_ref = data_ref.month
        ano_ref = data_ref.year
        
        labels_grafico.append(f"{mes_ref:02d}/{ano_ref}")
        
        r = Lancamento.objects.filter(
            empresa=empresa, tipo='C', 
            data_lancamento__month=mes_ref, data_lancamento__year=ano_ref
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        d = Lancamento.objects.filter(
            empresa=empresa, tipo='D', 
            data_lancamento__month=mes_ref, data_lancamento__year=ano_ref
        ).aggregate(Sum('valor'))['valor__sum'] or 0
        
        dados_receita.append(float(r))
        dados_despesa.append(abs(float(d)))

    context = {
        'total_clientes': total_clientes,
        'ativos': ativos,
        'receita_mensal': receita_mensal,
        'despesa_mensal': abs(despesa_mensal_raw),
        'saldo': saldo_mes,
        'ultimos_pagamentos': ultimos_pagamentos,
        'contas_atrasadas': contas_atrasadas,
        'grafico_labels': labels_grafico,
        'grafico_receita': dados_receita,
        'grafico_despesa': dados_despesa,
        'os_total': os_total,
        'os_abertas': os_abertas,
        'os_concluidas': os_concluidas,
        'os_fechadas_mes': os_fechadas_mes,
        'os_canceladas': os_canceladas,
        'os_status_labels': os_status_labels,
        'os_status_dados': os_status_dados,
        'os_meses_labels': os_meses_labels,
        'os_meses_dados': os_meses_dados,
    }
    
    return render(request, 'web/dashboard.html', context)