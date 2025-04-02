# GitHub Actions Workflows

This document explains the GitHub Actions workflows configured for MonitorPy.

## Docker Build and Publish Workflow

File: `.github/workflows/docker-publish.yml`

### Purpose

This workflow automatically builds and publishes Docker images for MonitorPy whenever:
- Code is pushed to the `main` branch
- A version tag (e.g., `v1.0.0`) is pushed
- A pull request is created/updated targeting the `main` branch

### Publishing Destinations

Images are published to:
1. **GitHub Container Registry**: `ghcr.io/dabonzo/monitorpy`
2. **Docker Hub**: `dabonzo/monitorpy`

### Image Tags

The workflow creates several types of tags:
- `latest`: Most recent build from main branch
- Semantic version tags (when a version tag is pushed):
  - Full version: `v1.0.0`
  - Minor version: `v1.0` 
  - Major version: `v1`
- Git SHA: `sha-abc123` (short commit hash)
- Branch name: `main`, `feature-xyz`, etc.

### Configuration

The workflow uses the following GitHub Actions:
- `docker/setup-buildx-action`: Sets up Docker BuildX for efficient builds
- `docker/login-action`: Authenticates with registries
- `docker/metadata-action`: Extracts metadata and generates tags
- `docker/build-push-action`: Builds and pushes images

### Required Secrets

For Docker Hub publishing, you need to set these secrets in your GitHub repository:
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: A Docker Hub access token (not your password)

GitHub Container Registry publishing uses the built-in `GITHUB_TOKEN` secret.

### Triggers

To trigger a new image build:

```bash
# For a standard build from the main branch:
git push origin main

# For a versioned release:
git tag v1.0.0
git push origin v1.0.0
```

## Creating A New Workflow

To add a new GitHub Actions workflow:

1. Create a new `.yml` file in the `.github/workflows/` directory
2. Configure the workflow with the appropriate triggers and jobs
3. Commit and push the file to the repository

See [GitHub Actions documentation](https://docs.github.com/en/actions) for more information on creating workflows.