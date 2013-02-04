@echo off
cd /d %~dp0
call ..\environment\Scripts\activate.bat && set DJANGO_SETTINGS_MODULE=settings
python manage.py syncdb
python manage.py syncdb --database archive
python manage.py syncdb --database modellog