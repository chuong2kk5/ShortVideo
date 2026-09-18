@echo off
chcp 65001 >nul
title AI SHORTS FACTORY - RUN TESTS
cd /d "%~dp0"

echo ==============================================================================
echo        AI SHORTS FACTORY & YOUTUBE MANAGER - TEST SUITE
echo ==============================================================================
echo.

python backend/tests/test_phase1.py

echo.
echo ==============================================================================
pause

