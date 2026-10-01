import csv
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from cadastros.models import Cadastro


def limpar_documento(doc):
    if not doc:
        return ''
    return doc.replace('.', '').replace('/', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').strip()


def gerar_documento_temporario(cod_cliente):
    codigo = str(cod_cliente).zfill(10)
    return f'SN{codigo}'


def parse_data(data_str):
    if not data_str or data_str.strip() in ('', '0'):
        return None
    data_str = data_str.strip()
    for fmt in ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y']:
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            continue
    return None


class Command(BaseCommand):
    help = 'Importa clientes do export legado Access (ExportarClientes_empresa_N.txt)'

    def add_arguments(self, parser):
        parser.add_argument('--arquivo', required=True, help='Caminho do arquivo .txt exportado do Access')
        parser.add_argument('--empresa', required=True, type=int, help='ID da empresa destino (core_empresa.id)')
        parser.add_argument('--dry-run', action='store_true', help='Simula sem gravar no banco')

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        empresa_id = options['empresa']
        dry_run = options['dry_run']

        try:
            import os
            if not os.path.exists(arquivo):
                raise CommandError(f'Arquivo nao encontrado: {arquivo}')
        except CommandError:
            raise
        except Exception as e:
            raise CommandError(str(e))

        criados = 0
        atualizados = 0
        sem_documento = 0
        erros = 0
        erros_lista = []
        cache_nome = {}

        with open(arquivo, 'r', encoding='latin-1') as f:
            total = sum(1 for _ in f) - 1

        self.stdout.write(f'Total de registros no arquivo: {total}')
        self.stdout.write(f'Empresa destino: {empresa_id}')
        self.stdout.write(f'Modo: {"DRY-RUN (sem gravar)" if dry_run else "GRAVACAO REAL"}')
        self.stdout.write('')

        with open(arquivo, 'r', encoding='latin-1') as f:
            reader = csv.DictReader(f, delimiter=';')

            for i, row in enumerate(reader, 1):
                try:
                    nome = (row.get('ccNomCli') or row.get('NomeRazao') or '').strip()
                    if not nome:
                        erros += 1
                        erros_lista.append(f'Linha {i}: nome vazio')
                        continue

                    cgc_raw = (row.get('ccCGC') or '').strip()
                    cpf_raw = (row.get('ccCPF') or '').strip()
                    cpf_cnpj = limpar_documento(cgc_raw) or limpar_documento(cpf_raw)

                    cod_cli = (row.get('CODCLI') or '').strip()
                    eh_temporario = False
                    if not cpf_cnpj:
                        if cod_cli:
                            cpf_cnpj = gerar_documento_temporario(cod_cli)
                            eh_temporario = True
                            sem_documento += 1
                        else:
                            erros += 1
                            erros_lista.append(f'Linha {i}: {nome} - sem CPF/CNPJ e sem CODCLI')
                            continue

                    tipo_pessoa = 'PJ' if cgc_raw else 'PF'

                    # Busca APENAS por NOME - ID legado (CODCLI) desconsiderado,
                    # pois nao corresponde aos IDs do servidor
                    nome_key = nome.lower()
                    existing = cache_nome.get(nome_key)
                    if existing is None:
                        existing = Cadastro.objects.filter(empresa_id=empresa_id, nome__iexact=nome).first()
                        cache_nome[nome_key] = existing

                    endereco = (row.get('ccEndereco') or '').strip()
                    if endereco == '0':
                        endereco = ''
                    numero = (row.get('ccNumero') or '').strip()
                    if numero and numero != '0':
                        endereco = f'{endereco}, {numero}' if endereco else numero

                    bairro = (row.get('ccBairro') or '').strip()
                    if bairro == '0':
                        bairro = ''
                    cep = (row.get('ccCep') or '').strip()
                    if cep in ('0', ''):
                        cep = ''
                    cidade = (row.get('ccCidade') or '').strip()
                    uf = (row.get('ccEstado') or '').strip()

                    obs_parts = []
                    if eh_temporario:
                        obs_parts.append('ATENCAO: Cliente importado sem CPF/CNPJ. Documento temporario gerado pelo sistema.')
                    if cod_cli:
                        obs_parts.append(f'CODCLI legado (sem correspondencia de ID): {cod_cli}')
                    for campo in ('ccInfCom', 'ccExtras', 'ccMensagem'):
                        valor = (row.get(campo) or '').strip()
                        if valor and valor not in ('0', '1'):
                            obs_parts.append(valor)

                    situacao = 'ATIVO'
                    if (row.get('ccBloqueio') or '').strip() == '1' or (row.get('ccAtivo') or '').strip() == '0':
                        situacao = 'INATIVO'

                    email = (row.get('ccEmail') or '').strip()
                    if email in ('0', '1'):
                        email = ''
                    celular = (row.get('ccCelular') or '').strip()
                    if celular == '0':
                        celular = ''
                    telefone = (row.get('ccTelefone') or '').strip()
                    if telefone == '0':
                        telefone = ''
                    rg = (row.get('ccRG') or '').strip()
                    if rg == '0':
                        rg = ''
                    insc_est = (row.get('ccInsEst') or '').strip()
                    if insc_est == '0':
                        insc_est = ''

                    dados = {
                        'empresa_id': empresa_id,
                        'papel': 'CLI',
                        'tipo_pessoa': tipo_pessoa,
                        'nome': nome[:255],
                        'razao_social': (row.get('ccNomFan') or '').strip()[:255] or None,
                        'cpf_cnpj': cpf_cnpj,
                        'rg': rg[:20] or None,
                        'inscricao_estadual': insc_est[:20] or None,
                        'data_nascimento': parse_data(row.get('cdDatNasc', '')),
                        'email': email[:254] or None,
                        'celular': celular[:20],
                        'telefone_fixo': telefone[:20],
                        'cep': cep[:9],
                        'endereco': endereco[:255],
                        'bairro': bairro[:100],
                        'cidade': cidade[:100],
                        'uf': uf[:2],
                        'situacao': situacao,
                        'observacoes': '\n'.join(obs_parts)[:2000] if obs_parts else '',
                    }

                    if existing:
                        if dry_run:
                            self.stdout.write(
                                f'[ATUALIZAR por NOME] "{nome}" == cadastro servidor id {existing.id} '
                                f'(nome no servidor: "{existing.nome}")'
                            )
                        else:
                            for key, value in dados.items():
                                if key != 'empresa_id':
                                    setattr(existing, key, value)
                            existing.save()
                        atualizados += 1
                        cache_nome[nome_key] = existing
                    else:
                        if dry_run:
                            self.stdout.write(f'[CRIAR] {nome} (doc={cpf_cnpj})')
                        else:
                            novo = Cadastro.objects.create(**dados)
                            cache_nome[nome_key] = novo
                        criados += 1

                    if i % 100 == 0:
                        self.stdout.write(f'  Processado {i}/{total}...')

                except Exception as e:
                    erros += 1
                    erros_lista.append(f'Linha {i}: {(row.get("ccNomCli") or "?")} - {str(e)[:100]}')

        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write('RESULTADO:')
        self.stdout.write(f'  Criados:     {criados}')
        self.stdout.write(f'  Atualizados: {atualizados}')
        if sem_documento:
            self.stdout.write(f'  Doc temporario (sem CPF/CNPJ): {sem_documento}')
        self.stdout.write(f'  Erros:       {erros}')
        if erros_lista:
            self.stdout.write('')
            self.stdout.write('Detalhes dos erros:')
            for e in erros_lista[:30]:
                self.stdout.write(f'  - {e}')
            if len(erros_lista) > 30:
                self.stdout.write(f'  ... e mais {len(erros_lista) - 30} erros')
        if dry_run:
            self.stdout.write('')
            self.stdout.write('[AVISO] DRY-RUN: Nenhum dado foi gravado no banco.')
