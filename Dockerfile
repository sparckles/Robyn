# syntax=docker/dockerfile:1
FROM python:buster
# RUN apt install gcc musl-dev linux-headers software-properties-common && add-apt-repository ppa:deadsnakes/ppa
# RUN apt update && apt install python3.8
# RUN apt update && apt install -y software-properties-common
# RUN add-apt-repository ppa:deadsnakes/ppa
# RUN apt -y install python3-9
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

# Add .cargo/bin to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Check cargo is visible
RUN cargo --help
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip3 install -r  requirements.txt
EXPOSE 5000
COPY test_python .
CMD [ "python3", "base_routes.py" ]

