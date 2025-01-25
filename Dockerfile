FROM nvidia/cuda:11.6.2-devel-ubuntu20.04
LABEL maintainer="shazzad0407@gmail.com"
ENV PYTHONUNBUFFERED=1

RUN apt-get -y update && \
    apt-get -y install &&\
    apt-get -y install build-essential && \
    apt-get -y install ffmpeg libsm6 libxext6

RUN apt-get -y install python3-pip
RUN python3 -m pip install --upgrade pip

COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install  --no-cache-dir -r requirements.txt
RUN pip3 install gunicorn

COPY . .

CMD ["python3", "main.py"]