FROM beevenue-app

WORKDIR /beevenue
COPY . /beevenue/

RUN pip install -r requirements.cionly.txt

ENTRYPOINT [ "sh", "script/coverage.sh" ]
