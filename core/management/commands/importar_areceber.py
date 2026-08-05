import csv
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Empresa
from cadastros.models import Cadastro
from financeiro.models import Conta, PlanoDeContas


class Command(BaseCommand):
    help = 'Importa contas a receber de arquivo legado (Exportar_AReceber.txt)'

    def add_arguments(self, parser):
        parser.add_argument('--arquivo', type=str, required=True, help='Caminho do arquivo .txt')
        parser.add_argument('--empresa', type=int, required=True, help='ID da empresa')
        parser.add_argument('--dry-run', action='store_true', help='Simula sem gravar no banco')

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        empresa_id = options['empresa']
        dry_run = options['dry_run']

        try:
            empresa = Empresa.objects.get(id=empresa_id)
        except Empresa.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Empresa com id={empresa_id} não encontrada'))
            return

        if not os.path.exists(arquivo):
            self.stderr.write(self.style.ERROR(f'Arquivo não encontrado: {arquivo}'))
            return

        plano, _ = PlanoDeContas.objects.get_or_create(
            empresa=empresa,
            nome='Receita de Serviços',
            defaults={'tipo': 'R', 'codigo': '1.01'}
        )

        contas_criadas = 0
        cadastros_encontrados = 0
        cadastros_criados = 0
        erros = 0
        erros_detalhe = []

        with open(arquivo, 'r', encoding='latin-1') as f:
            linhas = f.readlines()

        total = len(linhas) - 1

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'  IMPORTAÇÃO DE CONTAS A RECEBER - LEGADO')
        self.stdout.write(f'  Empresa: {empresa.nome} (id={empresa_id})')
        self.stdout.write(f'  Arquivo: {arquivo}')
        self.stdout.write(f'  Total de registros: {total}')
        self.stdout.write(f'  Modo: {"DRY-RUN (sem gravar)" if dry_run else "IMPORTAÇÃO REAL"}')
        self.stdout.write(f'{"="*60}\n')

        cadastros_cache = {}

        for i, linha in enumerate(linhas[1:], start=1):
            linha = linha.strip()
            if not linha:
                continue

            try:
                campos = linha.split(';')
                if len(campos) < 7:
                    erros += 1
                    erros_detalhe.append(f'Linha {i}: número insuficiente de colunas ({len(campos)})')
                    continue

                cod_cli = campos[0].strip().strip('"')
                num_doc = campos[1].strip().strip('"')
                numero_os = campos[2].strip().strip('"')
                num_dup = campos[3].strip().strip('"')
                dat_lan = campos[4].strip().strip('"')
                dat_ven = campos[5].strip().strip('"')
                valor_par = campos[6].strip().strip('"')

                cadastro = None
                if cod_cli:
                    if cod_cli in cadastros_cache:
                        cadastro = cadastros_cache[cod_cli]
                    else:
                        try:
                            cadastro = Cadastro.objects.get(
                                empresa=empresa,
                                num_registro=int(cod_cli)
                            )
                            cadastros_encontrados += 1
                        except (Cadastro.DoesNotExist, ValueError):
                            cadastro = Cadastro(
                                empresa=empresa,
                                nome=f'Cliente Legado {cod_cli}',
                                cpf_cnpj='000.000.000-00',
                                num_registro=int(cod_cli) if cod_cli.isdigit() else None,
                                papel='CLI',
                                tipo_pessoa='PF',
                                situacao='ATIVO',
                                observacoes=f'Cadastro criado automaticamente na importação legado. CODCLI={cod_cli}'
                            )
                            if not dry_run:
                                cadastro.save()
                            cadastros_criados += 1
                        except Exception as e:
                            erros += 1
                            erros_detalhe.append(f'Linha {i}: erro ao buscar cadastro CODCLI={cod_cli}: {e}')
                            continue
                        cadastros_cache[cod_cli] = cadastro

                valor = self.parse_valor(valor_par)
                if valor is None:
                    erros += 1
                    erros_detalhe.append(f'Linha {i}: valor inválido "{valor_par}"')
                    continue

                data_vencimento = self.parse_data(dat_ven)
                if data_vencimento is None:
                    erros += 1
                    erros_detalhe.append(f'Linha {i}: data de vencimento inválida "{dat_ven}"')
                    continue

                pago = bool(dat_lan and dat_lan.strip())
                status = 'PAGA' if pago else 'PENDENTE'
                valor_pago = valor if pago else Decimal('0.00')

                obs = f'OS: {numero_os}' if numero_os else ''

                if not dry_run:
                    conta = Conta(
                        empresa=empresa,
                        descricao=num_doc or f'Conta Legado {cod_cli}',
                        plano_de_contas=plano,
                        cadastro=cadastro,
                        valor=valor,
                        valor_pago=valor_pago,
                        data_vencimento=data_vencimento,
                        status=status,
                        documento=num_doc,
                        observacoes=obs
                    )
                    conta.save()

                contas_criadas += 1

                if contas_criadas % 50 == 0:
                    self.stdout.write(f'  Processadas {contas_criadas}/{total} linhas...')

            except Exception as e:
                erros += 1
                erros_detalhe.append(f'Linha {i}: erro inesperado: {e}')

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS(f'  RESUMO DA IMPORTAÇÃO'))
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'  Total de registros no arquivo: {total}')
        self.stdout.write(self.style.SUCCESS(f'  Contas criadas:              {contas_criadas}'))
        self.stdout.write(f'  Cadastros encontrados:        {cadastros_encontrados}')
        self.stdout.write(self.style.WARNING(f'  Cadastros criados (placeholder): {cadastros_criados}'))
        if erros:
            self.stdout.write(self.style.ERROR(f'  Erros:                        {erros}'))
        else:
            self.stdout.write(f'  Erros:                        0')
        self.stdout.write(f'{"="*60}')

        if erros_detalhe:
            self.stdout.write(f'\n{self.style.ERROR("  DETALHE DOS ERROS:")}')
            for erro in erros_detalhe[:20]:
                self.stdout.write(f'    - {erro}')
            if len(erros_detalhe) > 20:
                self.stdout.write(f'    ... e mais {len(erros_detalhe) - 20} erros')

        if dry_run:
            self.stdout.write(f'\n{self.style.WARNING("  [AVISO] DRY-RUN: Nenhum dado foi gravado no banco.")}')
            self.stdout.write(f'  Para importar de verdade, rode sem a flag --dry-run')

    def parse_valor(self, valor_str):
        if not valor_str:
            return None
        try:
            valor_str = valor_str.replace('R$', '').replace(' ', '').strip()
            valor_str = valor_str.replace('.', '').replace(',', '.')
            return Decimal(valor_str)
        except (InvalidOperation, ValueError):
            return None

    def parse_data(self, data_str):
        if not data_str or not data_str.strip():
            return None
        try:
            data_str = data_str.strip()
            for fmt in ('%d/%m/%Y %H:%M:%S', '%d/%m/%Y'):
                try:
                    return datetime.strptime(data_str, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None
