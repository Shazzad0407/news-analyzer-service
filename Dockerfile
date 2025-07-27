# FROM nvidia/cuda:11.1.1-cudnn8-devel-ubuntu20.04
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

LABEL maintainer="shazzad0407@gmail.com"


# Upgrade installed packages
RUN apt update && apt upgrade -y && apt clean

ENV TZ=Europe/Minsk
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


RUN apt update && \
    apt-get install -y tzdata && \
    apt install --no-install-recommends -y build-essential software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt install --no-install-recommends -y python3.7 python3.7-dev python3.7-distutils && \
    apt clean && rm -rf /var/lib/apt/lists/*



RUN apt-get -y update && \
    apt-get -y install && \
    apt-get -y install build-essential

RUN apt-get -y install python3-pip
RUN python3 -m pip install --upgrade pip

WORKDIR /app
COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


COPY . /app

EXPOSE 5063
# CMD ["python3", "main.py"]