FROM python:3.11-slim-bookworm
WORKDIR /code

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --create-home appuser

RUN python -m nltk.downloader stopwords wordnet punkt_tab

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade pip -r /code/requirements.txt

COPY ./data /code/data
COPY ./app /code/app
USER appuser
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
