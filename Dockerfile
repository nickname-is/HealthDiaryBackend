FROM python:3.12.3-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /healthdiarybackend

RUN pip install --upgrade pip wheel

COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY . .

RUN chmod +x app/prestart.sh

ENTRYPOINT ["app/prestart.sh"]
CMD ["python", "app/main.py"]