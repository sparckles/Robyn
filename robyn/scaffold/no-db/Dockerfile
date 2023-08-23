FROM ubuntu:22.04

WORKDIR /workspace

RUN apt-get update -y && apt-get install -y python3.10 python3-pip
RUN pip install --no-cache-dir --upgrade robyn
RUN pip install uvloop

COPY . .

EXPOSE 8080

CMD ["python3.10", "app.py", "--log-level=DEBUG"]