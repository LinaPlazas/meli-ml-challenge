FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_COLOR=1 \
    PYTHONIOENCODING=UTF-8 \
    OPENBLAS_NUM_THREADS=1

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --progress-bar off -r requirements.txt

COPY . .
COPY app/ app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
