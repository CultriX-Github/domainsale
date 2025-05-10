# Docker Guide for DomainSale

This guide explains how to use Docker with the DomainSale package.

## Using the Dockerfile

The `Dockerfile` in this directory can be used to build a Docker image for the DomainSale package.

### Building the Docker Image

From the root directory of the project, run:

```bash
docker build -t domainsale -f examples/Dockerfile .
```

### Running the Docker Container

Once the image is built, you can run it with:

```bash
docker run domainsale example.com
```

You can pass any arguments to the CLI:

```bash
docker run domainsale example.com --rdap --format json
```

## Using Docker Compose

The `docker-compose.yml` file in this directory provides a more convenient way to run the Docker container.

### Running with Docker Compose

From the `examples` directory, run:

```bash
docker-compose up
```

This will build the image and run the container with the default command (`example.com --format json`).

### Overriding the Command

You can override the command when running with Docker Compose:

```bash
docker-compose run domainsale yourdomain.com --rdap --format html
```

### Running the Web Server

The Docker Compose file also includes a service for running the web server:

```bash
docker-compose up webserver
```

This will start the web server on port 8000, which you can access at http://localhost:8000.

## Building a Custom Docker Image

If you want to build a custom Docker image for your specific use case, you can create a new Dockerfile based on the example:

```dockerfile
FROM python:3.9-slim

# Install Poetry
RUN pip install poetry

# Install the DomainSale package from GitHub
RUN pip install git+https://github.com/yourusername/domainsale.git

# Set the entrypoint to the domainsale CLI
ENTRYPOINT ["domainsale"]

# Default command (can be overridden)
CMD ["--help"]
```

## Deploying to Docker Hub

If you want to publish your Docker image to Docker Hub, you can do so with:

```bash
# Build the image
docker build -t yourusername/domainsale -f examples/Dockerfile .

# Log in to Docker Hub
docker login

# Push the image
docker push yourusername/domainsale
```

## Using the Docker Image from Docker Hub

Once the image is published to Docker Hub, others can use it with:

```bash
docker pull yourusername/domainsale
docker run yourusername/domainsale example.com
```

## GitHub Actions for Docker (Optional)

You can add GitHub Actions to automatically build and publish your Docker image. Create a file at `.github/workflows/docker-image.yml`:

```yaml
name: Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build the Docker image
      run: docker build -t domainsale -f examples/Dockerfile .
    - name: Test the Docker image
      run: docker run domainsale example.com --format json

  publish:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags')
    steps:
    - uses: actions/checkout@v3
    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_HUB_USERNAME }}
        password: ${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}
    - name: Extract metadata for Docker
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: yourusername/domainsale
    - name: Build and push Docker image
      uses: docker/build-push-action@v3
      with:
        context: .
        file: examples/Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
```

This will build and test the Docker image on every push to the main branch, and publish it to Docker Hub when a new tag is pushed.
