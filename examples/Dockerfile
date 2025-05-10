# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy the rest of the application
COPY domainsale/ ./domainsale/

# Set the entrypoint to the domainsale CLI
ENTRYPOINT ["python", "-m", "domainsale.cli"]

# Default command (can be overridden)
CMD ["--help"]
