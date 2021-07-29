from beevenue.beevenue import get_application

app = get_application()

if __name__ == "__main__":
    app.run(app.hostname, app.port, threaded=True)
