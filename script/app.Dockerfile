FROM python:3.9
WORKDIR /beevenue

RUN apt-get update && apt-get install -y ffmpeg \
    && pip install --upgrade pip && pip install gunicorn \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.* /beevenue/
RUN pip install -r requirements.txt -r requirements.linuxonly.txt

COPY . /beevenue/
CMD [ "sh", "script/release_server.sh" ]
