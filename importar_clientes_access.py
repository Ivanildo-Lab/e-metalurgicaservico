import csv
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from cadastros.models import Cadastro, CategoriaCliente

EMPRESA_ID = 1
CSV_PATH = r'F:\HD 1tb\Dados\Projetos\Desnvolvimento com IA\clientes_access.csv'

def limpar_documento(doc):
    if not doc:
        return ''
    return doc.replace('.', '').replace('/', '').replace('-', '').replace(' ', '').strip()

def parse_data(data_str):
    if not data_str or data_str.strip() == '':
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

def importar():
    criados = 0
    atualizados = 0
    erros = 0
    erros_lista = []

    with open(CSV_PATH, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter=';')
        total = sum(1 for _ in open(CSV_PATH, 'r', encoding='latin-1')) - 1

    print(f'Total de registros no CSV: {total}')
    print()

    with open(CSV_PATH, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter=';')

        for i, row in enumerate(reader, 1):
            try:
                cpf_cnpj = limpar_documento(row.get('ccCGC', ''))
                if not cpf_cnpj:
                    cpf_cnpj = limpar_documento(row.get('ccCPF', ''))

                if not cpf_cnpj:
                    erros += 1
                    erros_lista.append(f"Linha {i}: {row.get('ccNomCli', '?')} - sem CPF/CNPJ")
                    continue

                # Determinar tipo pessoa
                if row.get('ccCGC', '').strip():
                    tipo_pessoa = 'PJ'
                else:
                    tipo_pessoa = 'PF'

                # Verificar se já existe
                existing = Cadastro.objects.filter(
                    empresa_id=EMPRESA_ID,
                    cpf_cnpj=cpf_cnpj
                ).first()

                # Montar endereco
                endereco_parts = []
                if row.get('ccEndereco', '').strip():
                    addr = row['ccEndereco'].strip()
                    numero = row.get('ccNumero', '').strip()
                    if numero and numero != '0':
                        addr += f', {numero}'
                    endereco_parts.append(addr)

                # Observacoes
                obs_parts = []
                if row.get('ccInfCom', '').strip():
                    obs_parts.append(row['ccInfCom'].strip())
                if row.get('ccExtras', '').strip():
                    obs_parts.append(row['ccExtras'].strip())

                # Status
                situacao = 'ATIVO'
                if row.get('ccBloqueio', '').strip() == '1':
                    situacao = 'INATIVO'
                elif row.get('ccAtivo', '').strip() == '0':
                    situacao = 'INATIVO'

                dados = {
                    'empresa_id': EMPRESA_ID,
                    'papel': 'CLI',
                    'tipo_pessoa': tipo_pessoa,
                    'nome': row.get('ccNomCli', '').strip()[:255],
                    'razao_social': row.get('ccNomFan', '').strip()[:255] or None,
                    'cpf_cnpj': cpf_cnpj,
                    'rg': row.get('ccRG', '').strip()[:20] or None,
                    'inscricao_estadual': row.get('ccInsEst', '').strip()[:20] or None,
                    'data_nascimento': parse_data(row.get('cdDatNasc', '')),
                    'email': row.get('ccEmail', '').strip()[:254] or None,
                    'celular': row.get('ccCelular', '').strip()[:20] or '',
                    'telefone_fixo': row.get('ccTelefone', '').strip()[:20] or '',
                    'cep': row.get('ccCep', '').strip()[:9] or '',
                    'endereco': endereco_parts[0][:255] if endereco_parts else '',
                    'bairro': row.get('ccBairro', '').strip()[:100] or '',
                    'cidade': row.get('ccCidade', '').strip()[:100] or '',
                    'uf': row.get('ccEstado', '').strip()[:2] or '',
                    'situacao': situacao,
                    'observacoes': '\n'.join(obs_parts)[:2000] if obs_parts else '',
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

                if i % 100 == 0:
                    print(f'  Processado {i}/{total}...')

            except Exception as e:
                erros += 1
                erros_lista.append(f"Linha {i}: {row.get('ccNomCli', '?')} - {str(e)[:100]}")

    print()
    print('='*50)
    print(f'RESULTADO:')
    print(f'  Criados:     {criados}')
    print(f'  Atualizados: {atualizados}')
    print(f'  Erros:       {erros}')
    if erros_lista:
        print()
        print('Detalhes dos erros:')
        for e in erros_lista[:20]:
            print(f'  - {e}')
        if len(erros_lista) > 20:
            print(f'  ... e mais {len(erros_lista) - 20} erros')

if __name__ == '__main__':
    importar()
