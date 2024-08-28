# Use a slim version of Python
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set PYTHONPATH to include the working directory
ENV PYTHONPATH=/usr/src/app

# Run the application
CMD ["python", "app/main.py"]
