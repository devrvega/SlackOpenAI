FROM python:3.9.18

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["gunicorn", "main:app", "-w", "4", "--bind", "0.0.0.0:8000"]
