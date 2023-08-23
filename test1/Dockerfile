
FROM ubuntu:22.04

WORKDIR /workspace

RUN apt-get update -y && apt-get install -y python 3.10 python3-pip
RUN pip install --no-cache-dir --upgrade robyn

COPY ./src/workspace/

EXPOSE 8080

CMD ["python3.10", "/workspace/foo/app.py", "--log-level=DEBUG"]
                