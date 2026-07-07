from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import permission_required_module
from django.contrib import messages
from django.db.models import Q
from .models import Cadastro, CategoriaCliente
from .forms import CadastroForm

# ==================================================
# GESTÃO DE CLIENTES (Sócios / Alunos / Clientes)
# ==================================================

@login_required
@permission_required_module('cadastros')
def lista_clientes(request):
    # Filtra apenas quem é Cliente ou Ambos (CLI + AMB)
    qs = Cadastro.objects.filter(empresa=request.user.empresa).filter(Q(papel='CLI') | Q(papel='AMB'))
    
    # --- Filtros da URL ---
    q = request.GET.get('q')
    categoria_id = request.GET.get('categoria')
    status = request.GET.get('status')

    if q:
        # Busca por Nome, CPF ou Email
        qs = qs.filter(Q(nome__icontains=q) | Q(cpf_cnpj__icontains=q) | Q(email__icontains=q))
    
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)

    if status:
        qs = qs.filter(situacao=status)

    # Carrega categorias para o dropdown de filtro
    categorias = CategoriaCliente.objects.filter(empresa=request.user.empresa)
    
    return render(request, 'cadastros/lista_clientes.html', {
        'cadastros': qs,
        'categorias': categorias,
        'filtro_q': q,
        'filtro_cat': categoria_id,
        'filtro_status': status
    })

@login_required
@permission_required_module('cadastros')
def novo_cliente(request):
    if request.method == 'POST':
        # Passamos papel='CLI' para o form saber que deve manter o campo Categoria
        form = CadastroForm(request.POST, request.FILES, user=request.user, papel='CLI')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.papel = 'CLI' # Força ser Cliente
            obj.save()
            messages.success(request, "Cliente cadastrado com sucesso!")
            return redirect('lista_clientes')
    else:
        # Inicializa como Pessoa Física por padrão
        form = CadastroForm(user=request.user, initial={'tipo_pessoa': 'PF'}, papel='CLI')
    
    return render(request, 'cadastros/formulario.html', {
        'form': form, 
        'titulo': 'Novo Cliente',
        'url_cancelar': 'lista_clientes' 
    })


# ==================================================
# GESTÃO DE FORNECEDORES
# ==================================================

@login_required
@permission_required_module('cadastros')
def lista_fornecedores(request):
    # Filtra apenas Fornecedores ou Ambos (FOR + AMB)
    qs = Cadastro.objects.filter(empresa=request.user.empresa).filter(Q(papel='FOR') | Q(papel='AMB'))
    
    # --- Filtros da URL ---
    q = request.GET.get('q')
    status = request.GET.get('status')

    if q:
        # Busca por Nome, CPF/CNPJ ou Razão Social
        qs = qs.filter(Q(nome__icontains=q) | Q(cpf_cnpj__icontains=q) | Q(razao_social__icontains=q))
        
    if status:
        qs = qs.filter(situacao=status)

    return render(request, 'cadastros/lista_fornecedores.html', {
        'cadastros': qs,
        'filtro_q': q,
        'filtro_status': status
    })

@login_required
@permission_required_module('cadastros')
def novo_fornecedor(request):
    if request.method == 'POST':
        # Passamos papel='FOR' para o form remover o campo Categoria
        form = CadastroForm(request.POST, request.FILES, user=request.user, papel='FOR')
        if form.is_valid():
            obj = form.save(commit=False)
            obj.empresa = request.user.empresa
            obj.papel = 'FOR' # Força ser Fornecedor
            obj.save()
            messages.success(request, "Fornecedor cadastrado com sucesso!")
            return redirect('lista_fornecedores')
    else:
        # Inicializa como Pessoa Jurídica por padrão
        form = CadastroForm(user=request.user, initial={'tipo_pessoa': 'PJ'}, papel='FOR')
    
    return render(request, 'cadastros/formulario.html', {
        'form': form, 
        'titulo': 'Novo Fornecedor',
        'url_cancelar': 'lista_fornecedores'
    })


# ==================================================
# AÇÕES GERAIS (EDITAR / EXCLUIR)
# ==================================================

@login_required
@permission_required_module('cadastros')
def editar_cadastro(request, id):
    cadastro = get_object_or_404(Cadastro, id=id, empresa=request.user.empresa)
    
    # Define dinamicamente para onde voltar ao clicar em Cancelar ou Salvar
    rota_retorno = 'lista_fornecedores' if cadastro.papel == 'FOR' else 'lista_clientes'

    if request.method == 'POST':
        # Passamos o papel atual (cadastro.papel) para manter a lógica do campo categoria
        form = CadastroForm(request.POST, request.FILES, instance=cadastro, user=request.user, papel=cadastro.papel)
        if form.is_valid():
            form.save()
            messages.success(request, "Dados atualizados com sucesso!")
            return redirect(rota_retorno)
    else:
        form = CadastroForm(instance=cadastro, user=request.user, papel=cadastro.papel)
    
    return render(request, 'cadastros/formulario.html', {
        'form': form, 
        'titulo': f'Editar {cadastro.nome}',
        'url_cancelar': rota_retorno
    })

@login_required
@permission_required_module('cadastros')
def excluir_cadastro(request, id):
    cadastro = get_object_or_404(Cadastro, id=id, empresa=request.user.empresa)
    tipo_redirect = 'lista_fornecedores' if cadastro.papel == 'FOR' else 'lista_clientes'

    # Proteção de Integridade: Não permite apagar se tiver Financeiro vinculado
    if cadastro.conta_set.exists() or cadastro.lancamento_set.exists():
        messages.error(request, "Não é possível excluir: Este cadastro possui movimentações financeiras. Recomendamos inativá-lo.")
    else:
        cadastro.delete()
        messages.success(request, "Cadastro excluído com sucesso.")
    
    return redirect(tipo_redirect)