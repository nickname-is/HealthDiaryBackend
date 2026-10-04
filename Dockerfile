FROM python:3.14.2-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PIP_NO_CACHE_DIR=1

WORKDIR /healthdiarybackend

ENV PYTHONPATH=/healthdiarybackend

RUN pip install --upgrade pip wheel
RUN pip install poetry==2.5.1

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-interaction --no-ansi

COPY . .

RUN chmod +x app/prestart.sh

ENTRYPOINT ["app/prestart.sh"]
CMD ["python", "app/main.py"]
