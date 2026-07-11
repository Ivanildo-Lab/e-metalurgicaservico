# Exportar/Copiar Clientes para Empresa 2

Existem **3 formas** de exportar seus clientes para a empresa 2:

---

## ✅ **Opção 1: Script Interativo (RECOMENDADO)**

Execute o arquivo batch que facilita tudo:

```bash
copiar_clientes.bat
```

Escolha uma das opções:
- **1**: Exportar clientes da empresa 1 para arquivo JSON
- **2**: Copiar clientes direto no banco (empresa 1 → empresa 2)
- **3**: Fazer ambos

---

## 📋 **Opção 2: Copiar Direto no Banco (Mais Rápido)**

Se você quer copiar os clientes direto no banco de dados:

```bash
python copiar_clientes_empresa.py
```

**O que faz:**
- Copia todas as categorias de clientes
- Copia todos os clientes
- Não duplica se já existir (verifica por CPF/CNPJ)
- Mostra o progresso durante a execução

---

## 📁 **Opção 3: Exportar para JSON (Para Backup/Compartilhamento)**

Se você quer gerar um arquivo JSON:

```bash
python exportar_clientes_empresa1.py
```

**Gera:**
- `dados_clientes_empresa1.json` (com todas as categorias e clientes)

**Uso posterior:**
Carregue no banco com Django:
```bash
python manage.py loaddata dados_clientes_empresa1.json
```

---

## 🔄 **Comandos Django Equivalentes**

Se preferir fazer manualmente:

### Exportar (Empresa 1)
```bash
python manage.py dumpdata cadastros --indent 2 -o dados_clientes_empresa1.json
```

### Importar (Empresa 2)
```bash
python manage.py loaddata dados_clientes_empresa1.json
```

---

## ⚠️ **Observações Importantes**

1. **Categorias**: Se a categoria já existir na empresa 2, não será duplicada
2. **CPF/CNPJ**: Se o cliente já existe na empresa 2, será pulado
3. **Banco de dados**: Faça backup antes de executar!
4. **Ambiente Django**: Os scripts precisam do Django ativo (venv)

---

## 🆘 **Troubleshooting**

**"ModuleNotFoundError: No module named 'django'"**
- Ative o ambiente virtual: `venv\Scripts\activate`

**"ERROR: App 'cadastros' doesn't have a 'CategoriaCliente' model"**
- Execute as migrações: `python manage.py migrate`

**"Client already exists"**
- Normal! Significa que o cliente já estava importado
