FROM beevenue-tests-app:beevenue-tests-app

WORKDIR /beevenue
COPY . /beevenue/

RUN pip install -r requirements.cionly.txt

ENTRYPOINT [ "bash", "script/coverage.sh" ]
