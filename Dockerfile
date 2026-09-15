FROM python:3.10-slim-bookworm

RUN apt update && apt upgrade -y
RUN apt install git ffmpeg -y
COPY requirements.txt /requirements.txt

RUN cd /
RUN pip3 install -U pip && pip3 install -U -r requirements.txt
RUN mkdir /TheInsomniacsClub
WORKDIR /TheInsomniacsClub
COPY . /TheInsomniacsClub
CMD ["python", "bot.py"]
