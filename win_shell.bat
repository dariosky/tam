@echo off
cd /d %~dp0
cmd /e:on /k "call ..\environment\Scripts\activate.bat && set DJANGO_SETTINGS_MODULE=settings"