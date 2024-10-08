FROM python:3.10

WORKDIR /PythonWebApp

COPY . /PythonWebApp

RUN pip install -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=app.py

CMD ["python3", "app.py"]


