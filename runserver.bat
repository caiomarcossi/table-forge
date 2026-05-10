@echo off
call venv\scripts\activate.bat
cd rpg
python manage.py runserver
