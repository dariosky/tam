call ..\environment\scripts\activate.bat
start python manage.py runserver 127.0.0.1:8111 --nothreading
sleep 5
start http://localhost:8111