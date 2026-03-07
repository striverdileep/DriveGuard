FROM python:3.10

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    cmake \
    libgl1 \
    libglib2.0-0

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

CMD ["python", "main.py"]