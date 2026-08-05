import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from financeiro.models import Conta, PlanoDeContas
from cadastros.models import Cadastro

# Remover contas do plano "Receita de Servicos" (importacao legado)
contas = Conta.objects.filter(empresa_id=2, plano_de_contas__nome='Receita de Servicos')
print(f"Contas legado encontradas: {contas.count()}")
contas.delete()

# Remover cadastros placeholder (criados pela importacao)
cads = Cadastro.objects.filter(empresa_id=2, observacoes__icontains='importacao legado')
print(f"Cadastros placeholder encontrados: {cads.count()}")
cads.delete()

# Remover plano de contas se vazio
plano = PlanoDeContas.objects.filter(empresa_id=2, nome='Receita de Servicos')
if plano.exists():
    p = plano.first()
    if not Conta.objects.filter(plano_de_contas=p).exists():
        print(f"Removendo plano de contas vazio: {p}")
        p.delete()

print("Limpeza concluida.")
