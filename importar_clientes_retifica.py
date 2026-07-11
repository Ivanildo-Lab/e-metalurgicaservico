import csv
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from cadastros.models import Cadastro

EMPRESA_ID = 3
CSV_PATH = r'CLIENTES_RETIFICACENTRAL.txt'


def limpar_documento(doc):
    if not doc:
        return ''
    return doc.replace('.', '').replace('/', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').strip()


def gerar_documento_temporario(cod_cliente):
    """Gera um CPF/CNPJ temporário para clientes sem documento, usando o código do sistema antigo"""
    codigo = str(cod_cliente).zfill(10)
    return f'SN{codigo}'


def parse_data(data_str):
    if not data_str or data_str.strip() in ('', '0'):
        return None
    try:
        from datetime import datetime
        data_str = data_str.strip()
        for fmt in ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y']:
            try:
                return datetime.strptime(data_str, fmt).date()
            except ValueError:
                continue
        return None
    except Exception:
        return None


def parse_sexo(sexo_code):
    if not sexo_code:
        return ''
    sexo_code = str(sexo_code).strip()
    if sexo_code == '1':
        return 'M'
    elif sexo_code == '2':
        return 'F'
    return ''


def importar():
    criados = 0
    atualizados = 0
    pulados = 0
    erros = 0
    erros_lista = []

    if not os.path.exists(CSV_PATH):
        print(f'ERRO: Arquivo nao encontrado: {CSV_PATH}')
        return

    with open(CSV_PATH, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter=';')
        total = sum(1 for _ in open(CSV_PATH, 'r', encoding='latin-1')) - 1

    print(f'Total de registros no arquivo: {total}')
    print(f'Empresa destino: {EMPRESA_ID}')
    print()

    with open(CSV_PATH, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter=';')

        for i, row in enumerate(reader, 1):
            try:
                nome = row.get('nomecliente', '').strip()
                if not nome:
                    erros += 1
                    erros_lista.append(f"Linha {i}: nome vazio")
                    continue

                cpf_cnpj = limpar_documento(row.get('cpfcliente', ''))
                if not cpf_cnpj:
                    cpf_cnpj = limpar_documento(row.get('cgccliente', ''))

                # Se não tem CPF/CNPJ, gera um temporário com base no código do cliente
                if not cpf_cnpj:
                    cod_cliente = row.get('codcliente', '').strip()
                    if cod_cliente:
                        cpf_cnpj = gerar_documento_temporario(cod_cliente)
                    else:
                        erros += 1
                        erros_lista.append(f"Linha {i}: {nome} - sem CPF/CNPJ e sem código")
                        continue

                if row.get('cgccliente', '').strip():
                    tipo_pessoa = 'PJ'
                else:
                    tipo_pessoa = 'PF'

                # Verificar se é documento temporário
                eh_documento_temporario = cpf_cnpj.startswith('SN')

                existing = Cadastro.objects.filter(
                    empresa_id=EMPRESA_ID,
                    cpf_cnpj=cpf_cnpj
                ).first()

                telefone_raw = row.get('fonecliente', '').strip()
                fax_raw = row.get('faxcliente', '').strip()

                endereco = row.get('enderecocliente', '').strip()
                if endereco == '0':
                    endereco = ''

                bairro = row.get('bairrocliente', '').strip()
                if bairro == '0':
                    bairro = ''

                cep = row.get('cepcliente', '').strip()
                if cep == '0' or not cep:
                    cep = ''

                cidade = row.get('cidadecliente', '').strip()
                uf = row.get('estadocliente', '').strip()

                obs_parts = []
                if eh_documento_temporario:
                    obs_parts.append("ATENÇÃO: Cliente importado sem CPF/CNPJ. Documento temporário gerado pelo sistema.")
                contato = row.get('contato', '').strip()
                if contato and contato != '0':
                    obs_parts.append(f"Contato: {contato}")

                obs = row.get('obs', '').strip()
                if obs and obs != '0':
                    obs_parts.append(obs)

                referencia = row.get('referencia', '').strip()
                if referencia:
                    obs_parts.append(f"Ref: {referencia}")

                email = row.get('email', '').strip()
                if email == '0' or email == '1':
                    email = ''

                insc_est = row.get('insccliente', '').strip()
                if insc_est == '0':
                    insc_est = ''

                rg = row.get('rgcliente', '').strip()
                if rg == '0':
                    rg = ''

                cliente_inativo = row.get('clienteinativo', '').strip()
                situacao = 'INATIVO' if cliente_inativo == '1' else 'ATIVO'

                dados = {
                    'empresa_id': EMPRESA_ID,
                    'papel': 'CLI',
                    'tipo_pessoa': tipo_pessoa,
                    'nome': nome[:255],
                    'cpf_cnpj': cpf_cnpj,
                    'rg': rg[:20] or None,
                    'inscricao_estadual': insc_est[:20] or None,
                    'data_nascimento': parse_data(row.get('datanascimento', '')),
                    'email': email[:254] or None,
                    'celular': telefone_raw[:20] if telefone_raw and telefone_raw != '0' else '',
                    'telefone_fixo': fax_raw[:20] if fax_raw and fax_raw != '0' else '',
                    'cep': cep[:9],
                    'endereco': endereco[:255],
                    'bairro': bairro[:100],
                    'cidade': cidade[:100],
                    'uf': uf[:2],
                    'situacao': situacao,
                    'observacoes': '\n'.join(obs_parts)[:2000] if obs_parts else '',
                    'num_registro': int(row.get('codcliente', 0) or 0) or None,
                }

                if existing:
                    for key, value in dados.items():
                        if key != 'empresa_id':
                            setattr(existing, key, value)
                    existing.save()
                    atualizados += 1
                else:
                    Cadastro.objects.create(**dados)
                    criados += 1

                if i % 50 == 0:
                    print(f'  Processado {i}/{total}...')

            except Exception as e:
                erros += 1
                erros_lista.append(f"Linha {i}: {row.get('nomecliente', '?')} - {str(e)[:100]}")

    print()
    print('=' * 50)
    print('RESULTADO:')
    print(f'  Criados:     {criados}')
    print(f'  Atualizados: {atualizados}')
    print(f'  Erros:       {erros}')
    if erros_lista:
        print()
        print('Detalhes dos erros:')
        for e in erros_lista[:30]:
            print(f'  - {e}')
        if len(erros_lista) > 30:
            print(f'  ... e mais {len(erros_lista) - 30} erros')


if __name__ == '__main__':
    importar()
