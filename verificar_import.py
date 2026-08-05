import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from financeiro.models import Conta
from cadastros.models import Cadastro
from django.db.models import Sum

total = Conta.objects.filter(empresa_id=2, plano_de_contas__nome='Receita de Servicos').count()
pagas = Conta.objects.filter(empresa_id=2, plano_de_contas__nome='Receita de Servicos', status='PAGA').count()
pendentes = Conta.objects.filter(empresa_id=2, plano_de_contas__nome='Receita de Servicos', status='PENDENTE').count()
valor_total = Conta.objects.filter(empresa_id=2, plano_de_contas__nome='Receita de Servicos').aggregate(Sum('valor'))['valor__sum']
cadastros = Cadastro.objects.filter(empresa_id=2, observacoes__icontains='importacao legado').count()

print(f"Contas: {total}")
print(f"  Pagas: {pagas}")
print(f"  Pendentes: {pendentes}")
print(f"  Valor total: R$ {valor_total:,.2f}")
print(f"Cadastros placeholder: {cadastros}")

print()
print("Amostra de contas com cliente:")
amostra = Conta.objects.filter(empresa_id=2, plano_de_contas__nome='Receita de Servicos').select_related('cadastro')[:5]
for c in amostra:
    print(f"  id={c.id} cliente_id={c.cadastro.id} cliente={c.cadastro.nome[:30]} doc={c.documento} valor={c.valor} status={c.status}")
