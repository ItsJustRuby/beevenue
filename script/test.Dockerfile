FROM beevenue-tests-app:beevenue-tests-app

WORKDIR /beevenue

RUN pip install -r requirements.cionly.txt

ENTRYPOINT [ "bash", "script/coverage.sh" ]
