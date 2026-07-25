FROM python:3.12-slim

# Évite l'écriture de fichiers .pyc et force l'affichage direct des logs Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

# Copie et installation des dépendances
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du projet
COPY . /workspace/