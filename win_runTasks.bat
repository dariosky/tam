@echo off
cd /d %~dp0
call ..\environment\scripts\activate.bat
set DJANGO_SETTINGS_MODULE=settings
title TASKD
start python manage.py taskd run