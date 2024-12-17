FROM python:3.11-bookworm

WORKDIR /workspace

COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt


RUN python3 -m prisma generate
RUN python3 -m prisma migrate dev --name init

EXPOSE 8080

CMD ["python3", "app.py", "--log-level=DEBUG"]
