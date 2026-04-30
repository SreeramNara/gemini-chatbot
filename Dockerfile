FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir gradio google-genai

EXPOSE 8080

CMD ["python", "Chatbot.py"]