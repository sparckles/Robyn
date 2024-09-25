FROM python:3.11-bookworm AS builder

WORKDIR /workspace

COPY . .
RUN pip install --no-cache-dir --upgrade -r requirements.txt --target=/workspace/deps

FROM gcr.io/distroless/python3-debian11

WORKDIR /workspace
COPY --from=builder /workspace /workspace
ENV PYTHONPATH=/workspace/deps

CMD ["server.py", "--log-level=DEBUG"]
