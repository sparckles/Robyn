FROM python:3.11-bookworm

WORKDIR /workspace

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python3", "app.py", "--log-level=DEBUG"]
