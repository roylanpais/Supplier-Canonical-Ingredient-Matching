FROM python:3.11-slim
WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

COPY ./app /code/app
COPY ./data /code/data

RUN python -m nltk.downloader stopwords wordnet punkt

EXPOSE 8000
ENV ENVIRONMENT=production

# The --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]