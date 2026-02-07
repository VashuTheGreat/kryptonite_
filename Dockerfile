# # Use the official Python image
# FROM python:3.13-slim

# # Install uv inside the image
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# WORKDIR /app

# # Copy all project files
# COPY . /app

# # Synchronize dependencies using uv
# RUN uv pip install --system -r requirements.txt

# EXPOSE 8002

# # Use python to run the main script (dependencies are already installed in system)
# CMD ["uv","run","main.py"]


FROM python:3.13-slim

# install required system libs for opencv
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . /app

RUN uv pip install --system -r requirements.txt

EXPOSE 8002
CMD ["sh","-c","uvicorn src.app:app --host 0.0.0.0 --port 8002"]
