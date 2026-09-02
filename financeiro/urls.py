from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # FLUXO
    path('fluxo/', views.fluxo_caixa, name='fluxo_caixa'),
     # CRUD DO FLUXO
    path('fluxo/novo/', views.novo_lancamento_manual, name='adicionar_lancamento'),
    path('fluxo/editar/<int:id>/', views.editar_lancamento, name='editar_lancamento'),
    path('fluxo/excluir/<int:id>/', views.excluir_lancamento, name='excluir_lancamento'),
    
    # RELATÓRIO
    path('fluxo/relatorio/', views.relatorio_fluxo, name='relatorio_fluxo'),
    path('contas/relatorio/', views.relatorio_contas, name='relatorio_contas'),
    path('contas/relatorio/sintetico/', views.relatorio_contas_sintetico, name='relatorio_contas_sintetico'),
    path('relatorios/dre/', views.relatorio_dre, name='relatorio_dre'),
    path('relatorios/dre/sintetico/', views.relatorio_dre_sintetico, name='relatorio_dre_sintetico'),
        
    # RECEBER (NOVO)
    path('contas/receber/', views.lista_contas_receber, name='lista_receber'),
    path('contas/receber/nova/', views.nova_receita, name='nova_receita'), # Atalho para criar
    
    # PAGAR (NOVO)
    path('contas/pagar/', views.lista_contas_pagar, name='lista_pagar'),
    path('contas/pagar/nova/', views.nova_despesa, name='nova_despesa'), # Atalho para criar

    # AÇÕES COMUNS (Editar/Baixar/Excluir servem para ambos)
    path('contas/baixar-lote/', views.baixar_contas_lote, name='baixar_contas_lote'),
    path('contas/baixar/<int:id>/', views.baixar_conta, name='baixar_conta'),
    path('contas/editar/<int:id>/', views.editar_conta, name='editar_conta'),
    path('contas/excluir/<int:id>/', views.excluir_conta, name='excluir_conta'),

    # CADASTROS AUXILIARES
    path('caixas/', views.lista_caixas, name='lista_caixas'),
    path('caixas/novo/', views.adicionar_caixa, name='adicionar_caixa'),
    path('caixas/editar/<int:id>/', views.editar_caixa, name='editar_caixa'),
    path('caixas/excluir/<int:id>/', views.excluir_caixa, name='excluir_caixa'),

    path('plano-de-contas/', views.lista_plano_de_contas, name='lista_plano_de_contas'),
    path('plano-de-contas/novo/', views.adicionar_plano_de_contas, name='adicionar_plano_de_contas'),
    path('plano-de-contas/editar/<int:id>/', views.editar_plano_de_contas, name='editar_plano_de_contas'),
    path('plano-de-contas/excluir/<int:id>/', views.excluir_plano_de_contas, name='excluir_plano_de_contas'),
]
