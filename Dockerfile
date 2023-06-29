FROM python:3.10
LABEL version="1.0"

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-dev

COPY . /app

ENTRYPOINT ["poetry", "run", "python", "luxmedhunter/luxmed_runner.py"]
