#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

#removed makemigrations as migration files are generated in dev and pushed to repo
#python manage.py makemigrations
python manage.py migrate