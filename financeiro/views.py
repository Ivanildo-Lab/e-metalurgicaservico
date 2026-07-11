from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import permission_required_module
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils.dateparse import parse_date

# Imports dos Modelos e Formulários
from .models import Conta, Lancamento, Caixa, PlanoDeContas
from .forms import ContaForm, LancamentoManualForm, CaixaForm, PlanoContasForm
from core.models import ParametroSistema
from decimal import Decimal
import calendar
import random


def add_months(source_date, months):
    """Adiciona meses a uma data corretamente (ex: 31/01 + 1 mês -> 28/02)"""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

# ==========================================================
# 1. GESTÃO DE CAIXAS (BANCOS)
# ==========================================================
@login_required
@permission_required_module('financeiro')
def lista_caixas(request):
    caixas = Caixa.objects.filter(empresa=request.user.empresa)
    return render(request, 'financeiro/caixa_list.html', {'caixas': caixas})

@login_required
@permission_required_module('financeiro')
def adicionar_caixa(request):
    if request.method == 'POST':
        form = CaixaForm(request.POST)
        if form.is_valid():
            caixa = form.save(commit=False)
            caixa.empresa = request.user.empresa
            caixa.save()
            messages.success(request, "Caixa adicionado com sucesso!")
            return redirect('financeiro:lista_caixas')
    else:
        form = CaixaForm()
    return render(request, 'financeiro/caixa_form.html', {'form': form})

@login_required
@permission_required_module('financeiro')
def editar_caixa(request, id):
    caixa = get_object_or_404(Caixa, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = CaixaForm(request.POST, instance=caixa)
        if form.is_valid():
            form.save()
            messages.success(request, "Caixa atualizado!")
            return redirect('financeiro:lista_caixas')
    else:
        form = CaixaForm(instance=caixa)
    return render(request, 'financeiro/caixa_form.html', {'form': form})

@login_required
@permission_required_module('financeiro')
def excluir_caixa(request, id):
    caixa = get_object_or_404(Caixa, id=id, empresa=request.user.empresa)
    if caixa.lancamento_set.exists():
        messages.error(request, "Não é possível excluir este caixa pois existem lançamentos vinculados.")
    else:
        caixa.delete()
        messages.success(request, "Caixa excluído com sucesso.")
    return redirect('financeiro:lista_caixas')


# ==========================================================
# 2. GESTÃO DE PLANO DE CONTAS
# ==========================================================
@login_required
@permission_required_module('financeiro')
def lista_plano_de_contas(request):
    contas = PlanoDeContas.objects.filter(empresa=request.user.empresa).order_by('codigo')
    return render(request, 'financeiro/plano_de_contas_list.html', {'planos_de_contas': contas})

# financeiro/views.py

@login_required
@permission_required_module('financeiro')
def adicionar_plano_de_contas(request):
    if request.method == 'POST':
        # PASSANDO O USER AQUI
        form = PlanoContasForm(request.POST, user=request.user)
        if form.is_valid():
            conta = form.save(commit=False)
            conta.empresa = request.user.empresa
            conta.save()
            messages.success(request, "Categoria criada com sucesso!")
            return redirect('financeiro:lista_plano_de_contas')
    else:
        # E AQUI TAMBÉM
        form = PlanoContasForm(user=request.user)
    return render(request, 'financeiro/plano_de_contas_form.html', {'form': form})

@login_required
@permission_required_module('financeiro')
def editar_plano_de_contas(request, id):
    conta = get_object_or_404(PlanoDeContas, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        # PASSANDO O USER NA EDIÇÃO TAMBÉM
        form = PlanoContasForm(request.POST, instance=conta, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada!")
            return redirect('financeiro:lista_plano_de_contas')
    else:
        # E AQUI
        form = PlanoContasForm(instance=conta, user=request.user)
    return render(request, 'financeiro/plano_de_contas_form.html', {'form': form})

@login_required
@permission_required_module('financeiro')
def excluir_plano_de_contas(request, id):
    conta = get_object_or_404(PlanoDeContas, id=id, empresa=request.user.empresa)
    if conta.lancamento_set.exists() or conta.conta_set.exists():
        messages.error(request, "Não é possível excluir: existem lançamentos ou contas usando esta categoria.")
    else:
        conta.delete()
        messages.success(request, "Categoria excluída.")
    return redirect('financeiro:lista_plano_de_contas')


# ==========================================================
# 3. CONTAS A PAGAR E RECEBER (SEPARADAS COM FILTROS)
# ==========================================================

@login_required
@permission_required_module('financeiro')
def lista_contas_receber(request):
    """Lista apenas contas onde o Plano de Contas é TIPO RECEITA"""
    # Base Query
    contas = Conta.objects.filter(empresa=request.user.empresa, plano_de_contas__tipo='R')

    # --- FILTROS DE BUSCA ---
    data_ini = request.GET.get('data_ini')
    data_fim = request.GET.get('data_fim')
    cliente_nome = request.GET.get('cliente')
    status = request.GET.get('status')
    categoria_id = request.GET.get('categoria') # NOVO

    if data_ini and data_fim:
        contas = contas.filter(data_vencimento__range=[data_ini, data_fim])
    
    if cliente_nome:
        contas = contas.filter(cadastro__nome__icontains=cliente_nome)

    if status:
        if status == 'ATRASADA':
            contas = contas.filter(status='PENDENTE', data_vencimento__lt=date.today())
        else:
            contas = contas.filter(status=status)

    # Filtro por Categoria (NOVO)
    if categoria_id:
        contas = contas.filter(plano_de_contas_id=categoria_id)

    # Dados para os Dropdowns
    caixas = Caixa.objects.filter(empresa=request.user.empresa)
    # Carrega apenas categorias de RECEITA para o filtro
    categorias = PlanoDeContas.objects.filter(empresa=request.user.empresa, tipo='R').order_by('nome')
    
    return render(request, 'financeiro/contas_lista.html', {
        'contas': contas.order_by('data_vencimento'), 
        'caixas': caixas,
        'categorias': categorias, # Envia para o template
        'titulo': 'Contas a Receber',
        'tipo_lista': 'receber',
        
        # Mantém filtros preenchidos
        'filtro_data_ini': data_ini,
        'filtro_data_fim': data_fim,
        'filtro_nome': cliente_nome,
        'filtro_status': status,
        'filtro_categoria': categoria_id # NOVO
    })

@login_required
@permission_required_module('financeiro')
def lista_contas_pagar(request):
    """Lista apenas contas onde o Plano de Contas é TIPO DESPESA"""
    # Base Query
    contas = Conta.objects.filter(empresa=request.user.empresa, plano_de_contas__tipo='D')

    # --- FILTROS DE BUSCA ---
    data_ini = request.GET.get('data_ini')
    data_fim = request.GET.get('data_fim')
    fornecedor_nome = request.GET.get('cliente')
    status = request.GET.get('status')
    categoria_id = request.GET.get('categoria') # NOVO

    if data_ini and data_fim:
        contas = contas.filter(data_vencimento__range=[data_ini, data_fim])
    
    if fornecedor_nome:
        contas = contas.filter(cadastro__nome__icontains=fornecedor_nome)

    if status:
        if status == 'ATRASADA':
            contas = contas.filter(status='PENDENTE', data_vencimento__lt=date.today())
        else:
            contas = contas.filter(status=status)

    # Filtro por Categoria (NOVO)
    if categoria_id:
        contas = contas.filter(plano_de_contas_id=categoria_id)

    caixas = Caixa.objects.filter(empresa=request.user.empresa)
    # Carrega apenas categorias de DESPESA para o filtro
    categorias = PlanoDeContas.objects.filter(empresa=request.user.empresa, tipo='D').order_by('nome')
    
    return render(request, 'financeiro/contas_lista.html', {
        'contas': contas.order_by('data_vencimento'), 
        'caixas': caixas,
        'categorias': categorias,
        'titulo': 'Contas a Pagar',
        'tipo_lista': 'pagar',
        'filtro_data_ini': data_ini,
        'filtro_data_fim': data_fim,
        'filtro_nome': fornecedor_nome,
        'filtro_status': status,
        'filtro_categoria': categoria_id
    })

# ==========================================================
# FUNÇÃO AUXILIAR PARA CRIAR CONTAS (EVITA REPETIÇÃO DE CÓDIGO)
# ==========================================================
def processar_lancamento_conta(request, form, tipo_redirect):
    """Lógica comum para salvar Receita ou Despesa com parcelamento"""
    dados = form.cleaned_data
    
    # Dados base
    descricao_original = dados['descricao']
    valor_original = dados['valor']
    vencimento_inicial = dados['data_vencimento']
    gerar_parcelas = dados.get('gerar_parcelas')
    
    if gerar_parcelas:
        qtd = dados['qtd_parcelas']
        juros = dados.get('taxa_juros') or Decimal(0)
        
        acrescimo = valor_original * (juros / Decimal(100))
        valor_total = valor_original + acrescimo
        valor_parcela = valor_total / qtd
        
        # Gera um número aleatório de 4 dígitos para agrupar as parcelas (Ex: 1234)
        grupo_parcela = random.randint(1000, 9999) 
        
        # Cria as parcelas
        for i in range(qtd):
            nova_conta = form.save(commit=False)
            nova_conta.pk = None
            nova_conta.empresa = request.user.empresa
            
            # Formata: Descrição (Parcela X/Y)
            nova_conta.descricao = f"{descricao_original}"
            
            # Formata: 1234-1/3
            nova_conta.documento = f"{grupo_parcela}-{i+1}/{qtd}"
            
            nova_conta.valor = valor_parcela
            nova_conta.data_vencimento = add_months(vencimento_inicial, i)
            
            nova_conta.save()
            
        messages.success(request, f"{qtd} parcelas geradas com sucesso! (Doc: {grupo_parcela})")
    else:
        # Salva normal
        conta = form.save(commit=False)
        conta.empresa = request.user.empresa
        
        # Se não parcelou, gera um documento único se quiser, ou deixa vazio
        conta.documento = str(random.randint(10000, 99999))
        
        conta.save()
        messages.success(request, "Lançamento salvo com sucesso!")

    return redirect(tipo_redirect)

# ==========================================================
# VIEWS ATUALIZADAS
# ==========================================================

@login_required
@permission_required_module('financeiro')
def nova_receita(request):
    """Cria conta pré-filtrando categorias de Receita e Clientes"""
    if request.method == 'POST':
        form = ContaForm(request.POST, user=request.user, tipo_filtro='R')
        if form.is_valid():
            return processar_lancamento_conta(request, form, 'financeiro:lista_receber')
    else:
        form = ContaForm(user=request.user, tipo_filtro='R')
    return render(request, 'financeiro/conta_form.html', {'form': form, 'titulo': 'Novo Recebimento'})

@login_required
@permission_required_module('financeiro')
def nova_despesa(request):
    """Cria conta pré-filtrando categorias de Despesa e Fornecedores"""
    if request.method == 'POST':
        form = ContaForm(request.POST, user=request.user, tipo_filtro='D')
        if form.is_valid():
            return processar_lancamento_conta(request, form, 'financeiro:lista_pagar')
    else:
        form = ContaForm(user=request.user, tipo_filtro='D')
    return render(request, 'financeiro/conta_form.html', {'form': form, 'titulo': 'Nova Despesa'})

@login_required
@permission_required_module('financeiro')
def editar_conta(request, id):
    conta = get_object_or_404(Conta, id=id, empresa=request.user.empresa)
    
    # Define o tipo para filtrar corretamente o form na edição
    tipo_filtro = conta.plano_de_contas.tipo 

    if request.method == 'POST':
        form = ContaForm(request.POST, instance=conta, user=request.user, tipo_filtro=tipo_filtro)
        if form.is_valid():
            form.save()
            messages.success(request, "Conta atualizada.")
            return redirect('financeiro:lista_receber' if tipo_filtro == 'R' else 'financeiro:lista_pagar')
    else:
        form = ContaForm(instance=conta, user=request.user, tipo_filtro=tipo_filtro)
    return render(request, 'financeiro/conta_form.html', {'form': form})

@login_required
@permission_required_module('financeiro')
def excluir_conta(request, id):
    conta = get_object_or_404(Conta, id=id, empresa=request.user.empresa)
    tipo_redirect = 'financeiro:lista_receber' if conta.plano_de_contas.tipo == 'R' else 'financeiro:lista_pagar'
    
    if conta.status == 'PAGA':
        messages.error(request, "Não é possível excluir uma conta já paga. Estorne o lançamento primeiro.")
    else:
        conta.delete()
        messages.success(request, "Conta excluída.")
    
    return redirect(tipo_redirect)

@login_required
@permission_required_module('financeiro')
def baixar_conta(request, id):
    conta = get_object_or_404(Conta, id=id, empresa=request.user.empresa)
    
    if request.method == 'POST':
        caixa_id = request.POST.get('caixa')
        data_pagamento = request.POST.get('data_pagamento')
        
        if not caixa_id or not data_pagamento:
            messages.error(request, "Preencha todos os campos da baixa.")
            return redirect('financeiro:lista_receber' if conta.plano_de_contas.tipo == 'R' else 'financeiro:lista_pagar')

        caixa = get_object_or_404(Caixa, id=caixa_id, empresa=request.user.empresa)

        # Mapeia o tipo do Plano (R/D) para o tipo do Lançamento (C/D)
        # R (Receita) -> C (Crédito)
        # D (Despesa) -> D (Débito)
        tipo_lancamento = 'C' if conta.plano_de_contas.tipo == 'R' else 'D'

        Lancamento.objects.create(
            empresa=request.user.empresa,
            caixa=caixa,
            plano_de_contas=conta.plano_de_contas,
            conta_origem=conta,
            descricao=f"Baixa: {conta.descricao}",
            data_lancamento=data_pagamento,
            valor=conta.valor,
            tipo=tipo_lancamento
        )

        conta.status = 'PAGA'
        conta.save()
        
        messages.success(request, "Baixa realizada com sucesso!")
        
        if conta.plano_de_contas.tipo == 'R':
            return redirect('financeiro:lista_receber')
        else:
            return redirect('financeiro:lista_pagar')
    
    return redirect('financeiro:lista_receber')


# ==========================================================
# 4. FLUXO DE CAIXA E RELATÓRIOS
# ==========================================================

@login_required
@permission_required_module('financeiro')
def fluxo_caixa(request):
    # 1. Definição das Datas
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    
    # Se não vier no GET, usa os padrões
    data_inicio = request.GET.get('data_inicio') or inicio_mes.strftime('%Y-%m-%d')
    data_fim = request.GET.get('data_fim') or hoje.strftime('%Y-%m-%d')

    # 2. Lógica Rígida de Seleção do Caixa
    # Verifica se o usuário submeteu o formulário (se 'caixa' está nos parametros GET)
    parametro_caixa_get = request.GET.get('caixa')
    
    caixa_id = None
    
    if parametro_caixa_get is not None:
        # CENÁRIO A: O usuário clicou em "Filtrar"
        if parametro_caixa_get != '':
            caixa_id = int(parametro_caixa_get)
        else:
            # Se veio vazio (''), o usuário quer ver "Todos" (Geral)
            caixa_id = None
    else:
        # CENÁRIO B: Primeira carga da página (sem filtros na URL)
        # Tenta pegar o padrão do sistema
        try:
            param = ParametroSistema.objects.get(empresa=request.user.empresa, chave='CAIXA_PADRAO_ID')
            if param.valor and param.valor.isdigit():
                caixa_id = int(param.valor)
        except ParametroSistema.DoesNotExist:
            caixa_id = None

    # 3. Definição da Categoria
    categoria_id_str = request.GET.get('categoria')

    # =======================================================
    # CÁLCULO DO SALDO ANTERIOR (Onde estava o erro provável)
    # =======================================================
    
    # A. Saldo Inicial do Cadastro (Dinheiro que "nasceu" na conta)
    saldo_inicial_cadastro = 0
    
    # Se tem filtro de categoria, Saldo Inicial de banco é zero (banco não tem categoria)
    if not categoria_id_str:
        if caixa_id:
            # BUSCA ESPECÍFICA: Pega só deste caixa
            caixa_obj = Caixa.objects.filter(id=caixa_id, empresa=request.user.empresa).first()
            if caixa_obj:
                saldo_inicial_cadastro = caixa_obj.saldo_inicial
        else:
            # GERAL: Soma todos os caixas da empresa
            saldo_inicial_cadastro = Caixa.objects.filter(empresa=request.user.empresa).aggregate(Sum('saldo_inicial'))['saldo_inicial__sum'] or 0

    # B. Movimentações Passadas (Tudo antes da data_inicio)
    movimentos_anteriores = Lancamento.objects.filter(
        empresa=request.user.empresa,
        data_lancamento__lt=data_inicio # Menor que data de início
    )
    
    # Filtros obrigatórios no histórico
    if caixa_id:
        movimentos_anteriores = movimentos_anteriores.filter(caixa_id=caixa_id)
    
    if categoria_id_str:
        movimentos_anteriores = movimentos_anteriores.filter(plano_de_contas_id=categoria_id_str)

    # Soma do histórico
    total_anteriores = movimentos_anteriores.aggregate(Sum('valor'))['valor__sum'] or 0

    # ===> SALDO ANTERIOR FINAL
    saldo_anterior = saldo_inicial_cadastro + total_anteriores


    # =======================================================
    # MOVIMENTAÇÕES DO PERÍODO (TABELA)
    # =======================================================
    lancamentos = Lancamento.objects.filter(
        empresa=request.user.empresa,
        data_lancamento__range=[data_inicio, data_fim]
    )

    if caixa_id:
        lancamentos = lancamentos.filter(caixa_id=caixa_id)
    
    if categoria_id_str:
        lancamentos = lancamentos.filter(plano_de_contas_id=categoria_id_str)

    lancamentos = lancamentos.order_by('-data_lancamento')
    
    # Totais do Período
    total_periodo = lancamentos.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # ===> SALDO FINAL
    saldo_final = saldo_anterior + total_periodo

    # Contexto
    caixas = Caixa.objects.filter(empresa=request.user.empresa)
    categorias = PlanoDeContas.objects.filter(empresa=request.user.empresa).order_by('nome')

    return render(request, 'financeiro/fluxo_lista.html', {
        'lancamentos': lancamentos, 
        'saldo_anterior': saldo_anterior,
        'saldo_final': saldo_final,
        'caixas': caixas,
        'categorias': categorias,
        'caixa_selecionado_id': str(caixa_id) if caixa_id else '',
        'categoria_selecionada_id': categoria_id_str or '',
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    })

@login_required
@permission_required_module('financeiro')
def novo_lancamento_manual(request):
    if request.method == 'POST':
        form = LancamentoManualForm(request.POST, user=request.user)
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.empresa = request.user.empresa
            lancamento.save()
            messages.success(request, "Lançamento registrado!")
            return redirect('financeiro:fluxo_caixa')
    else:
        form = LancamentoManualForm(user=request.user)
    return render(request, 'financeiro/lancamento_form.html', {'form': form})

@login_required
@permission_required_module('financeiro')
def editar_lancamento(request, id):
    lancamento = get_object_or_404(Lancamento, id=id, empresa=request.user.empresa)
    if request.method == 'POST':
        form = LancamentoManualForm(request.POST, instance=lancamento, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Lançamento atualizado!")
            return redirect('financeiro:fluxo_caixa')
    else:
        form = LancamentoManualForm(instance=lancamento, user=request.user)
    return render(request, 'financeiro/lancamento_form.html', {'form': form})

@login_required
@permission_required_module('financeiro')
def excluir_lancamento(request, id):
    lancamento = get_object_or_404(Lancamento, id=id, empresa=request.user.empresa)
    
    # Se for baixa de conta, retorna a conta para PENDENTE
    if lancamento.conta_origem:
        conta = lancamento.conta_origem
        conta.status = 'PENDENTE'
        conta.save()
        aviso_extra = " A conta original voltou para 'Pendente'."
    else:
        aviso_extra = ""

    lancamento.delete()
    messages.success(request, f"Lançamento excluído.{aviso_extra}")
    return redirect('financeiro:fluxo_caixa')

@login_required
@permission_required_module('financeiro')
def relatorio_fluxo(request):
    # 1. Definição de Datas
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    
    data_inicio_str = request.GET.get('data_inicio') or inicio_mes.strftime('%Y-%m-%d')
    data_fim_str = request.GET.get('data_fim') or hoje.strftime('%Y-%m-%d')
    
    data_inicio = parse_date(data_inicio_str)
    data_fim = parse_date(data_fim_str)

    # 2. Filtros (Caixa e Categoria)
    caixa_id_str = request.GET.get('caixa')
    categoria_id_str = request.GET.get('categoria')
    
    caixa_id = None
    caixa_selecionado = None

    # Lógica do Caixa (Prioridade: Filtro > Padrão > Geral)
    if caixa_id_str and caixa_id_str != 'None' and caixa_id_str != '':
        caixa_id = int(caixa_id_str)
        caixa_selecionado = Caixa.objects.filter(id=caixa_id, empresa=request.user.empresa).first()
    else:
        # Se não veio no filtro, tenta o padrão APENAS se o usuário não pediu "Todos" explicitamente
        # Aqui assumimos que se veio vazio na URL, tenta o padrão.
        try:
            param = ParametroSistema.objects.get(empresa=request.user.empresa, chave='CAIXA_PADRAO_ID')
            if param.valor and param.valor.isdigit():
                caixa_id = int(param.valor)
                caixa_selecionado = Caixa.objects.filter(id=caixa_id, empresa=request.user.empresa).first()
        except ParametroSistema.DoesNotExist:
            pass

    # =======================================================
    # 3. CÁLCULO DO SALDO ANTERIOR (A CORREÇÃO)
    # =======================================================
    saldo_inicial_cadastro = 0
    
    # Se não tem filtro de categoria, considera o saldo de abertura do banco
    if not categoria_id_str:
        if caixa_id:
            if caixa_selecionado:
                saldo_inicial_cadastro = caixa_selecionado.saldo_inicial
        else:
            # Soma de todos os caixas
            saldo_inicial_cadastro = Caixa.objects.filter(empresa=request.user.empresa).aggregate(Sum('saldo_inicial'))['saldo_inicial__sum'] or 0

    # Movimentações anteriores à data de início
    movimentos_anteriores = Lancamento.objects.filter(
        empresa=request.user.empresa,
        data_lancamento__lt=data_inicio_str
    )
    
    if caixa_id:
        movimentos_anteriores = movimentos_anteriores.filter(caixa_id=caixa_id)
    
    if categoria_id_str:
        movimentos_anteriores = movimentos_anteriores.filter(plano_de_contas_id=categoria_id_str)

    total_anteriores = movimentos_anteriores.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # ===> SALDO ANTERIOR REAL
    saldo_anterior = saldo_inicial_cadastro + total_anteriores


    # =======================================================
    # 4. DADOS DO PERÍODO
    # =======================================================
    lancamentos = Lancamento.objects.filter(
        empresa=request.user.empresa,
        data_lancamento__range=[data_inicio_str, data_fim_str]
    )

    if caixa_id:
        lancamentos = lancamentos.filter(caixa_id=caixa_id)
    
    if categoria_id_str:
        lancamentos = lancamentos.filter(plano_de_contas_id=categoria_id_str)

    # Listas detalhadas
    receitas = lancamentos.filter(tipo='C').order_by('data_lancamento')
    despesas = lancamentos.filter(tipo='D').order_by('data_lancamento')

    # Totais do Período
    total_receitas = receitas.aggregate(Sum('valor'))['valor__sum'] or 0
    total_despesas = despesas.aggregate(Sum('valor'))['valor__sum'] or 0
    resultado_periodo = total_receitas + total_despesas
    
    # ===> SALDO FINAL REAL
    saldo_final = saldo_anterior + resultado_periodo

    resumo_pagamentos = (
        Lancamento.objects.filter(
            empresa=request.user.empresa,
            data_lancamento__range=[data_inicio_str, data_fim_str],
            tipo='C',
            descricao__icontains='Recebimento OS'
        )
        .select_related('caixa')
        .order_by('data_lancamento', 'id')
    )

    if caixa_id:
        resumo_pagamentos = resumo_pagamentos.filter(caixa_id=caixa_id)

    resumo_pagamentos = list(resumo_pagamentos)

    return render(request, 'financeiro/relatorio_impresso.html', {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'caixa_selecionado': caixa_selecionado,
        'receitas': receitas,
        'despesas': despesas,
        
        # Totais Calculados
        'saldo_anterior': saldo_anterior,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'resultado_periodo': resultado_periodo,
        'saldo_final': saldo_final,
        'resumo_pagamentos': resumo_pagamentos,
        
        'empresa': request.user.empresa,
    })

@login_required
@permission_required_module('financeiro')
def relatorio_contas(request):
    """
    Gera relatório de Contas a Pagar ou Receber baseado nos filtros da URL
    """
    tipo_lista = request.GET.get('tipo_lista', 'receber')
    tipo_plano = 'R' if tipo_lista == 'receber' else 'D'
    
    contas = Conta.objects.filter(empresa=request.user.empresa, plano_de_contas__tipo=tipo_plano)

    # Helper para limpar strings
    def clean_val(val):
        return val if val and val != 'None' else None

    data_ini = clean_val(request.GET.get('data_ini'))
    data_fim = clean_val(request.GET.get('data_fim'))
    nome = clean_val(request.GET.get('cliente'))
    status = clean_val(request.GET.get('status'))
    categoria_id = clean_val(request.GET.get('categoria')) # NOVO

    if data_ini and data_fim:
        contas = contas.filter(data_vencimento__range=[data_ini, data_fim])
    
    if nome:
        contas = contas.filter(cadastro__nome__icontains=nome)

    if status:
        if status == 'ATRASADA':
            contas = contas.filter(status='PENDENTE', data_vencimento__lt=date.today())
        else:
            contas = contas.filter(status=status)

    # Filtro Categoria no Relatório
    if categoria_id:
        contas = contas.filter(plano_de_contas_id=categoria_id)

    contas = contas.order_by('data_vencimento')
    total_valor = contas.aggregate(Sum('valor'))['valor__sum'] or 0
    titulo_relatorio = "Relatório de Contas a Receber" if tipo_lista == 'receber' else "Relatório de Contas a Pagar"

    return render(request, 'financeiro/relatorio_contas_impresso.html', {
        'contas': contas,
        'total_valor': total_valor,
        'titulo_relatorio': titulo_relatorio,
        'empresa': request.user.empresa,
        'data_ini': parse_date(data_ini) if data_ini else None,
        'data_fim': parse_date(data_fim) if data_fim else None,
        'status_filtro': status
    })

@login_required
@permission_required_module('financeiro')
def relatorio_dre(request):
    # 1. Filtros de Data
    hoje = date.today()
    inicio_ano = hoje.replace(month=1, day=1)
    
    data_inicio_str = request.GET.get('data_inicio') or inicio_ano.strftime('%Y-%m-%d')
    data_fim_str = request.GET.get('data_fim') or hoje.strftime('%Y-%m-%d')
    
    data_inicio = parse_date(data_inicio_str)
    data_fim = parse_date(data_fim_str)

    # 2. Busca Lançamentos
    lancamentos = Lancamento.objects.filter(
        empresa=request.user.empresa,
        data_lancamento__range=[data_inicio_str, data_fim_str],
        plano_de_contas__isnull=False
    )

    # 3. Agrupamento (Total por Categoria)
    from django.db.models import Sum
    
    # Receitas
    receitas = lancamentos.filter(tipo='C').values(
        'plano_de_contas__codigo', 'plano_de_contas__nome'
    ).annotate(total=Sum('valor')).order_by('plano_de_contas__codigo')

    total_receitas = lancamentos.filter(tipo='C').aggregate(Sum('valor'))['valor__sum'] or 0

    # Despesas
    despesas = lancamentos.filter(tipo='D').values(
        'plano_de_contas__codigo', 'plano_de_contas__nome'
    ).annotate(total=Sum('valor')).order_by('plano_de_contas__codigo')

    total_despesas = lancamentos.filter(tipo='D').aggregate(Sum('valor'))['valor__sum'] or 0

    # 4. Resultado (Lucro ou Prejuízo)
    resultado = total_receitas + total_despesas

    return render(request, 'financeiro/relatorio_dre.html', {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'receitas': receitas,
        'despesas': despesas,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'resultado': resultado,
        'empresa': request.user.empresa,
    })

@login_required
@permission_required_module('financeiro')
def relatorio_dre_sintetico(request):
    # 1. Filtros
    hoje = date.today()
    inicio_ano = hoje.replace(month=1, day=1)
    
    data_inicio_str = request.GET.get('data_inicio') or inicio_ano.strftime('%Y-%m-%d')
    data_fim_str = request.GET.get('data_fim') or hoje.strftime('%Y-%m-%d')
    
    data_inicio = parse_date(data_inicio_str)
    data_fim = parse_date(data_fim_str)

    # 2. Busca
    lancamentos = Lancamento.objects.filter(
        empresa=request.user.empresa,
        data_lancamento__range=[data_inicio_str, data_fim_str],
        plano_de_contas__isnull=False
    )

    # 3. Agrupamento Manual (Soma por Código Pai)
    grupos_receitas = {}
    grupos_despesas = {}

    total_rec = 0
    total_desp = 0

    for l in lancamentos:
        # Pega o primeiro nível do código (ex: '01.02.001' -> pega '01')
        # Se seu código não usa ponto (ex: 101001), ajuste o slice (ex: l.plano_de_contas.codigo[:2])
        codigo_pai = l.plano_de_contas.codigo.split('.')[0] if '.' in l.plano_de_contas.codigo else l.plano_de_contas.codigo[:2]
        
        # Garante um fallback se o código for vazio
        if not codigo_pai: 
            codigo_pai = 'OUTROS'

        # Lógica para Receitas (C)
        if l.tipo == 'C':
            if codigo_pai not in grupos_receitas:
                nome_pai_obj = PlanoDeContas.objects.filter(empresa=request.user.empresa, codigo=codigo_pai).first()
                nome_grupo = nome_pai_obj.nome if nome_pai_obj else f'GRUPO {codigo_pai}'
                grupos_receitas[codigo_pai] = {'nome': nome_grupo, 'total': 0}
            
            grupos_receitas[codigo_pai]['total'] += l.valor
            total_rec += l.valor
            
        # Lógica para Despesas (D)
        elif l.tipo == 'D':
            if codigo_pai not in grupos_despesas:
                nome_pai_obj = PlanoDeContas.objects.filter(empresa=request.user.empresa, codigo=codigo_pai).first()
                nome_grupo = nome_pai_obj.nome if nome_pai_obj else f'GRUPO {codigo_pai}'
                grupos_despesas[codigo_pai] = {'nome': nome_grupo, 'total': 0}
            
            grupos_despesas[codigo_pai]['total'] += l.valor # Soma valor negativo
            total_desp += l.valor

    # 4. Ordenação (Para aparecer 01, 02, 03 na ordem)
    # Transforma dicionário em lista de tuplas ordenadas
    receitas_ordenadas = dict(sorted(grupos_receitas.items()))
    despesas_ordenadas = dict(sorted(grupos_despesas.items()))

    resultado = total_rec + total_desp

    return render(request, 'financeiro/relatorio_dre_sintetico.html', {
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'receitas': receitas_ordenadas,
        'despesas': despesas_ordenadas,
        'total_receitas': total_rec,
        'total_despesas': total_desp,
        'resultado': resultado,
        'empresa': request.user.empresa,
    })