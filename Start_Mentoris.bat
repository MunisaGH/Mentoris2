@echo off
echo Mentoris loyihasi ishga tushirilmoqda...
cd /d %~dp0
python manage.py runserver 0.0.0.0:8000
pause
