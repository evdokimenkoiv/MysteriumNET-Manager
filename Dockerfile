FROM python:3.11-slim

WORKDIR /app

# Install tools needed for optional remote deploys
RUN apt-get update -y &&     apt-get install -y --no-install-recommends openssh-client sshpass &&     rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
