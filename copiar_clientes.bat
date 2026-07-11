@echo off
REM ============================================
REM Exportar e copiar clientes entre empresas
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ==============================================
echo    EXPORTAR/COPIAR CLIENTES ENTRE EMPRESAS
echo ==============================================
echo.

echo Escolha uma opcao:
echo.
echo 1 - Exportar clientes da EMPRESA 1 para arquivo JSON
echo 2 - Copiar clientes de EMPRESA 1 para EMPRESA 2 (direto no banco)
echo 3 - Fazer ambos - EMPRESA 1 para EMPRESA 2 (exportar e copiar)
echo.
echo 4 - Exportar clientes da EMPRESA 2 para arquivo JSON
echo 5 - Copiar clientes de EMPRESA 2 para EMPRESA 1 (direto no banco)
echo 6 - Fazer ambos - EMPRESA 2 para EMPRESA 1 (exportar e copiar)
echo.

set /p opcao="Digite a opcao (1, 2 ou 3): "

if "%opcao%"=="1" (
    echo.
    echo Exportando clientes da empresa 1...
    python exportar_clientes_empresa1.py
) else if "%opcao%"=="2" (
    echo.
    echo Copiando clientes da empresa 1 para empresa 2 no banco...
    python copiar_clientes_empresa.py
) else if "%opcao%"=="3" (
    echo.
    echo Exportando clientes da empresa 1...
    python exportar_clientes_empresa1.py
    echo.
    echo Aguarde...
    timeout /t 2 /nobreak
    echo.
    echo Copiando clientes da empresa 1 para empresa 2 no banco...
    python copiar_clientes_empresa.py
) else if "%opcao%"=="4" (
    echo.
    echo Exportando clientes da empresa 2...
    python exportar_clientes_empresa2.py
) else if "%opcao%"=="5" (
    echo.
    echo Copiando clientes da empresa 2 para empresa 1 no banco...
    python copiar_clientes_empresa2_para_1.py
) else if "%opcao%"=="6" (
    echo.
    echo Exportando clientes da empresa 2...
    python exportar_clientes_empresa2.py
    echo.
    echo Aguarde...
    timeout /t 2 /nobreak
    echo.
    echo Copiando clientes da empresa 2 para empresa 1 no banco...
    python copiar_clientes_empresa2_para_1.py
) else (
    echo Opcao invalida!
)

echo.
pause
