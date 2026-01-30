# Docker Buildx Installation Guide for Arch Linux

## Issue
You're seeing this warning when running `./docker-start-with-sudo.sh`:
```
WARN[0000] Docker Compose requires buildx plugin to be installed
```

## Quick Fix (Recommended)

### Install docker-buildx package:
```bash
sudo pacman -S docker-buildx
```

After installation, verify:
```bash
docker buildx version
```

Then retry your deployment:
```bash
./docker-start-with-sudo.sh
```

---

## Alternative: Manual Installation

If the package isn't available, install manually:

### 1. Download the buildx plugin:
```bash
# Get latest version
BUILDX_VERSION=$(curl -s https://api.github.com/repos/docker/buildx/releases/latest | grep tag_name | cut -d '"' -f 4)

# Download for Linux AMD64
mkdir -p ~/.docker/cli-plugins
curl -L "https://github.com/docker/buildx/releases/download/${BUILDX_VERSION}/buildx-${BUILDX_VERSION}.linux-amd64" -o ~/.docker/cli-plugins/docker-buildx

# Make executable
chmod +x ~/.docker/cli-plugins/docker-buildx
```

### 2. Verify installation:
```bash
docker buildx version
```

---

## Alternative: Use Legacy Build (If buildx continues to fail)

Modify the docker-start script to use legacy build:

### Edit docker-start-with-sudo.sh:

Change line 103 from:
```bash
$COMPOSE_CMD build --no-cache
```

To:
```bash
DOCKER_BUILDKIT=0 $COMPOSE_CMD build --no-cache
```

---

## Workaround: Try Without Installing

The warning might not actually block the build. Try continuing:

```bash
# Let the script continue past the warning
# It may still build successfully using legacy builder
./docker-start-with-sudo.sh
```

---

## Recommended Action

**Execute this command now:**
```bash
sudo pacman -S docker-buildx && ./docker-start-with-sudo.sh
```

This will install buildx and immediately retry the deployment.

---

## Verification Commands

After fixing, verify everything works:
```bash
# Check Docker
docker --version

# Check Buildx
docker buildx version

# Check Compose
docker compose version

# Test deployment
./docker-start-with-sudo.sh
```

---

## Need Help?

If issues persist, check:
1. Docker service is running: `sudo systemctl status docker`
2. You have enough disk space: `df -h`
3. Your user is in docker group: `groups $USER`

To add yourself to docker group (avoid sudo):
```bash
sudo usermod -aG docker $USER
# Then logout and login again
```
