import json
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.models import ParametroSistema
from financeiro.models import PlanoDeContas, Caixa
from servicos.models import FormaPagamento

EMPRESA_ORIGEM = 1
EMPRESA_DESTINO = 2

print(f'Limpando dados da empresa {EMPRESA_DESTINO}...')

# Limpar dados existentes da empresa destino
ParametroSistema.objects.filter(empresa_id=EMPRESA_DESTINO).delete()
PlanoDeContas.objects.filter(empresa_id=EMPRESA_DESTINO).delete()
Caixa.objects.filter(empresa_id=EMPRESA_DESTINO).delete()
FormaPagamento.objects.filter(empresa_id=EMPRESA_DESTINO).delete()

print('Dados antigos removidos!')

# Agora copia os dados
print(f'\nCopiando dados da empresa {EMPRESA_ORIGEM} para {EMPRESA_DESTINO}...')

# Parametros
for obj in ParametroSistema.objects.filter(empresa_id=EMPRESA_ORIGEM):
    obj.pk = None
    obj.empresa_id = EMPRESA_DESTINO
    obj.save()
    print(f'  Parametro: {obj.chave} = {obj.valor}')

# Plano de Contas
for obj in PlanoDeContas.objects.filter(empresa_id=EMPRESA_ORIGEM):
    obj.pk = None
    obj.empresa_id = EMPRESA_DESTINO
    obj.save()
    print(f'  Plano de Contas: {obj.nome}')

# Caixas
for obj in Caixa.objects.filter(empresa_id=EMPRESA_ORIGEM):
    obj.pk = None
    obj.empresa_id = EMPRESA_DESTINO
    obj.save()
    print(f'  Caixa: {obj.nome}')

# Formas de Pagamento
for obj in FormaPagamento.objects.filter(empresa_id=EMPRESA_ORIGEM):
    obj.pk = None
    obj.empresa_id = EMPRESA_DESTINO
    obj.save()
    print(f'  Forma Pagamento: {obj.nome}')

print('\nPronto! Todos os dados foram copiados para a empresa 2.')
