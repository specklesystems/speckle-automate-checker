# Use the official Python 3.11 slim image as the base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /home/speckle

# Copy the application files to the working directory
COPY . /home/speckle

# Upgrade pip and install dependencies using requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Set the entrypoint for running the Speckle function
CMD ["python", "-u", "main.py", "run"]
