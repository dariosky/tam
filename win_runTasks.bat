@echo off
cd /d %~dp0
call C:\Stuff\development\Python\.environments\tam\scripts\activate.bat
set TAM_SETTINGS=settings_arte
set DJANGO_SETTINGS_MODULE=settings
title TASKD
start python manage.py taskd run
