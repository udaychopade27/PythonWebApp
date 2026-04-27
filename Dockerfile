FROM python:3.10

WORKDIR /PythonWebApp

COPY . /PythonWebApp

# Install system dependencies
RUN apt-get update && \
    apt-get install -y curl jq && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=app.py

CMD ["python3", "app.py"]