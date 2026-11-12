FROM python:3.11-slim
RUN pip install --no-cache-dir pytest pytest-cov
RUN useradd -m runner
USER runner
