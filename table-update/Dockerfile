# 1. Base the image on slim Python
FROM python:3.10-slim as builder

# 2. Install the sqlite3 C runtime so `import sqlite3` works
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc \
      libpq-dev \
      libsqlite3-0 \
 && rm -rf /var/lib/apt/lists/*

# 3. Set working dir and copy dependency list
WORKDIR /workspace

# 4. Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 5. Copy your source code
COPY . .

FROM scratch
WORKDIR /workspace

COPY --from=builder --chown=33:33 /workspace /workspace

CMD ["functions-framework", "--target=blob_trigger", "--signature-type=cloudevent"]