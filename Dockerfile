# official Python runtime
FROM python:3.10-slim

# define working directory in the container
WORKDIR /usr/src/app

# copy & install requirements into the container
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the application into the container
COPY . .

# application entry point
CMD ["python", "app/main.py"]
