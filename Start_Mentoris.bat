@echo off
echo Mentoris loyihasi ishga tushirilmoqda...
cd /d %~dp0
python manage.py runserver
pause
