FROM python:3

EXPOSE 8000

RUN mkdir /app
WORKDIR /app

COPY . /app

RUN pip install -r requirements/requirements.txt

ENV TAM_SETTINGS settings_taxi2beta
CMD python manage.py daphne start
CMD python manage.py workers start
d
