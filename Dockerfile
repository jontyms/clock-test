FROM python:3

RUN mkdir /code

WORKDIR /code

RUN ["python", "-m", "pip", "install", "--upgrade", "pip", "wheel"]

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=80"]