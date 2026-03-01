# Dockerfile for DriveGuard
# build with: docker build -t driveguard .
# on a Raspberry Pi you may want to specify --platform linux/arm/v7 or arm64

FROM python:3.11-slim

# avoid interactive prompts and improve python stdout behavior
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

# create a virtual environment to isolate dependencies (optional but
# ensures we have an explicit pip and python executable path).
ENV VENV_PATH="/opt/venv"
RUN python -m venv ${VENV_PATH} \
    && ${VENV_PATH}/bin/python -m pip install --upgrade pip setuptools wheel

# use the venv's bin directory in PATH so that all subsequent commands
# (including pip install) operate inside the venv
ENV PATH="${VENV_PATH}/bin:$PATH"

# install system packages needed by python libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        libgl1 \
        libsm6 \
        libxrender1 \
        libxext6 \
        build-essential \
        python3-dev \
        gcc \
        g++ \
        git \
        libcap-dev \
        # atlas dev packages have been removed from newer Ubuntu repos; the
        # Python wheels we install contain their own BLAS/accelerations so we
        # can safely drop the dev headers.  keep runtime libs just in case.
        libatlas3-base \
        liblapack-dev \
        libblas-dev \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# create application directory
WORKDIR /app

# copy dependency list and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# pre-download DeepFace models so the first run inside the container
# doesn't block waiting for large weights to download. we only use
# Facenet in the application but caching a handful of models is cheap.
RUN python - <<'PYCODE'
from deepface import DeepFace
for m in ("Facenet", "ArcFace", "DeepFace"):
    try:
        DeepFace.build_model(m)
    except Exception as e:
        # network may not be available during build; container will
        # still work and models will download lazily at runtime
        print(f"warning: could not prefetch {m}: {e}")
PYCODE

# copy the rest of the source code
COPY . ./

# expose any ports here if needed (none required for PiGPIO)

# default command
CMD ["python3", "Main_File.py"]
