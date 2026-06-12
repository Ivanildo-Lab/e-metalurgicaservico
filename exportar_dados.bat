@echo off
REM ============================================
REM Exportar dados para migrar para PythonAnywhere
REM ============================================

echo.
echo Exportando dados do banco local...
echo.

python manage.py dumpdata core.parametrosistema --indent 2 -o dados_parametros.json
python manage.py dumpdata financeiro.planodecontas --indent 2 -o dados_planocontas.json
python manage.py dumpdata financeiro.caixa --indent 2 -o dados_caixas.json
python manage.py dumpdata servicos.formapagamento --indent 2 -o dados_formaspagamento.json

echo.
echo Convertendo para UTF-8 (sem BOM)...
echo.

powershell -Command "[System.IO.File]::WriteAllText('dados_parametros_utf8.json', [System.IO.File]::ReadAllText('dados_parametros.json', [System.Text.Encoding]::Default), [System.Text.UTF8Encoding]::new($false))"
powershell -Command "[System.IO.File]::WriteAllText('dados_planocontas_utf8.json', [System.IO.File]::ReadAllText('dados_planocontas.json', [System.Text.Encoding]::Default), [System.Text.UTF8Encoding]::new($false))"
powershell -Command "[System.IO.File]::WriteAllText('dados_caixas_utf8.json', [System.IO.File]::ReadAllText('dados_caixas.json', [System.Text.Encoding]::Default), [System.Text.UTF8Encoding]::new($false))"
powershell -Command "[System.IO.File]::WriteAllText('dados_formaspagamento_utf8.json', [System.IO.File]::ReadAllText('dados_formaspagamento.json', [System.Text.Encoding]::Default), [System.Text.UTF8Encoding]::new($false))"

echo.
echo Arquivos UTF-8 (sem BOM) gerados:
echo   - dados_parametros_utf8.json
echo   - dados_planocontas_utf8.json
echo   - dados_caixas_utf8.json
echo   - dados_formaspagamento_utf8.json
echo.
echo Faca upload dos arquivos *_utf8.json para ~/e-metalurgicaservico/
echo.
pause
