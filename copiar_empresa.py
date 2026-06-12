import json

# Mapeamento: empresa 1 -> empresa 2
arquivos = [
    'dados_empresa1.json',
    'dados_empresa1_planocontas.json',
    'dados_empresa1_caixas.json',
    'dados_empresa1_formaspagamento.json'
]

for arquivo in arquivos:
    try:
        # Tenta UTF-8 primeiro, senão usa latin-1
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except UnicodeDecodeError:
            with open(arquivo, 'r', encoding='latin-1') as f:
                data = json.load(f)
        
        for obj in data:
            if 'fields' in obj and 'empresa' in obj['fields']:
                obj['fields']['empresa'] = 2
            # Remove pk para evitar conflito
            obj['pk'] = None
        
        nome_saida = arquivo.replace('empresa1', 'empresa2')
        with open(nome_saida, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f'{arquivo} -> {nome_saida} ({len(data)} registros)')
    except FileNotFoundError:
        print(f'Arquivo nao encontrado: {arquivo}')

print('\nPronto! Faca upload dos arquivos *_empresa2.json para o PythonAnywhere')
