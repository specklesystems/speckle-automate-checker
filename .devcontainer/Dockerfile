# Use the official Python 3.13 slim image as the base
FROM python:3.13-slim

# Change to UK mirror for better reliability (robust for missing files)
RUN find /etc/apt/ -name '*.list' -exec sed -i 's|http://deb.debian.org|http://ftp.uk.debian.org|g' {} + || true

# Force apt to use IPv4 to avoid CDN/network issues
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4

# Install system dependencies
RUN apt-get update && apt-get install -y \
  git \
  && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /home/speckle

# Create a non-root user
RUN useradd -ms /bin/bash vscode
USER vscode

# Set environment variables
ENV PYTHONPATH=/home/speckle
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt requirements-dev.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt && \
  pip install --no-cache-dir -r requirements-dev.txt && \
  echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc 