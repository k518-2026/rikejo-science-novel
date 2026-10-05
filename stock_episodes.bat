@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ============================================================================
echo  『放課後サイエンス・キャンパス』週5話＆挿絵 自動生成・GitHub Pages蓄積 (Qwen3.5 x Gemma4 x FLUX.2)
echo ============================================================================
python -m src.main --auto-replenish --min-stock 5 --push
pause
