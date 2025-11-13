# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container
COPY ./requirements.txt /code/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copy the application code into the container
COPY ./app /code/app
# Copy the data needed at runtime
COPY ./data /code/data

# Run the NLTK downloader to get necessary corpora
# This runs at build time, so it's available for the app
RUN python -m nltk.downloader stopwords wordnet punkt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable for production
ENV ENVIRONMENT=production

# Run uvicorn server
# The --host 0.0.0.0 makes the server accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]