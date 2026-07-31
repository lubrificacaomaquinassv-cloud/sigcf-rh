@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  SIGRH - Importar Termos de Quitacao (PDF)
echo  ==========================================
echo  Pasta padrao: C:\Users\hmauricio\Desktop\RH
echo.
python gerar_sql_rescisoes_pdf.py "C:\Users\hmauricio\Desktop\RH"
echo.
if exist "sql\010_update_rescisoes_pdf.sql" (
    echo  SQL gerado: sql\010_update_rescisoes_pdf.sql
    echo  Relatorio:  sql\010_rescisoes_relatorio.txt
    echo.
    echo  Proximo passo: abra o arquivo SQL e cole no Supabase SQL Editor.
) else (
    echo  Nenhum SQL gerado. Verifique os PDFs na pasta RH.
)
echo.
pause
