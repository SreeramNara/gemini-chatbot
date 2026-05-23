FROM python:3.11-slim

WORKDIR /app

# system stability (recommended)
RUN pip install --upgrade pip

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . .

# Cloud Run port
ENV PORT=8080

EXPOSE 8080

# production uvicorn config
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]