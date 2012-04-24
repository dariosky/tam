call ..\environment\scripts\activate.bat
start python manage.py runserver 127.0.0.1:81111 --nothreading
ping localhost -n 8
start http://localhost:81111