@echo off
cd /d %~dp0
call ..\environment\Scripts\activate.bat
set DJANGO_SETTINGS_MODULE=settings

rem Migro i DB all'ultima versione
python manage.py migrate

python manage.py collectstatic --noinput
python manage.py generatemedia

python manage.py sqlitereindex tam
python manage.py sqlitereindex fatturazione

python manage.py cleanup

echo Fine.