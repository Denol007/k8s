FROM python:3.10-slim
COPY app.py /app.py
RUN pip install flask
CMD ["python", "/app.py"]
