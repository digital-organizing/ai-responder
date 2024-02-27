# pull official base image
FROM python:3.10-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
  apt-get install -y \
  netcat-traditional gettext build-essential gcc

# install dependencies

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache --upgrade pip
COPY ./pyproject.toml .
RUN --mount=type=cache,target=/root/.cache pip install .

RUN useradd -ms /bin/bash app
# create the appropriate directories

ENV HOME=/home/app
ENV APP_HOME=/home/app/web

RUN mkdir -p $APP_HOME/.cache ${APP_HOME}/nltk_data $APP_HOME/store /static

WORKDIR $APP_HOME

# copy project
COPY --chown=app:app . $APP_HOME

RUN chown -R app:app /static ${APP_HOME}

# change to the app user
USER app

RUN SKIP_MILVUS=true python manage.py compilemessages && SKIP_MILVUS=true python manage.py collectstatic --noinput

ENTRYPOINT ["/home/app/web/entrypoint.sh"]

CMD uvicorn --host 0.0.0.0 --port 8000 core.asgi:application
