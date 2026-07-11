import json
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cadastros.models import Cadastro, CategoriaCliente

EMPRESA_ORIGEM = 2

print(f'Exportando clientes e categorias da empresa {EMPRESA_ORIGEM}...\n')

# Exportar categorias de clientes
categorias = CategoriaCliente.objects.filter(empresa_id=EMPRESA_ORIGEM)
categorias_data = [
    {
        "model": "cadastros.categoriacliente",
        "pk": obj.pk,
        "fields": {
            "empresa": obj.empresa_id,
            "nome": obj.nome
        }
    }
    for obj in categorias
]

print(f'Categorias exportadas: {len(categorias_data)}')
for cat in categorias_data:
    print(f"  - {cat['fields']['nome']}")

# Exportar clientes
clientes = Cadastro.objects.filter(empresa_id=EMPRESA_ORIGEM, papel='CLI')
clientes_data = [
    {
        "model": "cadastros.cadastro",
        "pk": obj.pk,
        "fields": {
            "empresa": obj.empresa_id,
            "papel": obj.papel,
            "categoria": obj.categoria_id,
            "tipo_pessoa": obj.tipo_pessoa,
            "nome": obj.nome,
            "razao_social": obj.razao_social,
            "cpf_cnpj": obj.cpf_cnpj,
            "rg": obj.rg,
            "inscricao_estadual": obj.inscricao_estadual,
            "is_produtor_rural": obj.is_produtor_rural,
            "num_registro": obj.num_registro,
            "data_nascimento": obj.data_nascimento.isoformat() if obj.data_nascimento else None,
            "email": obj.email,
            "celular": obj.celular,
            "telefone_fixo": obj.telefone_fixo,
            "cep": obj.cep,
            "endereco": obj.endereco,
            "bairro": obj.bairro,
            "cidade": obj.cidade,
            "uf": obj.uf,
            "situacao": obj.situacao,
            "foto": obj.foto.name if obj.foto else None,
            "observacoes": obj.observacoes
        }
    }
    for obj in clientes
]

print(f'Clientes exportados: {len(clientes_data)}')

# Salvar em arquivo
output_file = 'dados_clientes_empresa2.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(categorias_data + clientes_data, f, ensure_ascii=False, indent=2)

print(f'\n✓ Arquivo gerado: {output_file}')
print(f'Total de registros: {len(categorias_data) + len(clientes_data)}')
