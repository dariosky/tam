@echo off
call ..\environment\scripts\activate.bat
set tamport=8000
set DJANGO_SETTINGS_MODULE=settings
IF EXIST win_startLocal.bat call win_settings.bat
start python manage.py runserver 127.0.0.1:%tamport% --nothreading
start python manage.py celeryd
set tamport=
