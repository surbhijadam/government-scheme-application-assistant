FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r requirements.txt
COPY . .

EXPOSE 8501

# --server.address=0.0.0.0 is required inside a container - Streamlit's
# default (localhost only) would make it unreachable from outside the container.
CMD ["streamlit", "run", "Home.py", "--server.address=0.0.0.0", "--server.port=8501"]