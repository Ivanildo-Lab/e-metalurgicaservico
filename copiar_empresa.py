#!/usr/bin/env python3
import json
import argparse
import subprocess
from pathlib import Path


def process_file(path: Path, target_empresa: int) -> Path:
    try:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except UnicodeDecodeError:
            data = json.loads(path.read_text(encoding='latin-1'))
    except FileNotFoundError:
        print(f'Arquivo nao encontrado: {path.name}')
        return None

    for obj in data:
        if isinstance(obj, dict) and 'fields' in obj and isinstance(obj['fields'], dict) and 'empresa' in obj['fields']:
            obj['fields']['empresa'] = target_empresa
        obj['pk'] = None

    return data


def main():
    parser = argparse.ArgumentParser(description='Gerar fixtures para outra empresa (altera campo empresa e remove pk)')
    parser.add_argument('--source', '-s', type=int, default=2, help='ID da empresa fonte (default: 2)')
    parser.add_argument('--target', '-t', type=int, required=True, help='ID da empresa destino')
    parser.add_argument('--apply-local', action='store_true', help='Executar loaddata localmente após gerar os arquivos')
    parser.add_argument('--out-dir', default='.', help='Diretorio de saida (default: current)')
    args = parser.parse_args()

    root = Path(args.out_dir)
    suffixes = ['', '_planocontas', '_caixas', '_formaspagamento']
    generated = []

    for suf in suffixes:
        src_name = f'dados_empresa{args.source}{suf}.json'
        src_path = root / src_name
        data = process_file(src_path, args.target)
        if data is None:
            continue
        out_name = f'dados_empresa{args.target}{suf}.json'
        out_path = root / out_name
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        generated.append(out_path)
        print(f'Gerado {out_name} com {len(data)} registros')

    if not generated:
        print('Nenhum arquivo gerado.')
        return

    print('\nArquivos gerados:')
    for p in generated:
        print(' -', p)

    print('\nPara importar no servidor, copie os arquivos acima para a raiz do projeto Django e execute:')
    for p in generated:
        print(f'  python manage.py loaddata {p.name}')

    if args.apply_local:
        print('\nExecutando loaddata localmente (faça backup antes)!')
        for p in generated:
            try:
                subprocess.check_call(['python', 'manage.py', 'loaddata', str(p)])
                print(f'Importado {p.name} localmente')
            except subprocess.CalledProcessError as e:
                print(f'Erro ao importar {p.name}:', e)


if __name__ == '__main__':
    main()
