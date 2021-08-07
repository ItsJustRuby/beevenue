FROM beevenue-tests-app:beevenue-tests-app
WORKDIR /beevenue

USER root
RUN chown beevenue:beevenue /beevenue
USER beevenue:beevenue

RUN pip install -r requirements.cionly.txt

COPY --chown=beevenue:beevenue . /beevenue
ENTRYPOINT [ "bash", "script/coverage.sh" ]
