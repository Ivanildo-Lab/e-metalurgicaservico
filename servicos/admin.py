from django.contrib import admin
from .models import (
    Funcionario, OrdemServico, ServicoOS, FuncionarioOS,
    MetaFuncionario, Orcamento, ServicoOrcamento, FormaPagamento
)


class ServicoOSInline(admin.TabularInline):
    model = ServicoOS
    extra = 1
    fields = ['descricao', 'valor']


class FuncionarioOSInline(admin.TabularInline):
    model = FuncionarioOS
    extra = 1
    fields = ['funcionario', 'valor_remuneracao']


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'email', 'ativo', 'empresa']
    list_filter = ['ativo', 'empresa']
    search_fields = ['nome', 'email']
    list_editable = ['ativo']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cadastro', 'status', 'data_entrada', 'data_prevista', 'empresa']
    list_filter = ['status', 'empresa']
    search_fields = ['numero', 'cadastro__nome', 'descricao_geral']
    readonly_fields = ['numero', 'data_conclusao']
    inlines = [ServicoOSInline, FuncionarioOSInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)


@admin.register(MetaFuncionario)
class MetaFuncionarioAdmin(admin.ModelAdmin):
    list_display = ['funcionario', 'mes', 'ano', 'meta_valor', 'empresa']
    list_filter = ['mes', 'ano', 'empresa']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)


class ServicoOrcamentoInline(admin.TabularInline):
    model = ServicoOrcamento
    extra = 1
    fields = ['descricao', 'valor']


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cadastro', 'forma_pagamento', 'data', 'empresa']
    list_filter = ['forma_pagamento', 'empresa']
    search_fields = ['numero', 'cadastro__nome', 'descricao']
    readonly_fields = ['numero']
    inlines = [ServicoOrcamentoInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'afeta_caixa', 'ativo', 'ordem', 'empresa']
    list_filter = ['afeta_caixa', 'ativo', 'empresa']
    search_fields = ['nome']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)
