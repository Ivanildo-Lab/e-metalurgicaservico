from django.contrib import admin
from .models import PlanoDeContas, Caixa, Conta, Lancamento


@admin.register(PlanoDeContas)
class PlanoDeContasAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'tipo', 'empresa')
    list_filter = ('tipo', 'empresa')
    search_fields = ('codigo', 'nome')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)


@admin.register(Caixa)
class CaixaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'saldo_inicial', 'empresa')
    list_filter = ('empresa',)
    search_fields = ('nome',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data_vencimento', 'status', 'empresa')
    list_filter = ('status', 'empresa')
    search_fields = ('descricao', 'documento')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ('data_lancamento', 'descricao', 'valor', 'tipo', 'caixa', 'empresa')
    list_filter = ('tipo', 'empresa')
    search_fields = ('descricao',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)
