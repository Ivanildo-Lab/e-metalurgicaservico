from datetime import date
from django.test import TestCase, Client, override_settings
from django.contrib.messages import get_messages
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Empresa, Usuario
from cadastros.models import Cadastro
from .models import (
    Funcionario, OrdemServico, FuncionarioOS,
    MetaFuncionario, FormaPagamento,
)
from financeiro.models import Caixa, Conta, Lancamento, PlanoDeContas
from core.models import ParametroSistema


DATABASES_TEST = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PREFIX = '/servicos'


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


def criar_cliente(empresa, nome='Cliente Teste', cpf='123.456.789-00'):
    return Cadastro.objects.create(
        empresa=empresa, nome=nome, cpf_cnpj=cpf,
        tipo_pessoa='PF', papel='CLI'
    )


def login_usuario(client, user):
    client.login(username=user.username, password='123456')


def get_messages_list(response):
    return list(get_messages(response.wsgi_request))


# ============================================================
# FORMA DE PAGAMENTO
# ============================================================
@override_settings(DATABASES=DATABASES_TEST)
class FormaPagamentoTests(TestCase):

    def setUp(self):
        self.empresa = criar_empresa()
        self.user = criar_usuario(self.empresa)
        self.client = Client()
        login_usuario(self.client, self.user)

    def test_criar_forma_pagamento(self):
        resp = self.client.post(f'{PREFIX}/formas-pagamento/nova/', {
            'nome': 'Dinheiro', 'ativo': True, 'ordem': 0,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(FormaPagamento.objects.filter(
            empresa=self.empresa, nome='Dinheiro'
        ).exists())

    def test_rejeitar_nome_duplicado(self):
        FormaPagamento.objects.create(
            empresa=self.empresa, nome='Prazo', ativo=True
        )
        resp = self.client.post(f'{PREFIX}/formas-pagamento/nova/', {
            'nome': 'Prazo', 'ativo': True, 'ordem': 0,
        })
        self.assertEqual(resp.status_code, 200)
        msgs = get_messages_list(resp)
        self.assertTrue(any('já existe' in str(m).lower() for m in msgs))
        self.assertEqual(FormaPagamento.objects.filter(
            empresa=self.empresa, nome='Prazo'
        ).count(), 1)

    def test_rejeitar_nome_duplicado_case_insensitive(self):
        FormaPagamento.objects.create(
            empresa=self.empresa, nome='PIX', ativo=True
        )
        resp = self.client.post(f'{PREFIX}/formas-pagamento/nova/', {
            'nome': 'pix', 'ativo': True, 'ordem': 0,
        })
        self.assertEqual(resp.status_code, 200)
        msgs = get_messages_list(resp)
        self.assertTrue(any('já existe' in str(m).lower() for m in msgs))

    def test_editar_manter_mesmo_nome(self):
        fp = FormaPagamento.objects.create(
            empresa=self.empresa, nome='Boleto', ativo=True
        )
        resp = self.client.post(
            f'{PREFIX}/formas-pagamento/editar/{fp.id}/', {
                'nome': 'Boleto', 'ativo': False, 'ordem': 1,
            }
        )
        self.assertEqual(resp.status_code, 302)
        fp.refresh_from_db()
        self.assertFalse(fp.ativo)

    def test_editar_rejeitar_nome_duplicado(self):
        FormaPagamento.objects.create(
            empresa=self.empresa, nome='Cartão', ativo=True
        )
        fp2 = FormaPagamento.objects.create(
            empresa=self.empresa, nome='Pix', ativo=True
        )
        resp = self.client.post(
            f'{PREFIX}/formas-pagamento/editar/{fp2.id}/', {
                'nome': 'Cartão', 'ativo': True, 'ordem': 0,
            }
        )
        self.assertEqual(resp.status_code, 200)
        msgs = get_messages_list(resp)
        self.assertTrue(any('já existe' in str(m).lower() for m in msgs))


# ============================================================
# FECHAMENTO DE OS COM MÚLTIPLAS FORMAS DE PAGAMENTO
# ============================================================
@override_settings(DATABASES=DATABASES_TEST)
class FechamentoOSTests(TestCase):

    def setUp(self):
        self.empresa = criar_empresa()
        self.user = criar_usuario(self.empresa)
        self.cliente = criar_cliente(self.empresa)
        self.client = Client()
        login_usuario(self.client, self.user)

        self.plano = PlanoDeContas.objects.create(
            empresa=self.empresa, nome='Receita Serviços', tipo='R', codigo='4.01'
        )
        ParametroSistema.objects.create(
            empresa=self.empresa, chave='PLANO_CONTAS_SERVICOS_ID', valor=str(self.plano.id)
        )
        self.caixa = Caixa.objects.create(empresa=self.empresa, nome='Caixa Principal')
        ParametroSistema.objects.create(
            empresa=self.empresa, chave='CAIXA_PADRAO_ID', valor=str(self.caixa.id)
        )

        self.funcionario = Funcionario.objects.create(empresa=self.empresa, nome='João')
        self.os = OrdemServico.objects.create(
            empresa=self.empresa, cadastro=self.cliente,
            descricao_geral='Peça teste', data_entrada=date.today(), status='CONCLUIDA'
        )
        self.servico = self.os.servicos.create(descricao='Serviço', valor=150)
        self.os.funcionarios.create(funcionario=self.funcionario, valor_remuneracao=150)

        self.forma_dinheiro = FormaPagamento.objects.create(
            empresa=self.empresa, nome='Dinheiro', afeta_caixa=True, ativo=True
        )
        self.forma_pix = FormaPagamento.objects.create(
            empresa=self.empresa, nome='PIX', afeta_caixa=True, ativo=True
        )

    def test_fechar_os_com_duas_formas_de_pagamento(self):
        resp = self.client.post(f'{PREFIX}/ordens/{self.os.id}/fechar/', {
            'forma_pagamento': 'A_VISTA',
            'pagamento_forma_id[]': [str(self.forma_dinheiro.id), str(self.forma_pix.id)],
            'pagamento_valor[]': ['100.00', '50.00'],
            'pagamento_caixa_id[]': [str(self.caixa.id), str(self.caixa.id)],
        })

        self.assertEqual(resp.status_code, 302)
        self.os.refresh_from_db()
        self.assertEqual(self.os.status, 'FECHADA')
        self.assertEqual(Lancamento.objects.filter(empresa=self.empresa, tipo='C').count(), 2)
        self.assertEqual(Conta.objects.filter(empresa=self.empresa).count(), 2)

    def test_impressao_exibe_historico_de_pagamentos(self):
        Lancamento.objects.create(
            empresa=self.empresa,
            caixa=self.caixa,
            plano_de_contas=self.plano,
            data_lancamento=date.today(),
            descricao=f'Recebimento OS {self.os.numero} — Dinheiro',
            valor=100,
            tipo='C',
        )
        Lancamento.objects.create(
            empresa=self.empresa,
            caixa=self.caixa,
            plano_de_contas=self.plano,
            data_lancamento=date.today(),
            descricao=f'Recebimento OS {self.os.numero} — PIX',
            valor=50,
            tipo='C',
        )

        resp = self.client.get(f'{PREFIX}/ordens/{self.os.id}/imprimir/')

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Dinheiro')
        self.assertContains(resp, 'PIX')

    def test_lista_ordens_exibe_modal_com_multiplas_formas_de_pagamento(self):
        resp = self.client.get(f'{PREFIX}/ordens/')

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'pagamento_forma_id[]')
        self.assertContains(resp, 'pagamento_valor[]')
        self.assertContains(resp, 'pagamento_caixa_id[]')
        self.assertContains(resp, 'inputmode="decimal"')

    def test_editar_os_exibe_input_editavel_de_valor_de_pagamento(self):
        resp = self.client.get(f'{PREFIX}/ordens/editar/{self.os.id}/')

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'pagamento_valor[]')
        self.assertContains(resp, 'inputmode="decimal"')


# ============================================================
# FUNCIONÁRIO
# ============================================================
@override_settings(DATABASES=DATABASES_TEST)
class FuncionarioTests(TestCase):

    def setUp(self):
        self.empresa = criar_empresa()
        self.user = criar_usuario(self.empresa)
        self.client = Client()
        login_usuario(self.client, self.user)

    def test_criar_funcionario(self):
        resp = self.client.post(f'{PREFIX}/funcionarios/novo/', {
            'nome': 'João', 'telefone': '', 'email': '',
            'ativo': True, 'observacoes': '',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Funcionario.objects.filter(
            empresa=self.empresa, nome='João'
        ).exists())

    def test_rejeitar_nome_duplicado(self):
        Funcionario.objects.create(empresa=self.empresa, nome='Carlos')
        resp = self.client.post(f'{PREFIX}/funcionarios/novo/', {
            'nome': 'Carlos', 'telefone': '', 'email': '',
            'ativo': True, 'observacoes': '',
        })
        self.assertEqual(resp.status_code, 200)
        msgs = get_messages_list(resp)
        self.assertTrue(any('já existe' in str(m).lower() for m in msgs))
        self.assertEqual(Funcionario.objects.filter(
            empresa=self.empresa, nome='Carlos'
        ).count(), 1)

    def test_rejeitar_nome_duplicado_case_insensitive(self):
        Funcionario.objects.create(empresa=self.empresa, nome='Pedro')
        resp = self.client.post(f'{PREFIX}/funcionarios/novo/', {
            'nome': 'PEDRO', 'telefone': '', 'email': '',
            'ativo': True, 'observacoes': '',
        })
        self.assertEqual(resp.status_code, 200)
        msgs = get_messages_list(resp)
        self.assertTrue(any('já existe' in str(m).lower() for m in msgs))

    def test_editar_manter_mesmo_nome(self):
        func = Funcionario.objects.create(
            empresa=self.empresa, nome='Ana'
        )
        resp = self.client.post(
            f'{PREFIX}/funcionarios/editar/{func.id}/', {
                'nome': 'Ana', 'telefone': '99999', 'email': '',
                'ativo': False, 'observacoes': '',
            }
        )
        self.assertEqual(resp.status_code, 302)
        func.refresh_from_db()
        self.assertFalse(func.ativo)

    def test_editar_rejeitar_nome_duplicado(self):
        Funcionario.objects.create(empresa=self.empresa, nome='Lucia')
        func2 = Funcionario.objects.create(
            empresa=self.empresa, nome='Maria'
        )
        resp = self.client.post(
            f'{PREFIX}/funcionarios/editar/{func2.id}/', {
                'nome': 'Lucia', 'telefone': '', 'email': '',
                'ativo': True, 'observacoes': '',
            }
        )
        self.assertEqual(resp.status_code, 200)
        msgs = get_messages_list(resp)
        self.assertTrue(any('já existe' in str(m).lower() for m in msgs))


# ============================================================
# FUNCIONÁRIO DA OS
# ============================================================
@override_settings(DATABASES=DATABASES_TEST)
class FuncionarioOSTests(TestCase):

    def setUp(self):
        self.empresa = criar_empresa()
        self.user = criar_usuario(self.empresa)
        self.cliente = criar_cliente(self.empresa)
        self.func1 = Funcionario.objects.create(
            empresa=self.empresa, nome='João'
        )
        self.func2 = Funcionario.objects.create(
            empresa=self.empresa, nome='Carlos'
        )
        self.os = OrdemServico.objects.create(
            empresa=self.empresa, cadastro=self.cliente,
            descricao_geral='Peça teste', data_entrada=date.today(),
            status='ABERTA',
        )
        self.client = Client()
        login_usuario(self.client, self.user)

    def test_adicionar_funcionario(self):
        resp = self.client.post(
            f'{PREFIX}/ordens/{self.os.id}/funcionario/adicionar/', {
                'funcionario': self.func1.id,
                'valor_remuneracao': '100.00',
            }
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(FuncionarioOS.objects.filter(
            ordem_servico=self.os, funcionario=self.func1
        ).exists())

    def test_rejeitar_funcionario_duplicado(self):
        FuncionarioOS.objects.create(
            ordem_servico=self.os, funcionario=self.func1,
            valor_remuneracao=100
        )
        resp = self.client.post(
            f'{PREFIX}/ordens/{self.os.id}/funcionario/adicionar/', {
                'funcionario': self.func1.id,
                'valor_remuneracao': '200.00',
            }
        )
        self.assertEqual(resp.status_code, 302)
        msgs = get_messages_list(resp)
        self.assertTrue(any(
            'já está vinculado' in str(m).lower() for m in msgs
        ))
        self.assertEqual(FuncionarioOS.objects.filter(
            ordem_servico=self.os, funcionario=self.func1
        ).count(), 1)

    def test_adicionar_funcionario_diferente(self):
        FuncionarioOS.objects.create(
            ordem_servico=self.os, funcionario=self.func1,
            valor_remuneracao=100
        )
        resp = self.client.post(
            f'{PREFIX}/ordens/{self.os.id}/funcionario/adicionar/', {
                'funcionario': self.func2.id,
                'valor_remuneracao': '200.00',
            }
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(FuncionarioOS.objects.filter(
            ordem_servico=self.os
        ).count(), 2)


# ============================================================
# META DO FUNCIONÁRIO
# ============================================================
@override_settings(DATABASES=DATABASES_TEST)
class MetaFuncionarioTests(TestCase):

    def setUp(self):
        self.empresa = criar_empresa()
        self.user = criar_usuario(self.empresa)
        self.func = Funcionario.objects.create(
            empresa=self.empresa, nome='Pedro'
        )
        self.client = Client()
        login_usuario(self.client, self.user)

    def test_editar_manter_mesma_meta(self):
        meta = MetaFuncionario.objects.create(
            empresa=self.empresa, funcionario=self.func,
            mes=1, ano=2026, meta_valor=5000
        )
        resp = self.client.post(f'{PREFIX}/metas/editar/{meta.id}/', {
            'funcionario': self.func.id,
            'mes': 1, 'ano': 2026,
            'meta_valor': '6000.00',
            'percentual_ruim': '90.0',
            'percentual_regular': '100.0',
            'percentual_bom': '120.0',
            'percentual_otimo': '140.0',
            'bonus_bom': '50.00',
            'bonus_otimo': '100.00',
            'bonus_excelente_percentual': '5.0',
        })
        self.assertEqual(resp.status_code, 302)
        meta.refresh_from_db()
        self.assertEqual(meta.meta_valor, 6000)

    def test_editar_rejeitar_duplicata(self):
        func2 = Funcionario.objects.create(
            empresa=self.empresa, nome='Ana'
        )
        MetaFuncionario.objects.create(
            empresa=self.empresa, funcionario=func2,
            mes=1, ano=2026, meta_valor=4000
        )
        meta2 = MetaFuncionario.objects.create(
            empresa=self.empresa, funcionario=self.func,
            mes=2, ano=2026, meta_valor=3000
        )
        resp = self.client.post(f'{PREFIX}/metas/editar/{meta2.id}/', {
            'funcionario': func2.id,
            'mes': 1, 'ano': 2026,
            'meta_valor': '3000.00',
            'percentual_ruim': '90.0',
            'percentual_regular': '100.0',
            'percentual_bom': '120.0',
            'percentual_otimo': '140.0',
            'bonus_bom': '50.00',
            'bonus_otimo': '100.00',
            'bonus_excelente_percentual': '5.0',
        })
        self.assertEqual(resp.status_code, 200)
        msgs = get_messages_list(resp)
        self.assertTrue(any('já existe' in str(m).lower() for m in msgs))
