import json
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cadastros.models import Cadastro, CategoriaCliente

EMPRESA_ORIGEM = 1
EMPRESA_DESTINO = 2

print(f'Copiando clientes da empresa {EMPRESA_ORIGEM} para {EMPRESA_DESTINO}...\n')

# Mapeamento de categorias (origem -> destino)
categoria_map = {}

print('1. Copiando categorias de clientes...')
for categoria_origem in CategoriaCliente.objects.filter(empresa_id=EMPRESA_ORIGEM):
    # Verifica se categoria já existe na empresa destino
    categoria_destino = CategoriaCliente.objects.filter(
        empresa_id=EMPRESA_DESTINO,
        nome=categoria_origem.nome
    ).first()
    
    if categoria_destino:
        categoria_map[categoria_origem.pk] = categoria_destino.pk
        print(f'  ✓ Categoria existente: {categoria_origem.nome} (ID: {categoria_destino.pk})')
    else:
        # Cria nova categoria
        novo_cat = CategoriaCliente.objects.create(
            empresa_id=EMPRESA_DESTINO,
            nome=categoria_origem.nome
        )
        categoria_map[categoria_origem.pk] = novo_cat.pk
        print(f'  ✓ Categoria criada: {categoria_origem.nome} (ID: {novo_cat.pk})')

print(f'\n2. Copiando clientes...')
clientes_copiados = 0

for cliente_origem in Cadastro.objects.filter(empresa_id=EMPRESA_ORIGEM, papel='CLI'):
    # Verifica se cliente já existe na empresa destino
    cliente_existente = Cadastro.objects.filter(
        empresa_id=EMPRESA_DESTINO,
        cpf_cnpj=cliente_origem.cpf_cnpj
    ).first()
    
    if cliente_existente:
        print(f'  ⚠ Cliente já existe: {cliente_origem.nome} (CPF/CNPJ: {cliente_origem.cpf_cnpj})')
        continue
    
    # Copiar cliente
    novo_cliente = Cadastro.objects.create(
        empresa_id=EMPRESA_DESTINO,
        papel=cliente_origem.papel,
        categoria_id=categoria_map.get(cliente_origem.categoria_id) if cliente_origem.categoria_id else None,
        tipo_pessoa=cliente_origem.tipo_pessoa,
        nome=cliente_origem.nome,
        razao_social=cliente_origem.razao_social,
        cpf_cnpj=cliente_origem.cpf_cnpj,
        rg=cliente_origem.rg,
        inscricao_estadual=cliente_origem.inscricao_estadual,
        is_produtor_rural=cliente_origem.is_produtor_rural,
        num_registro=cliente_origem.num_registro,
        data_nascimento=cliente_origem.data_nascimento,
        email=cliente_origem.email,
        celular=cliente_origem.celular,
        telefone_fixo=cliente_origem.telefone_fixo,
        cep=cliente_origem.cep,
        endereco=cliente_origem.endereco,
        bairro=cliente_origem.bairro,
        cidade=cliente_origem.cidade,
        uf=cliente_origem.uf,
        situacao=cliente_origem.situacao,
        observacoes=cliente_origem.observacoes
    )
    
    print(f'  ✓ {novo_cliente.nome}')
    clientes_copiados += 1

print(f'\n✓ Processo concluído!')
print(f'  - Clientes copiados: {clientes_copiados}')
print(f'  - Categorias criadas/mapeadas: {len(categoria_map)}')
