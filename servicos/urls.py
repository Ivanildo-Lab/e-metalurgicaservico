from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    # Funcionários
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/novo/', views.novo_funcionario, name='novo_funcionario'),
    path('funcionarios/editar/<int:id>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionarios/excluir/<int:id>/', views.excluir_funcionario, name='excluir_funcionario'),

    # Ordens de Serviço
    path('ordens/', views.lista_ordens, name='lista_ordens'),
    path('ordens/nova/', views.nova_os, name='nova_os'),
    path('ordens/<int:id>/', views.detalhe_os, name='detalhe_os'),
    path('ordens/editar/<int:id>/', views.editar_os, name='editar_os'),
    path('ordens/excluir/<int:id>/', views.excluir_os, name='excluir_os'),

    # Ações de status
    path('ordens/<int:id>/concluir/', views.concluir_os, name='concluir_os'),
    path('ordens/<int:id>/fechar/', views.fechar_os, name='fechar_os'),
    path('ordens/<int:id>/cancelar/', views.cancelar_os, name='cancelar_os'),

    # Serviços da OS (inline)
    path('ordens/<int:os_id>/servico/adicionar/', views.adicionar_servico_os, name='adicionar_servico_os'),
    path('ordens/servico/editar/<int:id>/', views.editar_servico_os, name='editar_servico_os'),
    path('ordens/servico/excluir/<int:id>/', views.excluir_servico_os, name='excluir_servico_os'),

    # Funcionários da OS (inline)
    path('ordens/<int:os_id>/funcionario/adicionar/', views.adicionar_funcionario_os, name='adicionar_funcionario_os'),
    path('ordens/funcionario/editar/<int:id>/', views.editar_funcionario_os, name='editar_funcionario_os'),
    path('ordens/funcionario/excluir/<int:id>/', views.excluir_funcionario_os, name='excluir_funcionario_os'),

    # Metas
    path('metas/', views.lista_metas, name='lista_metas'),
    path('metas/nova/', views.nova_meta, name='nova_meta'),
    path('metas/editar/<int:id>/', views.editar_meta, name='editar_meta'),
    path('metas/excluir/<int:id>/', views.excluir_meta, name='excluir_meta'),

    # Relatórios
    path('relatorios/mensal/<int:ano>/<int:mes>/', views.relatorio_mensal, name='relatorio_mensal'),
    path('relatorios/anual/<int:ano>/', views.relatorio_anual, name='relatorio_anual'),
]
