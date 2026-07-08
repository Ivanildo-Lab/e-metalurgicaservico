from django.contrib import admin
from .models import Cadastro, CategoriaCliente

# 1. Categoria de Clientes (Simples)
@admin.register(CategoriaCliente)
class CategoriaClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa')
    list_filter = ('empresa',)
    search_fields = ('nome',)

    # Lógica SaaS para Categorias
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not obj.empresa_id:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)


# 2. Cadastro Principal (Clientes e Fornecedores)
@admin.register(Cadastro)
class CadastroAdmin(admin.ModelAdmin):
    # CORREÇÃO DOS NOMES DOS CAMPOS AQUI:
    # cpf -> cpf_cnpj
    # estado -> uf
    list_display = ('nome', 'empresa', 'papel', 'tipo_pessoa', 'cpf_cnpj', 'celular', 'uf', 'situacao')
    
    list_filter = ('papel', 'tipo_pessoa', 'situacao', 'uf', 'empresa')
    
    search_fields = ('nome', 'razao_social', 'cpf_cnpj', 'email')
    
    # Organização do formulário no Admin
    fieldsets = (
        ('Classificação', {
            'fields': ('empresa', 'papel', 'categoria', 'situacao')
        }),
        ('Identificação', {
            'fields': ('tipo_pessoa', 'nome', 'razao_social', 'cpf_cnpj', 'rg_ie', 'data_nascimento')
        }),
        ('Contato', {
            'fields': ('email', 'celular', 'telefone_fixo')
        }),
        ('Endereço', {
            'fields': ('cep', 'endereco', 'bairro', 'cidade', 'uf')
        }),
        ('Outros', {
            'fields': ('foto', 'observacoes')
        }),
    )

    # --- LÓGICA SAAS (MULTIEMPRESA) ---
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Se não for superusuário, esconde o campo empresa (preenche automático)
        if not request.user.is_superuser:
            if 'empresa' in form.base_fields:
                form.base_fields['empresa'].disabled = True
                form.base_fields['empresa'].widget.attrs['style'] = 'display:none;'
        return form

    def save_model(self, request, obj, form, change):
        # Vincula à empresa do usuário logado se não tiver
        if not obj.empresa_id and not request.user.is_superuser:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)