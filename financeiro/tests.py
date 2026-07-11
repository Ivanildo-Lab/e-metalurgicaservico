from datetime import date
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Empresa, Usuario, ParametroSistema
from financeiro.models import Caixa, Lancamento, PlanoDeContas


DATABASES_TEST = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PREFIX = '/financeiro'


def criar_empresa(nome='Empresa Teste'):
    return Empresa.objects.create(nome=nome, cnpj='00.000.000/0001-00')


def criar_usuario(empresa):
    user = Usuario.objects.create_user(
        username='admin', password='123456', empresa=empresa
    )
    for app_label in ['web', 'cadastros', 'financeiro', 'servicos', 'core']:
        ct = ContentType.objects.filter(app_label=app_label).first()
        if ct:
            perm = Permission.objects.filter(codename='acesso_modulo', content_type=ct).first()
            if perm:
                user.user_permissions.add(perm)
    return user


@override_settings(DATABASES=DATABASES_TEST)
class RelatorioFluxoTests(TestCase):

    def setUp(self):
        self.empresa = criar_empresa()
        self.user = criar_usuario(self.empresa)
        self.user.is_superuser = True
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password='123456')

        self.caixa = Caixa.objects.create(empresa=self.empresa, nome='Caixa Principal')
        self.plano = PlanoDeContas.objects.create(
            empresa=self.empresa, nome='Receita Serviços', tipo='R', codigo='4.01'
        )

    def test_relatorio_impressao_exibe_resumo_de_formas_de_pagamento(self):
        Lancamento.objects.create(
            empresa=self.empresa,
            caixa=self.caixa,
            plano_de_contas=self.plano,
            data_lancamento=date.today(),
            descricao='Recebimento OS 1001 — Dinheiro',
            valor=120,
            tipo='C',
        )
        Lancamento.objects.create(
            empresa=self.empresa,
            caixa=self.caixa,
            plano_de_contas=self.plano,
            data_lancamento=date.today(),
            descricao='Recebimento OS 1002 — PIX',
            valor=80,
            tipo='C',
        )

        response = self.client.get(
            f'{PREFIX}/fluxo/relatorio/',
            {'data_inicio': date.today().strftime('%Y-%m-%d'), 'data_fim': date.today().strftime('%Y-%m-%d')}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resumo de formas de pagamento')
        self.assertContains(response, 'Dinheiro')
        self.assertContains(response, 'PIX')
