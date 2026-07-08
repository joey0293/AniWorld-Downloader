FROM python:3.13-alpine

WORKDIR /app

# Need ffmpeg at runtime (muxing, etc.)
RUN apk add --no-cache ffmpeg

# Don’t run as root. Also make sure the usual dirs exist.
RUN adduser -D -h /home/aniworld aniworld \
    && mkdir -p /app/Downloads /home/aniworld/.aniworld \
    && chown -R aniworld:aniworld /app /home/aniworld

# Just nicer defaults in containers (no .pyc spam, logs show up immediately)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy the packaging bits first so Docker can cache the install layer
COPY pyproject.toml /app/
COPY README.md LICENSE MANIFEST.in /app/

RUN pip install --no-cache-dir --upgrade pip

# Actual source code
COPY src/ /app/src/

# Install the package
RUN pip install --no-cache-dir .

USER aniworld
CMD ["python", "-m", "aniworld"]