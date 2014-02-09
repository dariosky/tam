@echo off
cd /d %~dp0
cmd /e:on /k "call C:\Stuff\development\Python\.environments\tam\Scripts\activate.bat && set DJANGO_SETTINGS_MODULE=settings"