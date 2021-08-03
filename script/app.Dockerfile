FROM python:3.9
WORKDIR /beevenue

RUN apt-get update && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 3341 beevenue && \
    useradd --no-log-init --system --create-home --uid 2175 -g beevenue beevenue && \
    chown beevenue:beevenue /home/beevenue && chown beevenue:beevenue /beevenue

USER beevenue:beevenue

RUN pip install --upgrade pip && pip install gunicorn

COPY ./requirements.* /beevenue/
RUN pip install -r requirements.txt -r requirements.linuxonly.txt

# This is where pip installed the binaries for flask and gunicorn
ENV PATH="/home/beevenue/.local/bin:${PATH}"

COPY --chown=beevenue:beevenue . /beevenue/
CMD [ "bash", "script/release_server.sh" ]
