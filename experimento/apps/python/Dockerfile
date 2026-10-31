FROM python:3.11-slim
ARG WORKLOAD=minimal
COPY requirements-deps.txt /tmp/
# só instala as bibliotecas se o workload for "deps"
RUN if [ "$WORKLOAD" = "deps" ]; then pip install --no-cache-dir -r /tmp/requirements-deps.txt; fi
COPY app_${WORKLOAD}.py /app.py
CMD ["python", "/app.py"]