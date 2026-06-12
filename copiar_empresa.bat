@echo off
REM ============================================
REM Copiar dados da empresa 1 para empresa 2
REM ============================================

echo.
echo Passo 1: Exportando dados da empresa 1...
echo.

python manage.py dumpdata core.parametrosistema --indent 2 -o dados_empresa1.json
python manage.py dumpdata financeiro.planodecontas --indent 2 -o dados_empresa1_planocontas.json
python manage.py dumpdata financeiro.caixa --indent 2 -o dados_empresa1_caixas.json
python manage.py dumpdata servicos.formapagamento --indent 2 -o dados_empresa1_formaspagamento.json

echo.
echo Passo 2: Copiando para empresa 2...
echo.

python copiar_empresa.py

echo.
pause
