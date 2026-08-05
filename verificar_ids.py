import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cadastros.models import Cadastro

ids_arquivo = set()
with open(r'C:\Users\ivcos\OneDrive\Documentos\Exportar_AReceber.txt', 'r', encoding='latin-1') as f:
    next(f)
    for linha in f:
        linha = linha.strip()
        if not linha:
            continue
        cod = linha.split(';')[0].strip().strip('"')
        if cod.isdigit():
            ids_arquivo.add(int(cod))

print(f"Ids unicos no arquivo: {len(ids_arquivo)}")

ids_banco = set(Cadastro.objects.filter(empresa_id=2).values_list('id', flat=True))
encontrados = ids_arquivo & ids_banco
nao_encontrados = ids_arquivo - ids_banco

print(f"No banco: {len(ids_banco)} cadastros")
print(f"Encontrados: {len(encontrados)}")
print(f"NAO encontrados: {len(nao_encontrados)}")
if nao_encontrados:
    print(f"Ids faltando: {sorted(nao_encontrados)}")
