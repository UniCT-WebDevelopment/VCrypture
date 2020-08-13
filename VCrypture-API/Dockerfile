FROM python:3.8

ENV APP_DIR /usr/src/app
ENV APP_PORT 5050
ENV APP_WORKERS 2

WORKDIR $APP_DIR

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN adduser --no-create-home --gecos "" --disabled-password flask && \
    chown -R flask:flask $APP_DIR

USER flask

EXPOSE $APP_PORT

CMD gunicorn -w $APP_WORKERS -b 0.0.0.0:$APP_PORT app:app
