FROM python:3.10-slim

# System dependencies for ffmpeg, spleeter, yt-dlp, and native builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libsm6 \
    libxext6 \
    libgl1 \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in stages to isolate failures
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
# Stage 1: Heavy ML deps (spleeter pulls tensorflow + numpy)
RUN pip install --no-cache-dir numpy==1.24.4
RUN pip install --no-cache-dir tensorflow==2.12.1
RUN pip install --no-cache-dir spleeter==2.4.0

# Pin typer/click to versions compatible with BOTH Spleeter and Celery:
#   - Spleeter needs typer.models.List/Optional (removed in typer>=0.5)
#   - Spleeter needs click.termui.get_terminal_size (removed in click>=8.2)
#   - Celery needs click>=8.1.2,<9.0
RUN pip install --no-cache-dir typer==0.4.1 click==8.1.7

# GATE: Verify spleeter actually imports before continuing — fail fast
RUN python -c "from spleeter.separator import Separator; print('Spleeter import OK')"

# Stage 2: App deps (skip already-installed heavy deps)
RUN pip install --no-cache-dir -r requirements.txt

# GATE: Verify spleeter CLI works end-to-end after all deps installed
RUN python -c "from spleeter.separator import Separator; print('Spleeter import OK')"
RUN spleeter --help > /dev/null 2>&1 && echo "Spleeter CLI OK"

# Pre-download Spleeter 5stems model to avoid runtime download
RUN python -c "from spleeter.separator import Separator; Separator('spleeter:5stems')" || true

COPY . .

# Create temp directory
RUN mkdir -p /tmp/audio_viz

EXPOSE 8000

# Default: run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
